import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Initialize sentence transformer model for embeddings (used explicitly)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Connect explicitly to local ChromaDB instance (change settings for cloud later easily)
client = chromadb.Client(Settings(persist_directory="../data/vector_store"))
collection = client.get_or_create_collection(name="chattr_vectors")

# Explicitly defined function clearly for adding documents to vector store:
def add_document(text, metadata=None):
    embedding = model.encode(text).tolist()
    doc_id = metadata.get("id") if metadata else None
    collection.add(
        embeddings=[embedding],
        documents=[text],
        metadatas=[metadata or {}],
        ids=[doc_id] if doc_id else None
    )
    return doc_id

# Explicitly defined function clearly for querying vector store:
def query_documents(query_text, n_results=3):
    query_embedding = model.encode(query_text).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    return results