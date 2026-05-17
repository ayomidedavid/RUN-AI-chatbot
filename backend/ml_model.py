import os
import pickle
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from pathlib import Path
import re
import numpy as np

def has_nltk_resource(resource_path):
    try:
        nltk.data.find(resource_path)
        return True
    except LookupError:
        return False

HAS_WORDNET = has_nltk_resource('corpora/wordnet')
HAS_STOPWORDS = has_nltk_resource('corpora/stopwords')
HAS_PUNKT = has_nltk_resource('tokenizers/punkt') and has_nltk_resource('tokenizers/punkt_tab')

lemmatizer = WordNetLemmatizer() if HAS_WORDNET else None
stop_words = set(stopwords.words('english')) if HAS_STOPWORDS else set()

CATEGORIES = ['course_info', 'prerequisites', 'electives', 'career', 'greeting', 'small_talk', 'course_registration', 'graduation', 'gpa', 'course_management', 'department_info', 'capabilities']

QUESTION_FILE = Path(__file__).resolve().parents[1] / 'data' / 'quetion.txt'

QUESTION_CATEGORY_KEYWORDS = {
    'course_registration': [
        'register', 'register for this semester', 'units am i allowed', 'allowed to take', 'maximum unit', 'max unit', 'extra courses', 'required load', 'compulsory courses', 'compulsory course'
    ],
    'prerequisites': [
        'prerequisite', 'prereqs', 'failed its prerequisite', 'skip a required course', 'need to take', 'requirements for this course'
    ],
    'electives': [
        'elective', 'electives', 'career goals', 'choose the right electives', 'best for', 'what elective', 'elective courses'
    ],
    'career': [
        'career path', 'chosen career', 'want to be a', 'career', 'important for my chosen career'
    ],
    'graduation': [
        'graduate', 'graduation requirements', 'minimum number of units', 'total number of units', 'direct entry'
    ],
    'gpa': [
        'gpa', 'grade', 'marks', 'score', '40 marks'
    ],
    'course_management': [
        'add or drop', 'clash', 'timetable', 'conflict', 'schedule'
    ],
    'capabilities': [
        'what can you do', 'how do you work', 'what is your scope', 'help me', 'guide', 'features', 'tell me about yourself'
    ],
    'small_talk': [
        'how are you', 'how are you doing', 'thank you', 'thanks', 'bye', 'goodbye', 'ok', 'okay', 'cool', 'nice', 'lol',
        'how far', 'bawo ni', 'kedu', 'ndewo', 'sannu', 'ina kwana'
    ]
}


def load_question_examples():
    if not QUESTION_FILE.exists():
        return []

    examples = []
    current_question = ""
    with QUESTION_FILE.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            numbered = re.match(r'^\d+\.\s*(.+)$', line)
            if numbered:
                if current_question:
                    examples.append(current_question.strip())
                current_question = numbered.group(1).strip()
            elif current_question:
                current_question = f"{current_question} {line}".strip()
            else:
                examples.append(line)

        if current_question:
            examples.append(current_question.strip())

    normalized_examples = []
    for question in examples:
        if question.lower().startswith('i want to be a <career path>'):
            normalized_examples.extend([
                'I want to be a cybersecurity expert, what electives should I register?',
                'I want to be a software engineer, what electives should I register?',
                'I want to be a data scientist, what electives should I register?',
            ])
        else:
            normalized_examples.append(question)

    examples = normalized_examples
    return examples


def guess_intent_for_question(question):
    text = question.lower()
    if any(k in text for k in ['how are you', 'thank you', 'thanks', 'goodbye', 'bye']):
        return 'small_talk'
    if any(k in text for k in ['want to be', 'career path', 'career goals', 'chosen career', 'not very good at programming']):
        return 'career'
    if any(k in text for k in ['graduate', 'graduation requirements', 'direct entry student units']):
        return 'graduation'
    if any(k in text for k in ['prerequisite', 'skip a required course', 'failed its prerequisite']):
        return 'prerequisites'
    for intent, keywords in QUESTION_CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return intent
    if 'course' in text and 'what' in text:
        return 'course_info'
    if any(k in text for k in ['what', 'how', 'can you', 'help']):
        return 'capabilities'
    return 'course_registration'


