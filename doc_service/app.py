from fastapi import FastAPI, HTTPException, UploadFile, File
import httpx
import os
import fitz  
import json
from fastapi.middleware.cors import CORSMiddleware

STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8004")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8005")

app = FastAPI(title="Document Service")

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
    return {"message": "Document Service is running"}

@app.post("/process-pdf")
async def process_pdf(file: UploadFile = File(...)):
    # Read the PDF file
    contents = await file.read()
    
    try:
        # Open the PDF
        pdf_document = fitz.open(stream=contents, filetype="pdf")
        
        # Extract text and tables
        text = ""
        tables = []
        
        for page in pdf_document:
            text += page.get_text("text")  
            tables.extend(page.find_tables())  # Extract tables (if any)
        
        # Convert tables to list format (if extracted)
        table_data = [table for table in tables] if tables else []
        
        # Create metadata
        metadata = {"filename": file.filename, "tables": table_data}
        
        # Get embedding for the extracted text
        async with httpx.AsyncClient() as client:
            embedding_response = await client.post(
                f"{EMBEDDING_SERVICE_URL}/embed",
                json={"text": text}
            )
            
            if embedding_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to generate embedding")
            
            embedding = embedding_response.json()["embedding"]
        
        # Store the extracted data
        async with httpx.AsyncClient() as client:
            storage_response = await client.post(
                f"{STORAGE_SERVICE_URL}/store",
                json={
                    "content": text,
                    "source": "pdf",
                    "metadata": metadata,
                    "embedding": embedding
                }
            )
            
            if storage_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to store document data")
            
            return storage_response.json()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)