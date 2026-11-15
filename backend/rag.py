"""
RAG pipeline — ingest government scheme PDFs into ChromaDB,
then retrieve relevant chunks for a user query.

Run once to build the index:
    python rag.py --ingest
"""

import os, glob, argparse
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

SCHEMES_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "schemes")
CHROMA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
EMBED_MODEL  = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Lazy-loaded globals
_vectordb = None
_embeddings = None


def _get_db():
    global _vectordb, _embeddings
    if _vectordb is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        _vectordb   = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=_embeddings,
        )
    return _vectordb


def ingest():
    """Load all PDFs/TXTs from data/schemes/ and store in ChromaDB."""
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    splitter   = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)

    docs = []
    for path in glob.glob(os.path.join(SCHEMES_DIR, "**/*"), recursive=True):
        try:
            if path.endswith(".pdf"):
                loader = PyPDFLoader(path)
            elif path.endswith(".txt"):
                loader = TextLoader(path, encoding="utf-8")
            else:
                continue
            raw = loader.load()
            chunks = splitter.split_documents(raw)
            for c in chunks:
                c.metadata["source"] = os.path.basename(path)
            docs.extend(chunks)
            print(f"  ✓ {os.path.basename(path)} → {len(chunks)} chunks")
        except Exception as e:
            print(f"  ✗ {path}: {e}")

    if not docs:
        print("No documents found. Add PDFs to data/schemes/ and re-run.")
        return

    db = Chroma.from_documents(docs, embeddings, persist_directory=CHROMA_DIR)
    print(f"\n✅ Ingested {len(docs)} chunks into ChromaDB at {CHROMA_DIR}")
    return db


def query_schemes(question: str, k: int = 4) -> str:
    """Return top-k relevant chunks as a single context string."""
    db = _get_db()
    results = db.similarity_search(question, k=k)
    if not results:
        return "No relevant scheme information found."
    parts = []
    for i, doc in enumerate(results, 1):
        src = doc.metadata.get("source", "unknown")
        parts.append(f"[{i}] ({src})\n{doc.page_content.strip()}")
    return "\n\n".join(parts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingest", action="store_true", help="Build the vector DB")
    parser.add_argument("--query",  type=str, help="Test a query")
    args = parser.parse_args()

    if args.ingest:
        ingest()
    if args.query:
        print("\n--- Context ---")
        print(query_schemes(args.query))