def build_training_examples():
    examples = list(SYNTHETIC_DATA)
    for question in load_question_examples():
        intent = guess_intent_for_question(question)
        examples.append((question, intent))
    # Deduplicate while preserving order
    seen = set()
    unique_examples = []
    for sentence, label in examples:
        key = (sentence.lower(), label)
        if key not in seen:
            seen.add(key)
            unique_examples.append((sentence, label))
    return unique_examples

# 2.3 Synthesized Data for Intent Classification
SYNTHETIC_DATA = [
    ("What courses do I take for computer science?", "course_info"),
    ("tell me about csc 201", "course_info"),
    ("what is the description of software engineering course?", "course_info"),
    ("how many credits is data structures?", "course_info"),
    ("what is csc301", "course_info"),
    ("tell me about csc301", "course_info"),
    
    ("what are the prerequisites for csc 311?", "prerequisites"),
    ("wetin be prerequisite for csc 311", "prerequisites"),
    ("kini prerequisite fun csc 311", "prerequisites"),
    ("gini bu prerequisite for csc 311", "prerequisites"),
    ("menene prerequisite for csc 311", "prerequisites"),
    ("do I need to take math before algorithms?", "prerequisites"),
    ("what courses are required before artificial intelligence?", "prerequisites"),
    ("what is needed for machine learning?", "prerequisites"),
    ("what do i need for AI", "prerequisites"),
    ("what are the prereqs for AI", "prerequisites"),
    
    ("what electives can I take in year 3?", "electives"),
    ("tell me about elective courses", "electives"),
    ("can I choose a cybersecurity elective?", "electives"),
    ("list optional courses", "electives"),
    
    ("what courses are good for becoming a data scientist?", "career"),
    ("how do I become a software engineer?", "career"),
    ("career path for devops", "career"),
    ("what should i study to be in machine learning?", "career"),
    
    ("hello", "greeting"),
    ("hi", "greeting"),
    ("hi there", "greeting"),
    ("hey", "greeting"),
    ("yo", "greeting"),
    ("what's up", "greeting"),
    ("how far", "greeting"),
    ("wetin dey", "greeting"),
    ("bawo ni", "greeting"),
    ("e kaaro", "greeting"),
    ("e kaasan", "greeting"),
    ("e kaale", "greeting"),
    ("kedu", "greeting"),
    ("ndewo", "greeting"),
    ("sannu", "greeting"),
    ("ina kwana", "greeting"),
    ("ina wuni", "greeting"),
    ("good morning", "greeting"),
    ("hey bot", "greeting"),

    # Small Talk
    ("how are you", "small_talk"),
    ("how are you doing", "small_talk"),
    ("how is it going", "small_talk"),
    ("how body", "small_talk"),
    ("se daadaa ni", "small_talk"),
    ("kedu ka imere", "small_talk"),
    ("ya kake", "small_talk"),
    ("ya kike", "small_talk"),
    ("yaya dai", "small_talk"),
    ("are you okay", "small_talk"),
    ("thank you", "small_talk"),
    ("thanks", "small_talk"),
    ("ese", "small_talk"),
    ("daalu", "small_talk"),
    ("nagode", "small_talk"),
    ("appreciate it", "small_talk"),
    ("bye", "small_talk"),
    ("goodbye", "small_talk"),
    ("odabo", "small_talk"),
    ("ka odi", "small_talk"),
    ("sai anjima", "small_talk"),
    ("ok", "small_talk"),
    ("okay", "small_talk"),
    ("cool", "small_talk"),
    ("nice", "small_talk"),
    ("lol", "small_talk"),
    ("haha", "small_talk"),

    # Course Registration
    ("what courses should I register for this semester", "course_registration"),
    ("wetin course i go register this semester", "course_registration"),
    ("abeg what courses should i register", "course_registration"),
    ("which course i fit carry this semester", "course_registration"),
    ("melo ni units mo le register", "course_registration"),
    ("kedu courses ka m ga register", "course_registration"),
    ("course nawa zan yi register", "course_registration"),
    ("how many courses am I allowed to take per semester", "course_registration"),
    ("how many units i fit register", "course_registration"),
    ("nawa ne maximum units", "course_registration"),
    ("how many units am I allowed to take per semester", "course_registration"),
    ("can I take extra courses beyond the required load", "course_registration"),
    ("i fit take extra course", "course_registration"),
    ("what are the compulsory courses for my level", "course_registration"),
    ("wetin be compulsory courses for my level", "course_registration"),
    ("what compulsory courses do I need for 200 level", "course_registration"),
    ("what compulsory courses do I need for 300 level", "course_registration"),
    ("list compulsory courses for my level", "course_registration"),

    # Graduation Requirements
    ("how can I plan my courses to graduate on time", "graduation"),
    ("how do I know if I am meeting my graduation requirements", "graduation"),
    ("what is the minimum number of units required to graduate", "graduation"),
    ("how many units do I need to graduate", "graduation"),
    ("how many units i need to graduate", "graduation"),
    ("wetin i need to graduate", "graduation"),
    ("melo ni units to graduate", "graduation"),
    ("units ole ka m choro to graduate", "graduation"),
    ("units nawa nake bukata to graduate", "graduation"),
    ("what is the total number of units I should have registered to graduate", "graduation"),
    ("direct entry student units to graduate", "graduation"),

    # GPA
    ("how is GPA calculated", "gpa"),
    ("how dem dey calculate gpa", "gpa"),
    ("bawo ni won se calculate gpa", "gpa"),
    ("kedu ka esi calculate gpa", "gpa"),
    ("yaya ake calculate gpa", "gpa"),
    ("what is the minimum GPA I need to stay in the program", "gpa"),
    ("what happens if my GPA falls below the required level", "gpa"),
    ("can I retake a course I failed and how does it affect my GPA", "gpa"),
    ("if I score 40 marks what grade would I have", "gpa"),

    # Course Management
    ("can I add or drop a course after registration", "course_management"),
    ("what should I do if there is a clash in my timetable", "course_management"),
    ("how do I handle timetable conflict", "course_management"),

    # Electives
    ("what elective courses are available in my department", "electives"),
    ("which electives are best for cybersecurity", "electives"),
    ("which elective good for cybersecurity", "electives"),
    ("wetin elective good for data science", "electives"),
    ("which electives are best for software engineering", "electives"),
    ("which electives are best for data science", "electives"),
    ("how do I choose the right electives for my career goals", "electives"),
    ("I am not good at programming what elective should I take", "electives"),
    ("I want to be a software engineer what electives should I register", "career"),
    ("i wan be software engineer wetin elective i go register", "career"),
    ("mo fe di software engineer what elective should i register", "career"),
    ("achoro m ibu data scientist what elective should i register", "career"),
    ("ina son zama cybersecurity expert what elective should i register", "career"),
    ("I want to be a data scientist what electives should I register", "career"),
    ("I want to be a cybersecurity expert what electives should I register", "career"),

    # Department Info
    ("I am in computer science", "department_info"),
    ("I am a CSC student", "department_info"),
    ("my department is computer science", "department_info"),
    ("I study information technology", "department_info"),
    ("I am in the CYB department", "department_info"),
    ("I am an IFT student", "department_info"),
    ("my course is computer science", "department_info"),
    ("cyber security department", "department_info"),
    ("information technology student", "department_info"),
    ("I am a Computer Science major", "department_info"),
    ("I'm in Cyber Security", "department_info"),

    # Capabilities
    ("what can you do", "capabilities"),
    ("how do you work", "capabilities"),
    ("what is your purpose", "capabilities"),
    ("how can you help me", "capabilities"),
    ("what type of questions can you answer", "capabilities"),
    ("show me your features", "capabilities"),
    ("tell me about ACADEMIC QUERY", "capabilities"),
]

