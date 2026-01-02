🗾 Japan Travel AI Agent
A sophisticated RAG (Retrieval-Augmented Generation) and Real-time Search travel planner. 
It blends a deep local knowledge base with live Google Maps data to generate optimized, data-backed Japanese itineraries.


files:

app.py: Streamlit UI & Session management.

orchestrator.py: Workflow controller & State management.

search_service.py: Reasoning engine; coordinates RAG and Live Search.

rag.py: Vector search and embedding operations.

online.py: External Google Places API integration.

client.py: LLM API communication layer.

chat_service.py: General AI consultation and chat.

scraw.ipynb: Web crawler for building the static knowledge base.


🛠️ Tech Stack

Frontend: StreamlitVector

DB: ChromaDB

Embedding: paraphrase-multilingual-MiniLM-L12-v2

APIs: Google Places V1, LLM (GPT/Llama)

Mapping: Folium / Streamlit-Folium


to run: streamlit run app.py


建立虛擬環境：
'''python
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
'''

安裝依賴庫：
'''python
pip install streamlit requests chromadb sentence-transformers tqdm tiktoken
'''
