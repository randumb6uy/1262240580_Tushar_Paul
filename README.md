# RAG Project (Retrieval-Augmented Generation)

A lightweight, high-performance Retrieval-Augmented Generation (RAG) system built with [LlamaIndex](https://www.llamaindex.ai/), [ChromaDB](https://www.trychroma.com/), and [OpenRouter](https://openrouter.ai/).

## Overview

- **Embeddings:** OpenRouter Embeddings API (`nvidia/nemotron-3-embed-1b:free`) via OpenAI-compatible client
- **LLM:** OpenRouter (`liquid/lfm-2.5-2.6b:free`) for fast, concise customer assistant responses
- **Chat Engine:** LlamaIndex `ContextChatEngine` with multi-turn conversation memory and system prompt handling
- **Vector Store:** ChromaDB persistent storage (`./chroma_db`)
- **Knowledge Base:** 30 Kohler bathroom products stored in high-density pipe-delimited format across 5 category files in `docs/`

## Project Structure

```
.
├── docs/                     # Product catalog in Option 1 pipe-delimited format
│   ├── faucets.txt           # 6 faucet models
│   ├── showers.txt           # 6 shower systems & fixtures
│   ├── toilets.txt           # 6 smart & conventional toilets
│   ├── tubs_and_sinks.txt    # 6 soaking tubs, vessel & undermount sinks
│   └── vanities.txt          # 6 vanities across styles and price points
├── ingest.py                 # Embeds documents and persists vectors into ChromaDB
├── query.py                  # Interactive chat interface with memory & RAG retrieval
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
   Create a `.env` file from the template:
   ```bash
   cp .env.example .env
   ```
   Add your OpenRouter API key inside `.env`:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

## Usage

### 1. Ingest Documents
Run `ingest.py` to index the 30 catalog products in `docs/` into ChromaDB:
```bash
python ingest.py
```

### 2. Chat with the Assistant
Run `query.py` to start an interactive chat session:
```bash
python query.py
```

- Handles **casual conversation & greetings** (*"Hello!", "Who are you?"*) warmly and concisely.
- Accurately retrieves **product specifications & pricing** from ChromaDB.
- Remembers **multi-turn context** (e.g., follow-up questions like *"How much does it cost?"*).
- Type `exit` to quit.

## Notes on OpenRouter Free Tier
Free tier accounts on OpenRouter have a limit of 50 requests per day (resetting daily at 00:00 UTC). Each query uses 2 requests (1 for embedding + 1 for LLM generation).