def clean_text(text):
    # Remove non-alphanumeric chars (keep numbers for course codes)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', str(text))
    text = text.lower()
    # Tokenize
    tokens = nltk.word_tokenize(text) if HAS_PUNKT else text.split()
    # Lemmatize and remove stopwords
    cleaned = [
        lemmatizer.lemmatize(word) if lemmatizer else word
        for word in tokens
        if word not in stop_words
    ]
    return " ".join(cleaned)

class IntentClassifier:
    def __init__(self, model_path="intent_model.pkl"):
        self.model_path = model_path
        self.pipeline = None

    def train_and_save(self):
        print("Training Intent Classifier...")
        
        # Combine synthetic data with examples from quetion.txt
        all_data = build_training_examples()
        
        sentences = [clean_text(x[0]) for x in all_data]
        labels = [x[1] for x in all_data]

        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
            ('clf', LogisticRegression(random_state=42))
        ])

        self.pipeline.fit(sentences, labels)
        
        with open(self.model_path, "wb") as f:
            pickle.dump(self.pipeline, f)
        print(f"Model saved to {self.model_path}")

    def load_model(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, "rb") as f:
                self.pipeline = pickle.load(f)
        else:
            self.train_and_save()

    def predict(self, text):
        if not self.pipeline:
            self.load_model()
        cleaned = clean_text(text)
        prediction = self.pipeline.predict([cleaned])[0]
        # Get probability
        probabilities = self.pipeline.predict_proba([cleaned])[0]
        max_prob = max(probabilities)
        
        # Threshold to avoid random guesses
        if max_prob < 0.1:
            return "unknown"
            
        return prediction

