"""
Semantic (vector) memory using ChromaDB with a local sentence-transformers
embedding model — fully offline, no API calls for embeddings.
"""
import chromadb
from chromadb.utils import embedding_functions
from config import CHROMA_PATH
import time

_client = chromadb.PersistentClient(path=CHROMA_PATH)

_embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"  # small, fast, runs fine on CPU
)

_collection = _client.get_or_create_collection(
    name="ultron_memory",
    embedding_function=_embedder,
)


def remember(text: str, metadata: dict = None):
    """Store a piece of text (a fact, a summary, a completed task) for later recall."""
    doc_id = f"mem_{int(time.time() * 1000)}"
    _collection.add(
        documents=[text],
        metadatas=[metadata if metadata else {"source": "ultron"}],
        ids=[doc_id],
    )
    return doc_id


def recall(query: str, n_results: int = 5):
    """Return the most semantically relevant memories to the query."""
    if _collection.count() == 0:
        return []
    results = _collection.query(query_texts=[query], n_results=min(n_results, _collection.count()))
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    return list(zip(docs, metas))
