🗾 Japan Travel AI Agent
A sophisticated RAG (Retrieval-Augmented Generation) and Real-time Search travel planner. It blends a deep local knowledge base with live Google Maps data to generate optimized, data-backed Japanese itineraries.

files:
app.py: Streamlit UI & Session management.
orchestrator.py: Workflow controller & State management.
search_service.py: Reasoning engine; coordinates RAG and Live Search.
rag.py: Vector search and embedding operations.
online.py: External Google Places API integration.
client.py: LLM API communication layer.
chat_service.py: easy chat with llm.
scraw.ipynb: used to scraw static db for reg.


to run: streamlit run app.py
