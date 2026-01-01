🗾 Japan Travel AI Agent
A sophisticated RAG (Retrieval-Augmented Generation) and Real-time Search travel planner. It blends a deep local knowledge base with live Google Maps data to generate optimized, data-backed Japanese itineraries.

app.py: Streamlit UI & Session management.

orchestrator.py: Workflow controller & State management.

search_service.py: Reasoning engine; coordinates RAG and Live Search.

rag.py: Vector search and embedding operations.

online.py: External Google Places API integration.

client.py: LLM API communication layer.

chat_service.py: General AI consultation and chat.

scraw.ipynb: Web crawler for building the static knowledge base.

to run: streamlit run app.py
