# Japan Travel AI Agent
A sophisticated RAG (Retrieval-Augmented Generation) and Real-time Search travel planner. 
It blends a deep local knowledge base with live Google Maps data to generate optimized, data-backed Japanese itineraries.


# files:

app.py: Streamlit UI & Session management.

orchestrator.py: Workflow controller & State management.

search_service.py: Reasoning engine; coordinates RAG and Live Search.

rag.py: Vector search and embedding operations.

online.py: External Google Places API integration.

client.py: LLM API communication layer.

chat_service.py: General AI consultation and chat.

scraw.ipynb: Web crawler for building the static knowledge base.

# structure:
```bash
project/
├── app.py                 # Streamlit UI 主程式
├── online.py              # Google Places API 工具
├── rag.py                 # RAG 檢索系統 (Vector DB)
├── llm/
│   └── client.py          # LLM API 呼叫介面
└── services/
    ├── chat_service.py    # 聊天功能邏輯
    ├── orchestrator.py    # 系統流程控制 (Pipeline)
    └── search_service.py  # 整合 RAG 與工具的搜尋邏輯
```
# Tech Stack
Frontend: StreamlitVector

DB: ChromaDB

Embedding: paraphrase-multilingual-MiniLM-L12-v2

APIs: Google Places V1, LLM (GPT/Llama)

Mapping: Folium / Streamlit-Folium

to run: streamlit run app.py

## Create a Virtual Environment:
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

## Install Dependencies:
```bash
pip install streamlit requests chromadb sentence-transformers tqdm tiktoken
```
# Execution Flow
## Step 1: Initialize Knowledge Base (RAG Preprocessing)
build the local vector database
```bash
python rag.py
```
## Step 2: Run the Application
```bash
streamlit run app.py
```
