import streamlit as st
import requests
import pandas as pd
import json
import os
from io import StringIO
import time

# API Gateway URL
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://localhost:8006")

st.set_page_config(
    page_title="AI-Driven Data Extraction Platform",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #808080;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .highlight {
        background-color: #808080;
        padding: 2px 5px;
        border-radius: 3px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.markdown("# Navigation")
page = st.sidebar.radio(
    "Select a page",
    ["Home", "Upload Documents", "Web Scraping", "Search", "Chat"]
)

# Initialize session state variables if they don't exist
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'scraped_articles' not in st.session_state:
    st.session_state.scraped_articles = []

# Home page
if page == "Home":
    st.markdown('<div class="main-header">AI-Driven Data Extraction Platform</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
    Welcome to the AI-Driven Data Extraction Platform. This application provides powerful tools for:
    
    - **Document Processing**: Upload and extract information from PDF documents
    - **Web Scraping**: Automatically collect news articles from the web
    - **Semantic Search**: Find relevant information using natural language queries
    - **Chat with Data**: Ask questions and get answers based on the extracted content
    
    Use the sidebar to navigate between different features.
    </div>
    """, unsafe_allow_html=True)


# Chat page
elif page == "Chat":
    st.markdown('<div class="main-header">AI Chat Interface</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
    Chat with the AI to ask questions based on the documents and web articles you've uploaded or scraped.
    The AI will use the extracted content to provide relevant answers.
    </div>
    """, unsafe_allow_html=True)

    # Chat interface
    user_query = st.text_input("Ask a question:")

    if st.button("Ask"):
        if user_query:
            with st.spinner("Getting response from AI..."):
                try:
                    # Send the user's query to the chat service
                    response = requests.post(
                        f"{CHAT_SERVICE_URL}/ask", 
                        json={"query": user_query}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"Answer: {result['answer']}")
                        # st.markdown(f"**Source:** {result['source']}")
                        # st.json(result['metadata'])
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")


# Upload Documents page
elif page == "Upload Documents":
    st.markdown('<div class="main-header">Upload Documents</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
    Upload PDF documents to extract their content and make them searchable.
    The system will process the PDFs, extract text and tables, and index the content for later search.
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        # Display file info
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / 1024:.2f} KB",
            "File type": uploaded_file.type
        }
        
        st.markdown('<div class="sub-header">File Details</div>', unsafe_allow_html=True)
        for key, value in file_details.items():
            st.write(f"**{key}:** {value}")
        
        # Process button
        if st.button("Process PDF"):
            with st.spinner("Processing PDF..."):
                try:
                    # Prepare the file for upload
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    
                    # Send to API Gateway
                    response = requests.post(f"{API_GATEWAY_URL}/upload-pdf", files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"PDF processed successfully! Document ID: {result.get('id', 'N/A')}")
                        
                        # Add to session state
                        st.session_state.uploaded_files.append({
                            "name": uploaded_file.name,
                            "id": result.get('id', 'N/A'),
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                    else:
                        st.error(f"Error processing PDF: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Display previously uploaded files
    if st.session_state.uploaded_files:
        st.markdown('<div class="sub-header">Previously Uploaded Files</div>', unsafe_allow_html=True)
        df = pd.DataFrame(st.session_state.uploaded_files)
        st.dataframe(df)

# Web Scraping page
elif page == "Web Scraping":
    st.markdown('<div class="main-header">Web Scraping</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
    Scrape news articles from websites. The system will extract article titles and links,
    and make them searchable in the platform.
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Scrape News Articles"):
        with st.spinner("Scraping news articles..."):
            try:
                # Call the web scraper service through the API Gateway
                response = requests.get(f"{API_GATEWAY_URL}/scrape-web-news")
                
                if response.status_code == 200:
                    result = response.json()
                    articles = result.get("data", [])
                    
                    st.success(f"Successfully scraped {len(articles)} news articles!")
                    
                    # Add to session state
                    st.session_state.scraped_articles = articles
                else:
                    st.error(f"Error scraping news: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Display scraped articles
    if st.session_state.scraped_articles:
        st.markdown('<div class="sub-header">Scraped Articles</div>', unsafe_allow_html=True)
        
        for i, article in enumerate(st.session_state.scraped_articles):
            st.markdown(f"""
            <div class="card">
                <h3>{article.get('content', 'No title')}</h3>
                <p><strong>Source:</strong> {article.get('source', 'web')}</p>
                <p><strong>URL:</strong> {article.get('metadata', {}).get('url', 'No URL')}</p>
                <p><strong>ID:</strong> {article.get('id', 'No ID')}</p>
            </div>
            """, unsafe_allow_html=True)

# Search page
elif page == "Search":
    st.markdown('<div class="main-header">Search Documents</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
    Search through your uploaded documents and scraped web content.
    Choose between keyword search and semantic search depending on your needs.
    </div>
    """, unsafe_allow_html=True)
    
    search_type = st.radio("Select search type:", ["Keyword Search", "Semantic Search"])
    
    query = st.text_input("Enter your search query:")
    
    if st.button("Search") and query:
        with st.spinner(f"Performing {search_type.lower()}..."):
            try:
                if search_type == "Keyword Search":
                    # Call the keyword search endpoint
                    response = requests.get(f"{API_GATEWAY_URL}/search/{query}")
                else:  # Semantic Search
                    # Call the semantic search endpoint
                    response = requests.get(f"{API_GATEWAY_URL}/semantic-search", params={"query": query})
                
                if response.status_code == 200:
                    result = response.json()
                    search_results = result.get("data", [])
                    
                    st.success(f"Found {len(search_results)} results!")
                    
                    # Store in session state
                    st.session_state.search_results = search_results
                else:
                    st.warning("No results found or an error occurred.")
                    st.session_state.search_results = []
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.search_results = []
    
    # Display search results
    if st.session_state.search_results:
        st.markdown('<div class="sub-header">Search Results</div>', unsafe_allow_html=True)
        
        for i, result in enumerate(st.session_state.search_results):
            try:
                # Parse metadata if it's a string
                metadata = result.get("metadata", "{}")
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata.replace("'", '"'))
                    except:
                        metadata = {"raw": metadata}
                
                similarity = result.get("similarity", None)
                similarity_text = f"<p><strong>Similarity:</strong> {similarity:.2f}</p>" if similarity is not None else ""
                
                st.markdown(f"""
                <div class="card">
                    <h3>Result #{i+1}</h3>
                    <p><strong>Source:</strong> {result.get('source', 'Unknown')}</p>
                    {similarity_text}
                    <p><strong>Content:</strong></p>
                    <div class="highlight">{result.get('content', 'No content')[:300]}{'...' if len(result.get('content', '')) > 300 else ''}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Expand for full content
                with st.expander("View full content"):
                    st.write(result.get('content', 'No content'))
                    
                    # Display metadata details
                    st.markdown("**Metadata:**")
                    st.json(metadata)
            except Exception as e:
                st.error(f"Error displaying result #{i+1}: {str(e)}")

# Add footer
st.markdown("""
<div style="text-align: center; margin-top: 50px; padding: 20px; font-size: 0.8rem; color: #666;">
    AI-Driven Data Extraction Platform
</div>
""", unsafe_allow_html=True)