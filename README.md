# AI-Driven Data Extraction Platform

## Overview

The **AI-Driven Data Extraction Platform** is an intelligent web application designed to facilitate document processing, web scraping, search functionality, and AI-based chat interactions. The platform allows users to upload PDF documents, scrape web content, perform keyword and semantic searches, and chat with an AI model to ask questions based on the data provided. This platform is powered by a **Microservices Architecture**, where each component operates as an independent service.

## Features

1. **Document Processing**: 
   - Upload and process PDF documents to extract text, tables, and metadata.
   - Use extracted content for search and chat functionality.

2. **Web Scraping**:
   - Automatically scrape news articles from the web.
   - Extract article titles, content, and metadata for further analysis.

3. **Semantic and Keyword Search**:
   - Search through uploaded documents and scraped content.
   - Supports both keyword-based search and semantic search (natural language processing).

4. **AI Chat Interface**:
   - Interact with an AI chatbot to ask questions related to the uploaded documents and scraped web articles.
   - The AI leverages NLP to provide contextually relevant responses based on the available data.

## Architecture

This platform is built using a **Microservices Architecture**, where each major component is encapsulated in a service:

- **API Gateway**: Acts as a central point to route all API requests to the appropriate microservices.
- **Chat Service**: A service that provides a chat interface where users can ask questions based on the extracted content.
- **Document Processing Service**: Handles PDF file uploads, processing the documents to extract content, tables, and other data.
- **Web Scraping Service**: Scrapes content from various news websites, extracting articles for further processing and search.
- **Search Service**: Facilitates both keyword-based and semantic search functionality over the extracted content.

## Technologies Used

The platform is built using several modern technologies, including:

- **Streamlit**: For building the frontend web application.
- **FastAPI**: For building the microservices.
- **Python**: The core programming language for the backend services.
- **Requests**: For making HTTP requests between services.
- **Pandas**: For managing and displaying tabular data (like previously uploaded files).
- **JSON**: For transferring data between frontend and backend in JSON format.
- **Gemini**: Used to enhance the platform's AI capabilities, particularly for language models.
- **Transformers**: A library by Hugging Face for working with state-of-the-art NLP models like GPT, BERT, etc., used for question answering and semantic search.
- **MongoDB**: A NoSQL database used to store processed document data and search indexes.
- **Cosine Similarity**: Used in the **Search Service** for comparing the similarity of text data in semantic searches.
- **BeautifulSoup (bs4)**: Used for web scraping to extract relevant content from HTML pages.
