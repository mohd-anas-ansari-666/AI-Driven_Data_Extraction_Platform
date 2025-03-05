from fastapi import FastAPI, HTTPException
import httpx
import os
import json
from fastapi.middleware.cors import CORSMiddleware

# Service URLs from environment variables
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8004")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8005")

app = FastAPI(title="Search Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Search Service is running"}

@app.get("/keyword-search/{query}")
async def keyword_search(query: str):
    # Forward the keyword search request to the storage service
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{STORAGE_SERVICE_URL}/keyword-search/{query}")
        
        if response.status_code != 200:
            if response.status_code == 404:
                return {"message": "No matching data found", "data": []}
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()

@app.get("/semantic-search")
async def semantic_search(query: str):
    try:
        # Get embedding for the query
        async with httpx.AsyncClient() as client:
            embedding_response = await client.post(
                f"{EMBEDDING_SERVICE_URL}/embed",
                json={"text": query}
            )
            
            if embedding_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to generate embedding")
            
            embedding = embedding_response.json()["embedding"]
        
        # Forward the semantic search request to the storage service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{STORAGE_SERVICE_URL}/semantic-search",
                json={"query": query, "embedding": embedding}
            )
            
            if response.status_code != 200:
                if response.status_code == 404:
                    return {"message": "No matching data found", "data": []}
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            return response.json()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)