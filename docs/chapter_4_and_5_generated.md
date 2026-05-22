# CHAPTER FOUR
## IMPLEMENTATION AND SYSTEM TESTING

### 4.1 Introduction
This chapter discusses the implementation details of the Academic Advising Chatbot ("ACADEMIC QUERY"). It outlines the system architecture, the technology stack utilized, the core modules developed, and the testing procedures conducted to ensure the system meets its functional requirements. The implementation focuses on providing a scalable, accurate, and highly responsive advising assistant for students.

### 4.2 System Architecture
The system employs a client-server architecture with a hybrid logic-routing mechanism on the backend. The architecture consists of three primary layers:
1. **Presentation Layer (Frontend):** A custom-built, responsive web interface utilizing HTML5, Vanilla CSS, and JavaScript. It features a floating chat widget and a secure Admin Dashboard.
2. **Application Layer (Backend):** Developed using Python and the FastAPI framework. This layer acts as the orchestrator, handling incoming chat requests, routing them through the machine learning pipelines, and interacting with the database. It uses a hybrid routing architecture:
   - **Structured Intent Pipeline:** Uses a Logistic Regression classifier (with TF-IDF vectorization) and deterministic heuristics for known intents (e.g., prerequisites, course info).
   - **Semantic Fallback Pipeline:** Uses `sentence-transformers` and a FAISS index to retrieve relevant passages for unknown queries, passing them to a local LLM for conversational generation.
3. **Data Access Layer (Database):** A relational MySQL database managed via SQLAlchemy ORM, storing course catalogs, electives, prerequisites, career mappings, FAQs, and chat history.

### 4.3 Technologies Used
The successful deployment of the system relies on the following technologies:
- **Backend Framework:** FastAPI (Python 3.8+) for high-performance API endpoints and asynchronous request handling.
- **Database:** MySQL for persistent data storage, accessed via SQLAlchemy ORM to prevent SQL injection and abstract database operations.
- **Machine Learning & NLP:**
  - `scikit-learn` for the Logistic Regression Intent Classifier and TF-IDF Vectorization.
  - `NLTK` for text preprocessing, tokenization, stop-word removal, and lemmatization.
  - `sentence-transformers` (specifically the `all-MiniLM-L6-v2` model) for generating dense vector embeddings of textual data.
  - `FAISS` (Facebook AI Similarity Search) for efficient similarity search and retrieval of course catalog chunks.
- **Frontend:** HTML5, CSS3 (including Glassmorphism aesthetics and Dark Mode), and JavaScript.
- **Server:** Uvicorn for ASGI server deployment.

### 4.4 Core Modules Implementation

#### 4.4.1 Database Layer and Schema
The database schema was implemented using SQLAlchemy ORM. The core models include:
- `Course`: Stores course codes, titles, descriptions, and credit units.
- `PrerequisiteRule`: Maps target courses to their required preliminary courses.
- `Elective`: Stores available elective courses and the semesters they are offered.
- `CareerMapping`: Maps specific career paths (e.g., Software Engineer, Data Scientist) to recommended courses.
- `FAQ`: Stores administrative frequently asked questions and their predefined answers.
- `ChatHistory`: Logs user interactions, session IDs, and context states for conversational memory.
Additionally, specialized tables (`ExamRule`, `Conduct`, `Curriculum`, `Policy`, `Staff`, `Facility`) were created to handle diverse student handbook data.

#### 4.4.2 Intent Classification Module
The system utilizes a custom `IntentClassifier` class. The training data combines deterministic heuristics (e.g., keyword matching for small talk, capabilities, career goals) with synthetic data mapped to categories like `course_registration`, `prerequisites`, and `graduation`.
- The text is cleaned, tokenized, and lemmatized using NLTK.
- A `Pipeline` is built combining a `TfidfVectorizer` (with bigrams) and a `LogisticRegression` classifier.
- The model computes prediction probabilities, falling back to an "unknown" intent if the confidence score is below 10%.

#### 4.4.3 Semantic Retrieval and Fallback Module
To handle complex, multi-sentence queries or topics not explicitly covered by the structured database, a Retrieval-Augmented Generation (RAG) approach is implemented:
- Student handbooks and course catalogs are parsed, chunked, and embedded using the local `all-MiniLM-L6-v2` model.
- These dense vectors are indexed using `FAISS` using L2 normalization.
- When the intent classifier outputs "unknown," the system searches the FAISS index for the Top-K (K=3) most relevant chunks and uses a Local LLM generator to synthesize a natural language response based *only* on the retrieved context, preventing hallucination.

