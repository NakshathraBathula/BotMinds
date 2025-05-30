# ai_handlers/memory_manager.py
import threading

user_memory = {}
user_memory_lock = threading.Lock()

def update_user_memory(user_data, query, response):
    history = user_data.setdefault("conversation_history", [])
    history.append((query, response))
    if len(history) > 7:
        history.pop(0)