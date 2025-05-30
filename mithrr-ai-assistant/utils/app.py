# app.py
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from pyngrok import ngrok
import os
import asyncio
from dotenv import load_dotenv
import requests
from services.firebase_service2 import update_firebase
from services.scraper_service import fetch_attendance, fetch_timetable_data, fetch_results_data
from services.news_service import (
    fetch_flash_news,
    fetch_news_bulletins,
    fetch_exam_notifications,
    fetch_exam_timetables,
    
)
from ai_handlers.response_handler import (
    kmit_response,
    code_response,
    subject_response
)
from ai_handlers.memory_manager import user_memory, user_memory_lock

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
CORS(app)

@app.before_request
def assign_user_id():
    if "user_id" not in session:
        session["user_id"] = os.urandom(16).hex()

@app.route('/')
def home():
    return render_template('i.html')

@app.route("/chat/kmit", methods=["POST"])
def chat_kmit():
    try:
        data = request.json
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "Query is required"}), 400
        user_id = session.get("user_id", "default_user")
        answer = kmit_response(query, user_id)
        return jsonify({
            "query": query,
            "response": answer
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat/code", methods=["POST"])
def chat_code():
    try:
        data = request.json
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "Query is required"}), 400
        user_id = session.get("user_id", "default_user")
        answer = code_response(query, user_id)
        return jsonify({
            "query": query,
            "response": answer
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat/subject", methods=["POST"])
def chat_subject():
    try:
        data = request.json
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "Query is required"}), 400
        user_id = session.get("user_id", "default_user")
        answer = subject_response(query, user_id)
        return jsonify({
            "query": query,
            "response": answer
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# News and Exam endpoints
@app.route("/news_bulletins", methods=["GET"])
def news_bulletins():
    try:
        result = fetch_news_bulletins()
        if "error" in result:
            return jsonify(result), result.get("status", 500)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/flash_news", methods=["GET"])
def flash_news():
    try:
        news = fetch_flash_news()
        return jsonify(news)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/exam_notifications", methods=["GET"])
def exam_notifications():
    try:
        result = fetch_exam_notifications()
        if "error" in result:
            return jsonify(result), result.get("status", 500)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/exam_timetables", methods=["GET"])
def exam_timetables():
    try:
        timetables = fetch_exam_timetables()
        return jsonify(timetables)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Student data endpoints
# Student data endpoints
@app.route("/attendance", methods=["POST"])
def attendance():
    data = request.json
    try:
        result = asyncio.run(fetch_attendance(
            data.get("mobile_number"),
            data.get("password")
        ))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/results", methods=["POST"])
def results():
    data = request.json
    try:
        result = asyncio.run(fetch_results_data(
            data.get("mobile_number"),
            data.get("password")
        ))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/timetable", methods=["POST"])
def timetable():
    data = request.json
    try:
        result = asyncio.run(fetch_timetable_data(
            data.get("mobile_number"),
            data.get("password")
        ))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    ngrok.set_auth_token("2vE70uA4Iy5uUSAFTCY2GzmWSSg_3i2rTxaFbHJc4AJaUQsua")
    public_url = ngrok.connect(5000).public_url
    update_firebase(public_url)

    # Print and force an immediate flush so you see it in the console right now:
    print("Firebase URL updated successfully!", flush=True)
    print(f" * Ngrok tunnel running at: {public_url}", flush=True)

    # Turn off the extra reloader-process
    app.run(port=5000, use_reloader=False)
