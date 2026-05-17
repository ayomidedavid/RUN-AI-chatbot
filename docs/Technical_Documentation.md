# ACADEMIC CHATBOT TECHNICAL DOCUMENTATION

Welcome to the Technical Documentation for the local, offline **Academic Chatbot**. This system provides students with instantaneous, private, and cost-free academic advising. 

---

## 1. Project Overview & Features
This project transitions academic advising from high-cost, key-dependent cloud APIs (like Google Gemini) to a **100% local, self-contained AI architecture** running on standard consumer CPU hardware.

*   **Local LLM Engine**: Powered by the highly optimized `Qwen2.5-0.5B-Instruct` model (~1GB footprint) running offline.
*   **Dual-Database Retrieval (RAG)**: Integrates structured data (SQLite) with unstructured documents (FAISS Vector database for official handbooks).
*   **Engaging Fidget Spinner Sequence**: Custom-built asynchronous loading states ("Loading..." -> "Generating... Reasoning: X" -> Answer).
*   **Advising Transparency**: Features a collapsible `"View AI Thought Process"` panel disclosing exact intent categorizations and raw retrieved sources.
*   **Offline Data Session Persistence**: Local chat histories are fully stored in the browser's `localStorage` context.

---

## 2. Directory Layout
The folder structure is organized as follows:
```text
Aichatbot/
├── backend/
│   ├── main.py                     # Primary FastAPI router and startup eagerly pre-loads models
│   ├── llm_service.py              # Hugging Face local generator pipeline (Qwen2.5-0.5B)
│   ├── ml_model.py                 # Intent classifier training, evaluation, and FAISS indexer
│   ├── chat_handlers.py            # SQLite courses/career lookups and RAG vector scanning
│   ├── database.py                 # SQLAlchmy connector and relational tables definition
│   └── models.py                   # Data schemas (Course, FAQ, Career, ChatHistory)
├── data/
│   ├── student hand book/          # Target academic PDF handbooks
│   │   ├── Computer Science BMAS handbook.pdf
│   │   └── Cyber Security handbook.pdf
│   └── quetion.txt                 # Model training intent dataset
├── frontend/
│   ├── index.html                  # Main Web Portal interface
│   ├── degree_requirements.html    # Academic degree overview page
│   ├── courses.html                # Course Catalog visual viewer
│   ├── contact.html                # Faculty contact directory
│   ├── chat-widget.js              # Floating widget Javascript and Fidget Spinner sequence
│   ├── chat-widget.css             # Widget animations, theme colors, and layout styles
│   ├── styles.css                  # Universal design guidelines and typography
│   └── theme.js                    # Light/Dark mode localStorage manager
├── requirements.txt                # Unified dependency list
└── chatbot.log                     # Unified system logs file
```

---

## 3. Installation and Local Setup

### Step 1: Clone and Navigate
Open PowerShell or your terminal and navigate to the project root directory:
```powershell
cd "c:\Users\Danny's PC\Downloads\Aichatbot"
```

### Step 2: Establish Python Environment & Dependencies
Create a virtual environment (optional but recommended) and install dependencies. Ensure `protobuf` is locked to version `7.34.1` to avoid ML library conflicts:
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Train Intent Classifier & Build FAISS Vector Index
Run the machine learning utility script to build your local intent classifier and parse the unstructured handbooks into the FAISS index database:
```powershell
python backend/ml_model.py
```
*(This creates `faiss_index`, `chunks.pkl`, and `intent_model.pkl` in your backend path).*

### Step 4: Launch Backend Server
Run the FastAPI development server using Uvicorn. The **eager pre-loader** will automatically initialize, allocating RAM for the models before binding to the port:
```powershell
python -m uvicorn backend.main:app --port 8001 --reload
```
Once the console prints `INFO: Application startup complete.`, your local AI is ready.

### Step 5: Run Frontend
You can launch the frontend by simply double-clicking **`frontend/index.html`** or serving it via a lightweight HTTP server (like VS Code Live Server).

---

## 4. Architecture Specifications

### 4.6.1 Local Text-Generation Pipeline
The `llm_service.py` loads the model onto the CPU inside a multi-threaded PyTorch environment:
```python
# Setup local text-generation pipeline
_generator = pipeline(
    "text-generation",
    model="Qwen/Qwen2.5-0.5B-Instruct",
    device_map="auto",
    torch_dtype=torch.float32
)
```
Lower temperature controls (`temperature=0.3`) are actively applied to enforce strict logical compliance and prevent conversational fabrication (hallucinations).

### 4.6.2 The Unified Chat Handler Flow
When an HTTP query arrives at `/api/chat`, `main.py` processes it through this specific sequence:

```mermaid
sequenceDiagram
    participant User as Student Browser
    participant API as FastAPI Backend
    participant ML as Intent Classifier
    participant DB as SQLite / FAISS DB
    participant LLM as Local Qwen Model
    
    User->>API: POST /api/chat {query: "..."}
    Note right of User: Visual Fidget Spinner: "Loading..."
    API->>ML: Predict Intent
    ML-->>API: Intent: "prerequisites"
    API->>DB: Query factual database rules
    DB-->>API: Returns: "CSC 201 is prerequisite for CSC 301"
    API->>User: Sends Intent metadata immediately
    Note right of User: Spinner shifts to: "Generating... Reasoning: prerequisites"
    API->>LLM: Pass (Query + Database Context)
    LLM-->>API: Returns conversational polished rewrite
    API-->>User: Sends final Markdown response
    Note right of User: Fidget Spinner fades; Answer & Thought Panel displays
```

---

## 5. Troubleshooting & FAQs

### Q1: I see a `winerror 10048` address conflict during backend startup.
**Cause**: An existing Uvicorn server is already running in the background and holding onto port `8001`.
**Solution**: Open PowerShell as Administrator and execute this quick script to kill the frozen process:
```powershell
$id = (Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue).OwningProcess
if ($id) { Stop-Process -Id $id -Force }
```
Then, try starting the server again.

### Q2: Why is the chatbot's very first response slow?
**Cause**: Eager loading was not successfully triggered or the server is still booting up.
**Solution**: Ensure you have restarted the server. Once the server says `Application startup complete`, the model is loaded into System RAM, and all subsequent responses will be virtually instant (under 1.5 seconds).

### Q3: How do I add new course information or custom FAQs?
**Solution**: You can use the **Admin Dashboard** (`frontend/admin.html`) to directly add courses, career mappings, and FAQs, or insert them directly into the `sqlite.db` database using standard DB tools. Remember to hit the **"Rebuild Index"** and **"Retrain Model"** buttons under the "System" tab inside the Admin Dashboard after making large modifications.
