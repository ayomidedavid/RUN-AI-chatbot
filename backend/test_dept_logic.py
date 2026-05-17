import requests
import json

BASE_URL = "http://localhost:8005/api/chat"
SESSION_ID = "test_session_123"

def ask(query):
    print(f"User: {query}")
    response = requests.post(BASE_URL, json={"query": query, "session_id": SESSION_ID})
    data = response.json()
    print(f"Bot: {data['response']}")
    print(f"Intent: {data['intent']}")
    print("-" * 20)
    return data

def run_tests():
    try:
        # 1. Greeting
        ask("Hello")
        
        # 2. Mention department code
        ask("I am in CSC")
        
        # 3. Confirm
        ask("Yes")
        
        # 4. Ask about a course
        ask("What is CSC201?")
        
        # 5. New session / check detection in course query
        global SESSION_ID
        SESSION_ID = "test_session_456"
        print("\nNew Session:")
        ask("Tell me about IFT 101")
        ask("Yes")
        
    except Exception as e:
        print(f"Error: {e}. Is the backend running?")

if __name__ == "__main__":
    run_tests()
