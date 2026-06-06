import os
import logging
import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)

# We use Qwen2.5-0.5B-Instruct because it is incredibly smart, lightweight (~1GB),
# and runs very fast even on standard laptop CPUs without needing a massive GPU.
MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct" 

# Global variable for lazy loading so we don't block the server startup
_generator = None

def get_generator():
    global _generator
    if _generator is None:
        logger.info(f"Loading local LLM ({MODEL_NAME}). This may take a minute on the first run as it downloads the model...")
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            if device == "cpu":
                # Optimize PyTorch CPU threading to prevent context switching thrashing
                torch.set_num_threads(4)
                
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None,
                local_files_only=True
            )
            if device == "cpu":
                model = model.to(device)
                
            _generator = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device=0 if device == "cuda" else -1
            )
            logger.info(f"Local LLM ({MODEL_NAME}) loaded successfully on {device}!")
        except Exception as e:
            logger.exception("Failed to load local LLM")
            _generator = "FAILED"
    return _generator

def generate_conversational_response(user_query, factual_context, intent, chat_history):
    """
    Enhances the hardcoded factual response into a natural, conversational response
    using a fully local, open-source model. No API keys required!
    """
    generator = get_generator()
    
    if generator == "FAILED" or not generator:
        # Fallback to the original hardcoded factual response if local model fails to load
        return factual_context

    # Prepare the messages in ChatML format which Qwen understands perfectly
    messages = [
        {
            "role": "system", 
            "content": f"You are 'ACADEMIC QUERY', an intelligent, highly polite, and professional academic advising chatbot for a university. Your goal is to provide accurate academic information based ONLY on the provided context.\n\nFactual Context from Database: {factual_context}\n\nRecent Conversation History:\n{chat_history}\n\nRule: Do not invent facts. Answer the user's latest query directly, taking into account the conversation history if they are asking a follow-up question. Quote the factual context directly if providing specific course information."
        },
        {
            "role": "user", 
            "content": user_query
        }
    ]
    
    # Apply the model's specific chat template
    prompt = generator.tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    try:
        outputs = generator(
            prompt,
            max_new_tokens=1024,
            do_sample=False,  # Greedy search is significantly faster on CPU and mathematically stable/factual
            repetition_penalty=1.1,
            return_full_text=False
        )
        response_text = outputs[0]["generated_text"].strip()
        return response_text
    except Exception as e:
        logger.exception("Error generating response with local LLM")
        return factual_context
