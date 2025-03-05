from fastapi import FastAPI, HTTPException, UploadFile, File
import httpx
import os
import json
from fastapi.middleware.cors import CORSMiddleware

# Service URLs from environment variables
DOCUMENT_SERVICE_URL = os.getenv("DOCUMENT_SERVICE_URL", "http://localhost:8001")
WEB_SCRAPER_SERVICE_URL = os.getenv("WEB_SCRAPER_SERVICE_URL", "http://localhost:8002")
SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL", "http://localhost:8003")

app = FastAPI(title="API Gateway Service")

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
    return {"message": "Welcome to the API Gateway"}

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    # Forward the PDF file to the document service
    async with httpx.AsyncClient() as client:
        # Create form data with the file
        files = {"file": (file.filename, await file.read(), file.content_type)}
        response = await client.post(f"{DOCUMENT_SERVICE_URL}/process-pdf", files=files)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()

@app.get("/scrape-web-news")
async def scrape_news():
    # Forward the request to the web scraper service
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{WEB_SCRAPER_SERVICE_URL}/scrape-news")
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()

@app.get("/search/{query}")
async def search_data(query: str):
    # Forward the search query to the search service
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SEARCH_SERVICE_URL}/keyword-search/{query}")
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()

@app.get("/semantic-search")
async def semantic_search(query: str):
    # Forward the semantic search query to the search service
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SEARCH_SERVICE_URL}/semantic-search", params={"query": query})
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)