if __name__ == "__main__":
    clf = IntentClassifier()
    clf.train_and_save()
    
    # Test
    print("Test 'what is csc301':", clf.predict("what is csc301"))
    print("Test 'what do i need for AI':", clf.predict("what do i need for AI"))


class EmbeddingModel:
    """Helper to load a SentenceTransformer model (local if available) and compute/save embeddings."""
    def __init__(self, model_name_or_path='sentence-transformers/all-MiniLM-L6-v2', local_subdir='all-MiniLM-L6-v2'):
        base = Path(__file__).resolve().parents[1]
        self.local_path = str(base / 'models' / local_subdir)
        self.model_name_or_path = model_name_or_path
        self.model = None

    def load(self):
        from sentence_transformers import SentenceTransformer

        # Prefer local cloned repo if it exists (avoids extra downloads).
        # Use offline mode only when loading from a local path.
        if os.path.isdir(self.local_path):
            print(f"Loading SentenceTransformer from local path: {self.local_path}")
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            try:
                self.model = SentenceTransformer(self.local_path)
                return
            except Exception as e:
                print('Local load failed, will attempt remote load:', e)
                # Ensure offline mode is disabled before trying remote
                os.environ.pop('HF_HUB_OFFLINE', None)
                os.environ.pop('TRANSFORMERS_OFFLINE', None)

        # Attempt remote load with retries (useful when network is flaky).
        print(f"Loading SentenceTransformer from remote id: {self.model_name_or_path}")
        import time
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                self.model = SentenceTransformer(self.model_name_or_path)
                return
            except Exception as e:
                print(f"Remote load attempt {attempt} failed: {e}")
                if attempt < max_attempts:
                    wait = 2 ** attempt
                    print(f"Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print("All remote download attempts failed. If you are offline, run backend/download_model.py to download the model into backend/models/all-MiniLM-L6-v2")
                    raise

    def embed(self, texts, batch_size=32):
        if self.model is None:
            self.load()
        return self.model.encode(texts, batch_size=batch_size, convert_to_numpy=True)

    def save_embeddings(self, texts, out_path):
        embs = self.embed(texts)
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(out_path), embs)
        return str(out_path)


# Example quick-run when this file executed directly
if __name__ == '__main__':
    # create embeddings for a couple sample sentences and save to backend/models/
    emb_model = EmbeddingModel()
    samples = ["What courses do I take for computer science?", "How many units am I allowed to take per semester?"]
    try:
        embs = emb_model.embed(samples)
        save_file = Path(__file__).resolve().parents[1] / 'models' / 'sample_embeddings.npy'
        np.save(str(save_file), embs)
        print('Saved sample embeddings to', save_file)
    except Exception as e:
        print('Embedding test failed:', e)
