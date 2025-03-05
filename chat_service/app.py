import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import os
from typing import List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

# Service URLs from environment variables
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8004")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8005")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDaLV2r9UaT7bMvEVX9lztTgGCtaSfcJtc")  

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="Chat Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    source: str
    metadata: Dict[str, Any]

@app.get("/")
async def root():
    return {"message": "Chat Service is running"}

@app.post("/ask", response_model=QueryResponse)
async def ask_query(request: QueryRequest):
    query = request.query
    try:
        # Step 1: Generate embedding for the user query
        async with httpx.AsyncClient() as client:
            embedding_response = await client.post(
                f"{EMBEDDING_SERVICE_URL}/embed",
                json={"text": query}
            )

            if embedding_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to generate query embedding")

            query_embedding = embedding_response.json()["embedding"]

        # Step 2: Perform semantic search on stored data using query embedding
        async with httpx.AsyncClient() as client:
            search_response = await client.post(
                f"{STORAGE_SERVICE_URL}/semantic-search",
                json={"query": query, "embedding": query_embedding}
            )

            if search_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Search service error")

            search_results = search_response.json()["data"]

        # Step 3: Prepare the context (combining the retrieved documents)
        context = "\n".join([result['content'] for result in search_results])  # Combine top results for context
        full_query = f"Query: {query}\nContext:\n{context}"

        # Step 4: Ask Gemini to generate an answer based on the query and the context
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(full_query)

        # Extract answer from the response
        # gemini_answer = response.get('generated_text', "Sorry, I couldn't find an answer.")

        if hasattr(response, 'text'):
            gemini_answer = response.text  # Get the generated content

        # Step 5: Return the response with the answer and metadata
        return QueryResponse(
            answer=gemini_answer,
            source="Search Results",
            metadata={"search_results": search_results}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
