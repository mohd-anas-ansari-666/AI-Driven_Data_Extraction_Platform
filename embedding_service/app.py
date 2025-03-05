from fastapi import FastAPI, HTTPException
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(title="Embedding Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class EmbeddingRequest(BaseModel):
    text: str

class EmbeddingResponse(BaseModel):
    embedding: List[float]

# Initialize Hugging Face's pre-trained Sentence-BERT model and tokenizer
tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')

def compute_embedding(text: str):
    """Generate an embedding for the given text using Sentence-BERT."""
    # Tokenize and prepare input
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    
    # Generate embeddings
    with torch.no_grad():
        embeddings = model(**inputs).last_hidden_state.mean(dim=1)
    
    # Convert to numpy array and then to list
    return embeddings.squeeze().numpy().tolist()

@app.get("/")
async def root():
    return {"message": "Embedding Service is running"}

@app.post("/embed", response_model=EmbeddingResponse)
async def embed_text(request: EmbeddingRequest):
    try:
        # Generate embedding for the input text
        embedding = compute_embedding(request.text)
        return {"embedding": embedding}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)