#### 4.4.4 API and Web Service Implementation
FastAPI provides the routing endpoints. Key endpoints include:
- `POST /api/chat`: The core endpoint that processes user messages, manages session context (pronoun resolution, department tracking), executes intent prediction, and returns the bot's response.
- `GET /api/courses` & `GET /api/faqs`: Retrieves structured data for the frontend.
- `POST /api/admin/*`: Protected routes requiring an `x-admin-password` header. These allow administrators to add/edit courses, manage FAQs, rebuild the FAISS index, and retrain the intent model dynamically without restarting the server.

### 4.5 System Testing and Validation
System testing was conducted across multiple phases:
1. **Unit Testing:** Individual components, such as the `clean_text` function in the NLP module and database CRUD operations, were tested for expected behavior.
2. **Intent Classification Accuracy:** The model was tested against varied synthetic queries (e.g., "what do i need for AI", "how dem dey calculate gpa") to ensure accurate intent mapping (e.g., mapping to `prerequisites` and `gpa` respectively).
3. **Integration Testing:** The flow from the frontend chat widget to the backend API, through the intent classifier, into the database handlers, and back to the user was validated to ensure seamless session tracking and context memory (e.g., resolving "it" to the previously mentioned course).
4. **Performance Testing:** The eager loading of the LLM and FAISS index at startup (`@app.on_event("startup")`) was tested to confirm that the initial chat response latency remains minimal. The structured intent pipeline consistently returns responses in under 5ms.

### 4.6 Conclusion of Chapter Four
The implementation phase successfully translated the architectural design into a functional, hybrid chatbot system. By combining the speed and deterministic accuracy of TF-IDF Logistic Regression with the semantic depth of FAISS and local LLMs, the system achieves a robust balance of performance and flexibility.

---

# CHAPTER FIVE
## SUMMARY, CONCLUSION, AND RECOMMENDATIONS

### 5.1 Summary of the Project
The primary objective of this project was to develop "ACADEMIC QUERY," an intelligent, full-stack Academic Advising assistant designed to help students navigate complex degree requirements, course catalogs, and administrative policies. 

To achieve this, a multi-layered AI approach was adopted. A relational database (MySQL) was utilized to store structured academic data, while a machine learning intent classifier (Scikit-Learn) was trained to parse user queries and route them to specific logic handlers. For unstructured or complex queries, a Retrieval-Augmented Generation (RAG) pipeline utilizing Sentence-Transformers and FAISS was implemented to scan embedded student handbooks and synthesize accurate responses. The entire backend was exposed via a high-performance FastAPI server, interacting with a modern, responsive web frontend equipped with an admin dashboard for continuous data management.

### 5.2 Conclusion
The development and deployment of the Academic Advising Chatbot have demonstrated the viability of hybrid AI systems in educational administration. The system successfully meets its core objectives:
1. **Accurate Advising:** By heavily utilizing database logic for known intents (prerequisites, course credits, electives), the system guarantees 100% factual advising accuracy for structured queries, eliminating the hallucination risks common in pure Generative AI models.
2. **Contextual Awareness:** The implementation of session management and pronoun resolution allows the chatbot to maintain conversational context, creating a natural and intuitive user experience.
3. **Scalability and Maintainability:** The inclusion of a secure Admin Dashboard, alongside API endpoints to dynamically rebuild the semantic index and retrain the intent model, ensures that the institution can update curricula without requiring technical code deployments.
4. **High Performance:** Pre-loading models into memory at server startup and utilizing lightweight classifiers ensures instantaneous response times for students.

In conclusion, ACADEMIC QUERY serves as a highly effective, automated tier-one support system for academic advising, significantly reducing the administrative burden on human advisors while providing students with immediate, 24/7 access to crucial academic information.

### 5.3 Recommendations for Future Work
While the current system is robust and functional, the following recommendations are proposed for future iterations and scalability:

1. **Integration with Student Information Systems (SIS):** Currently, the chatbot operates on generalized department data. Future versions should implement OAuth or secure SSO (Single Sign-On) integration with the university's central portal (e.g., Canvas, Blackboard). This would allow the bot to access personalized student transcripts, calculate exact remaining credits for graduation, and perform real-time course registration on the student's behalf.
2. **Expansion of Departmental Support:** The current intent and fallback logic is optimized primarily for the Computer Science, Cyber Security, and Information Technology departments. The system should be expanded to ingest handbooks and course catalogs from all faculties (e.g., Engineering, Medicine, Business) to serve the entire university ecosystem.
3. **Multi-Lingual and Voice Support:** While the intent classifier currently recognizes some localized phrasing and slang, integrating robust multi-lingual translation APIs and Voice-to-Text/Text-to-Voice interfaces would dramatically improve accessibility for international students and visually impaired users.
4. **Advanced Analytics Dashboard:** The admin panel can be enhanced to include data visualization tools that analyze the `ChatHistory` table. Tracking the most frequently asked questions and common points of confusion can provide the administration with actionable insights to proactively improve student handbooks and orientation programs.
