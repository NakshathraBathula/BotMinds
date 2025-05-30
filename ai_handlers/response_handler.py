# ai_handlers/response_handler.py
import os  # Add this line
import re
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from ai_handlers.memory_manager import update_user_memory, user_memory, user_memory_lock
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

# Initialize AI components
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Load FAISS index
try:

    index = faiss.read_index("data/faiss_index.bin")
    with open("data/faiss_metadata.json", "r", encoding='utf-8' ) as f:
        metadata = json.load(f)
        texts = metadata["texts"]
        urls = metadata["urls"]
        print("FAISS index and metadata loaded successfully.")
except Exception as e:
    print(f"Error loading FAISS index or metadata: {e}")
    texts = []
    urls = []
def kmit_response(query, user_id):
    # ... KMIT response implementation ...
    """
    Retrieve the top relevant text chunks from FAISS and generate a KMIT-specific response
    via Gemini AI. The prompt instructs the model to answer only KMIT-related queries.
    """
    with user_memory_lock:
        user_data = user_memory.setdefault(user_id, {})
        user_name = user_data.get("name", None)
        last_department = user_data.get("last_department", None)
        conversation_history = user_data.get("conversation_history", [])
    
    # Retrieve FAISS context for KMIT data
    query_embedding = embed_model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_embedding, len(texts))
    retrieved_texts = [texts[i] for i in indices[0][:30]]
    retrieved_context = "\n".join(retrieved_texts)
    
    memory_info = f"User's name is {user_name}." if user_name else "User's name is not yet known."
    dept_info = f"Previously discussed department: {last_department}." if last_department else "No department has been discussed yet."
    
    # Build the unified prompt
    prompt = rf"""
    Context:
    {retrieved_context}

You are Mithrr, an advanced and friendly AI assistant powered by RTRP 28-RP 3002 Botminds specialized in KMIT college administrative data. You should engage in a warm, conversational tone.

- Answer only queries related to KMIT administrative data (attendance, fee structure, timetable, results, faculty details, exam notifications, etc.).
- If the user's query includes code snippets or academic subject discussions (for example programming code, detailed subject theory questions), respond with:
  "It seems like you're looking for detailed code or subject assistance. Please switch to Code Assistance Mode by typing '/code-mode'."
- If the query is not related to KMIT college data, respond with:
  "This query is not related to KMIT college data."

User Information:
{memory_info}
{dept_info}

User: {query}
Mithrr:"""

    
    # Generate response via Gemini
    response = model.generate_content(prompt)
    raw_response = response.text.strip().replace("\\n", "\n")
    cleaned_response = re.sub(r'\*(\w+)\*', r'\1', raw_response)
    
    # Update user memory if name or department is mentioned in the query
    name_match = re.search(r"My name is (\w+)", query, re.IGNORECASE)
    if name_match:
        with user_memory_lock:
            user_data["name"] = name_match.group(1)
    dept_match = re.search(r"\b(IT|CSE|ECE|MECH|Civil|AIML)\b", query, re.IGNORECASE)
    if dept_match:
        with user_memory_lock:
            user_data["last_department"] = dept_match.group(1).upper()
    
    with user_memory_lock:
        update_user_memory(user_data, query, cleaned_response)
        user_data["last_query"] = query
    return cleaned_response

def code_response(query, user_id):
    # ... Code response implementation ...
    """
    Handle responses for a wide range of problem-solving logics and complex coding queries.
    The prompt instructs Mithrr to solve intricate problems, including programming, algorithmic,
    logical, and analytical challenges, providing a detailed, step-by-step explanation
    of the reasoning and including code, mathematical derivations, or logical proofs where relevant.
    Mithrr should leverage its extensive knowledge base to tackle complex inquiries.
    """
    with user_memory_lock:
        user_data = user_memory.setdefault(user_id, {})
        conversation_history = user_data.get("conversation_history", [])

    if conversation_history:
        history_lines = [f"User: {q}\nMithrr: {a}" for q, a in conversation_history[-3:]]
        history_str = "\n".join(history_lines)
    else:
        history_str = "No conversation history yet."

    prompt = f"""
You are Mithrr, an advanced AI assistant provided by RTRP 28-RP 3002 Botminds created exclusively for solving programming challenges,
algorithmic problems, logic-building tasks, and advanced software development issues.
You possess expert-level knowledge in:
- Coding (Python, C++, Java, etc.)
- Data structures and algorithms
- Debugging and optimization
- System design and software architecture
- Logical reasoning and computational thinking

Your job is to provide clear, detailed, step-by-step solutions using:
- Code examples
- Algorithmic breakdowns
- Logical derivations and proofs
- Mathematical expressions (in LaTeX, enclosed in $\$$ or $$\$$)

⚠️ IMPORTANT: You **must not** answer queries related to:
- College-specific information (e.g., KMIT-related queries)
- Academic subjects or syllabus topics (e.g., "features of Java", "OOP concepts")
- General knowledge or factual questions (e.g., "planets in the solar system")
- Non-coding discussions or unrelated topics

You are strictly configured to handle only **coding, logic, and algorithmic** queries.

Conversation History:
{history_str}

User: {query}
Mithrr:"""



    response = model.generate_content(prompt)
    raw_response = response.text.strip().replace("\\n", "\n")
    cleaned_response = re.sub(r'\*(\w+)\*', r'\1', raw_response)

    with user_memory_lock:
        update_user_memory(user_data, query, cleaned_response)
        user_data["last_query"] = query

    return cleaned_response

def subject_response(query, user_id):
    # ... Subject response implementation ...
    """
    Handle responses related to academic subjects across all educational levels (KG to PG).
    Incorporates relevant FAISS context and provides structured, clear explanations or summaries
    based on user intent.
    """
    with user_memory_lock:
        user_data = user_memory.setdefault(user_id, {})
        conversation_history = user_data.get("conversation_history", [])
        user_name = user_data.get("name", None)

    query_embedding = embed_model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_embedding, len(texts))
    retrieved_texts = [texts[i] for i in indices[0][:20]]
    retrieved_context = "\n".join(retrieved_texts)

    if conversation_history:
        history_lines = [f"User: {q}\nMithrr: {a}" for q, a in conversation_history[-3:]]
        history_str = "\n".join(history_lines)
    else:
        history_str = "No conversation history yet."

    prompt = f"""
Context:
{retrieved_context}

You are Mithrr, an AI assistant provided by RTRP 28-RP 3002 Botminds with deep expertise in academic subjects across all education levels—from kindergarten to postgraduate studies (including BTech, MTech, and beyond). Your sole purpose is to address academic subject queries. When a user asks a question, follow these guidelines:

- Structure answers with key concepts first
- Use diagrams/examples to explain complex topics
- Highlight real-world applications of theories
- If the query requires a detailed explanation, break it down step-by-step with examples, bullet points, and clear logical reasoning.
- If the user requests a summary or a quick answer, keep your response concise yet accurate.
- Tailor your explanation style to the subject matter, whether it is science, mathematics, literature, social studies, engineering, or another academic field.
- **Do not respond** to queries that involve coding instructions (e.g., "write code to...") or institution-specific topics (e.g., KMIT-related questions). You must strictly focus on academic subjects.

User Name: {user_name if user_name else "Unknown"}

Conversation History:
{history_str}

User: {query}
Mithrr:"""


    response = model.generate_content(prompt)
    raw_response = response.text.strip().replace("\\n", "\n")
    cleaned_response = re.sub(r'\*(\w+)\*', r'\1', raw_response)

    with user_memory_lock:
        update_user_memory(user_data, query, cleaned_response)
        user_data["last_query"] = query

    return cleaned_response