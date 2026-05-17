# Academic Advising Chatbot 🎓

# ACADEMIC QUERY — Academic Advising Chatbot 🎓

ACADEMIC QUERY is an intelligent, full-stack Academic Advising assistant to help Computer Science students navigate degree requirements. It answers questions about courses, prerequisites, electives, career pathways, and administrative FAQs.

## ✨ Features

- **Course Catalog & Details**: Easily ask about course descriptions and credit units (e.g., "Tell me about CSC 475").
- **Prerequisite Checks**: Instantly find out what subjects you must complete before tackling advanced classes.
- **Career Path Mapping**: Tells you exactly which courses to focus on to become a Software Engineer, Data Scientist, or AI Specialist.
- **FAQ Handling**: Designed with an automated fuzzy-matching algorithm to quickly answer administrative questions.
- **Modern Landing Page**: A responsive, dark-mode, glassmorphism web interface with an integrated floating chat widget.

## 🛠️ Technology Stack

- **Frontend:** HTML5, CSS3 (Vanilla), JavaScript, Custom Web Interface design
- **Backend:** Python + FastAPI 
- **Database:** MySQL + SQLAlchemy ORM
- **Machine Learning & Retrieval:** Scikit-Learn (Logistic Regression, TF-IDF), NLTK preprocessing, plus semantic retrieval using `sentence-transformers` + FAISS (for document search)
- **Data Pipeline:** Custom OCR Parsing Scripts (`data_populator.py`) to systematically ingest raw student handbook texts.

## 🚀 Getting Started

### Prerequisites
Make sure you have the following installed on your machine:
- Python 3.8+
- MySQL Server (running locally)
- Node/NPM (Optional, depending on future frontend expansions)

### 1. Database Setup
1. Ensure your local MySQL server is running.
2. In your MySQL terminal or client (e.g., phpMyAdmin), create a new database:
   ```sql
   CREATE DATABASE academic_chatbot_db;
   ```
3. Update your credentials in `backend/database.py` (e.g., `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`) if they differ from typical `root` defaults without a password.

### 2. Environment Setup
From the `backend` directory, install all required dependencies (assuming a virtual environment is active):
```bash
python -m pip install -r requirements.txt
```
*(Make sure to download the necessary NLTK corpora if asked, though the `ml_model.py` script attempts to download them quietly).*

### 3. Model Training & Data Population
Before starting the API, you must ingest the course data and train the AI model:
```bash
# 1. Train the Intent Classification Model
python backend/ml_model.py

# 2. Extract and Populate the Database
python backend/data_populator.py
```
### 3. Indexing, Model Training & Data Population
This project supports two complementary components:

- Intent classification (small TF‑IDF + logistic model). Train it locally with:

```bash
python backend/ml_model.py
```
python backend/index_documents.py --model backend/models/all-MiniLM-L6-v2 --out backend

- Semantic retrieval over the course catalog (recommended): build an embedding index from `backend/extracted_data.txt` using `sentence-transformers` and FAISS. Run:

```bash
python backend/index_documents.py
```

The indexing step creates `backend/faiss.index` and `backend/chunks.pkl`. Ensure `backend/extracted_data.txt` exists before running the indexer.

- Populate the database (if needed):

```bash
python backend/data_populator.py
```

### 4. Running the Application
1. **Start the Backend:**
   From the project root directory, run the FastAPI server. Use `--host 0.0.0.0` to expose it to your local network so your phone can reach it:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
   ```
   
2. **Start the Frontend:**
   To access the site from your phone, you must serve the frontend folder over an HTTP server (double-clicking the file won't work on mobile). Open a *new terminal window*, navigate to the `frontend` folder, and run:
   ```bash
   cd frontend
   python -m http.server 8080
   ```

3. **Accessing on Your Computer & Phone:**
   - **On your Computer:** Open your web browser and go to `http://localhost:8080`.
   - **On your Phone:** Ensure your phone is connected to the same Wi-Fi as your PC. Open your mobile browser and enter your computer's local IP address followed by the port, e.g.: `http://172.20.10.3:8080`. *(You can find your exact IP by running `ipconfig` in your command prompt and looking for the IPv4 Address under Wireless LAN adapter Wi-Fi)*.

## 🤖 Usage Examples

You can test the chatbot using queries like:
- "What is the description for CSC 475?" (Course Info)
- "What are the prerequisites for CSC 453?" (Prerequisites)
- "What courses should I take to become a Data Scientist?" (Careers)
- "What are electives?" (FAQ)

## 🔐 Admin Dashboard

The application includes a secure **Admin Dashboard** allowing you to add, edit, or delete courses directly from your browser without editing text files.

1. **Access the Dashboard:** Go to `http://localhost:8080/admin.html` (or use your local IP address).
2. **Default Password:** To log in, enter the default admin password: `admin123`.
3. **Manage Courses:** Use the "Add New Course" button to create entries, or the Edit/Delete buttons to modify the existing database. All changes are instantly synced with the AI Adviser!
http://192.168.199.22:8080

API helper endpoints
- `GET /api/retrieve?q=...&k=3` — returns top-k retrieved passages from the course catalog (used by the chatbot fallback).
- `POST /api/admin/rebuild_index` — rebuilds the FAISS index from `backend/extracted_data.txt` (admin header `x-admin-password: admin123`).# RUN-AI-chatbot
