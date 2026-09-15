# RAG Project (Retrieval-Augmented Generation)

A lightweight Retrieval-Augmented Generation (RAG) system built with [LlamaIndex](https://www.llamaindex.ai/), [ChromaDB](https://www.trychroma.com/), and [OpenRouter](https://openrouter.ai/).

## Overview

- **Embeddings:** OpenRouter Embeddings API (`nvidia/nemotron-3-embed-1b:free`) via OpenAI-compatible client
- **LLM:** OpenRouter (`nvidia/nemotron-3.5-lightning:free`)
- **Vector Store:** ChromaDB persistent storage (`./chroma_db`)
- **Knowledge Base:** Product catalog files stored in `docs/`

## Project Structure

```
.
├── docs/                     # Source documents to be indexed
├── ingest.py                 # Embeds documents and stores them in ChromaDB
├── query.py                  # Interactive query interface for RAG retrieval & QA
├── test_llm.py               # Simple test script to verify OpenRouter LLM connection
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── .gitignore                # Git ignore rules (.env, chroma_db, etc.)
```

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/randumb6uy/RAG-Project.git
   cd RAG-Project
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
   Add your OpenRouter API key inside `.env`:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

## Usage

### 1. Ingest Documents
Run `ingest.py` to chunk documents in `docs/`, compute embeddings via OpenRouter, and persist them into ChromaDB:
```bash
python ingest.py
```

### 2. Query the Knowledge Base
Run `query.py` to start an interactive question-answering session:
```bash
python query.py
```

Type your question and press Enter. Type `exit` to quit.
