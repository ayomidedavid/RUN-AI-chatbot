# Academic Query AI Chatbot

A sophisticated, fully local Academic Advising Chatbot designed to assist university students with course information, registration, GPA calculation, graduation tracking, career mapping, and more. The chatbot combines traditional conversational logic with advanced Natural Language Processing (NLP) using local LLMs and Retrieval-Augmented Generation (RAG).

## Features
- **Intelligent Intent Recognition**: Uses a trained Intent Classifier to route user queries accurately.
- **RAG-based Information Retrieval**: Employs FAISS and `SentenceTransformers` (`all-MiniLM-L6-v2`) to perform semantic search across the course catalog and university handbook.
- **Local Large Language Model**: Integrates `Qwen/Qwen2.5-0.5B-Instruct` via Hugging Face Pipelines for fully local, privacy-preserving, and offline-capable conversational AI. No API keys required.
- **Academic Tools**: Includes interactive tools for GPA calculation, timetabling, elective recommendations, and career mapping.
- **FastAPI Backend**: High-performance asynchronous backend server with a robust RESTful API and SQLite database (`academic_chatbot.db`) managed via SQLAlchemy.
- **Admin Panel & API**: Secure admin routes to retrain models, rebuild the document index, and manage courses, FAQs, and career mappings.
- **Interactive Web Frontend**: Includes an HTML/JS-based frontend served locally to interact directly with the chatbot.

## Architecture
- **Backend Framework**: FastAPI (Python)
- **Database**: SQLite (SQLAlchemy ORM)
- **Machine Learning**: Scikit-Learn (Intent Classifier), Hugging Face Transformers, SentenceTransformers, FAISS
- **Frontend**: HTML / Vanilla JavaScript served via Python's `http.server`

## Prerequisites
- **Python 3.8+**
- Git
- At least 8GB of RAM (for running the local LLM model and FAISS indices smoothly)

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd Aichatbot
   ```

2. **Create and activate a virtual environment (Optional but recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database:**
   The SQLite database is created automatically upon startup via SQLAlchemy models (`academic_chatbot.db`).

## Running the Application

For a convenient 1-click startup on Windows, you can use the provided batch script:
```cmd
start_chatbot.bat
```
This script will automatically:
1. Start the FastAPI backend on port 8001.
2. Start the Frontend server on port 8080.
3. Open the chatbot in your default web browser.

**Note on First Run**: The application will automatically download the LLM (`Qwen/Qwen2.5-0.5B-Instruct`) and sentence transformer models to your local machine. This may take several minutes depending on your internet connection.

### Starting Manually
If you prefer to start the servers manually:

**1. Start the Backend:**
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

**2. Start the Frontend:**
```bash
cd frontend
python -m http.server 8080
```

Access the frontend at `http://localhost:8080`.

## API Endpoints

- **Chat Interface**: `POST /api/chat`
- **Course Catalog**: `GET /api/courses`
- **GPA Calculation**: `POST /api/gpa/calculate`
- **Document Retrieval**: `GET /api/retrieve`
- **Admin Endpoints**: Require `x_admin_password` header
  - `POST /api/admin/rebuild_index`: Rebuilds the FAISS vector index
  - `POST /api/admin/retrain_model`: Retrains the intent classifier model
  - `POST /api/admin/courses`: Add new courses

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
MIT License
