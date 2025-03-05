import httpx
from fastapi import FastAPI, HTTPException
import os
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware

# Service URLs from environment variables
STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8004")
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8005")

app = FastAPI(title="Web Scraper Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

timeout = httpx.Timeout(60.0)  # Set a custom timeout (10 seconds)

@app.get("/scrape-news")
async def scrape_news():
    url = "https://news.ycombinator.com/"  # Example news website
    
    try:
        # Scrape the news website with httpx
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch news")
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")
            articles = []

            # Extract article information
            for item in soup.select(".athing"):
                try:
                    title = item.select_one(".title a").text
                    link = item.select_one(".title a")["href"]

                    # Get embedding for the article title
                    embedding_response = await client.post(
                        f"{EMBEDDING_SERVICE_URL}/embed",
                        json={"text": title}
                    )

                    if embedding_response.status_code != 200:
                        continue  # Skip this article if embedding fails
                    
                    embedding = embedding_response.json()["embedding"]

                    # Store the article data
                    article_data = {
                        "content": title,
                        "source": "web",
                        "metadata": {"url": link},
                        "embedding": embedding
                    }

                    storage_response = await client.post(
                        f"{STORAGE_SERVICE_URL}/store",
                        json=article_data
                    )

                    if storage_response.status_code == 200:
                        articles.append({
                            "source": "web",
                            "content": title,
                            "metadata": {"url": link},
                            "id": storage_response.json().get("id", "")
                        })

                except Exception as e:
                    # Skip this article if there's an error
                    continue

            return {"message": "News scraped and stored", "data": articles}

    except httpx.RequestTimeout as e:
        raise HTTPException(status_code=504, detail="The request to fetch news timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Web scraping error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
