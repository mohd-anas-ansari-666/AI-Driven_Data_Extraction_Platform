from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson import ObjectId
import os
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD
from whoosh.qparser import QueryParser
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from fastapi.middleware.cors import CORSMiddleware

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["data_extraction"]
collection = db["extracted_data"]

# Initialize Whoosh index
index_dir = "whoosh_index"
if not os.path.exists(index_dir):
    os.mkdir(index_dir)

# Define Whoosh schema
schema = Schema(id=ID(stored=True), content=TEXT(stored=True), source=TEXT(stored=True), metadata=TEXT(stored=True), embedding=KEYWORD(stored=True))

# Create or open the index
if not os.path.exists(os.path.join(index_dir, "MAIN_WRITELOCK")):
    ix = create_in(index_dir, schema)
else:
    ix = open_dir(index_dir)

# Create FastAPI app
app = FastAPI(title="Storage Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class StoreRequest(BaseModel):
    content: str
    source: str
    metadata: Dict[str, Any]
    embedding: List[float]

class SemanticSearchRequest(BaseModel):
    query: str
    embedding: List[float]

def convert_objectid_to_str(obj):
    """
    Converts ObjectId to string, recursively if nested.
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(i) for i in obj]
    return obj

@app.get("/")
async def root():
    return {"message": "Storage Service is running"}

@app.post("/store")
async def store_data(item: StoreRequest):
    try:
        # Store data in MongoDB
        mongo_item = {
            "source": item.source,
            "content": item.content,
            "metadata": item.metadata
        }
        result = collection.insert_one(mongo_item)
        
        # Convert embedding to a string for storage in Whoosh
        embedding_str = ",".join(map(str, item.embedding))
        
        # Add document to Whoosh index
        writer = ix.writer()
        writer.add_document(
            id=str(result.inserted_id),
            content=item.content,
            source=item.source,
            metadata=str(item.metadata),
            embedding=embedding_str
        )
        writer.commit()
        
        return {"message": "Data stored successfully", "id": str(result.inserted_id)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")

@app.get("/keyword-search/{query}")
async def keyword_search(query: str):
    try:
        # Open Whoosh index and search
        with ix.searcher() as searcher:
            query_parser = QueryParser("content", ix.schema)
            query_obj = query_parser.parse(query)
            results = searcher.search(query_obj)
            
            # Format search results
            results_list = []
            for result in results:
                result_dict = {
                    "id": str(result['id']),
                    "content": result['content'],
                    "source": result['source'],
                    "metadata": result['metadata']
                }
                results_list.append(result_dict)
        
        if not results_list:
            raise HTTPException(status_code=404, detail="No matching data found")
        
        return {"message": "Search results", "data": results_list}
    
    except Exception as e:
        if "No matching data found" in str(e):
            raise HTTPException(status_code=404, detail="No matching data found")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/semantic-search")
async def semantic_search(request: SemanticSearchRequest):
    try:
        # Get the query embedding
        query_embedding = np.array(request.embedding)
        
        # Search for similar documents
        with ix.searcher() as searcher:
            # Fetch all document embeddings
            results = []
            for doc in searcher.all_stored_fields():
                # Convert the stored embedding back to a numpy array
                doc_embedding = np.array(list(map(float, doc['embedding'].split(","))))
                # Compute cosine similarity between query and document embedding
                similarity = cosine_similarity([query_embedding], [doc_embedding])[0][0]
                results.append((doc, similarity))
            
            # Sort results by similarity
            results = sorted(results, key=lambda x: x[1], reverse=True)
            
            # Return top 5 results
            top_results = [
                {
                    "id": result[0]["id"],
                    "content": result[0]["content"],
                    "source": result[0]["source"],
                    "metadata": result[0]["metadata"],
                    "similarity": float(result[1])
                } for result in results[:5]
            ]
        
        if not top_results:
            raise HTTPException(status_code=404, detail="No matching data found")
        
        return {"message": "Search results", "data": top_results}
    
    except Exception as e:
        if "No matching data found" in str(e):
            raise HTTPException(status_code=404, detail="No matching data found")
        raise HTTPException(status_code=500, detail=f"Semantic search error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)