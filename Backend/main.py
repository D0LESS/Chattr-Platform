from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chroma_db import add_document, query_documents
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
import os

load_dotenv()

# Initialize explicitly the FastAPI app
app = FastAPI()

# Allow clearly CORS from frontend localhost explicitly:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Explicit schema clearly defined for embedding requests:
class EmbedRequest(BaseModel):
    text: str
    metadata: dict = None

# Explicitly schema clearly defined for ChatQuery:
class ChatQuery(BaseModel):
    query_text: str
    n_results: int = 3

# Endpoint explicitly defined clearly for basic API status check:
@app.get("/")
async def read_root():
    return {"Chattr Backend Status": "✅ Running"}

# Endpoint explicitly defined for adding new embeddings clearly:
@app.post("/embed")
async def embed_document(req: EmbedRequest):
    doc_id = add_document(req.text, req.metadata)
    return {"status": "success", "doc_id": doc_id}

# Endpoint explicitly defined for querying vectors clearly:
@app.post("/query")
async def query_embeddings(query: ChatQuery):
    results = query_documents(query.query_text, query.n_results)
    return {"status": "success", "results": results}

# Additional endpoints explicitly for authentication will be added explicitly in next stage (auth.py)