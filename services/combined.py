from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
import os
import tempfile
import base64
import time
import threading
import queue
import re
import speech_recognition as sr
from gtts import gTTS
from flask_socketio import SocketIO
from langdetect import detect, LangDetectException
import google.generativeai as genai

app = Flask(__name__)
socketio = SocketIO(app)

# -------------------- Legal Assistant Setup --------------------
LEGAL_API_KEY = "qCrx2JAOa9tDelNuVPhSusV5Fogl1NEL"
LEGAL_MODEL = "mistral-medium"
LEGAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
legal_token = 0
legal_tts_queue = queue.Queue()

def get_legal_response(user_input, language="en"):
    if language != "en":
        system_prompt = (
            "You are an AI legal assistant. Provide clear and concise legal information. "
            "Begin by summarizing the legal issue, then outline relevant statutes or guidelines. "
            "Respond in the same language as the user's query. "
            "Include a disclaimer stating that this is not legal advice and that users should consult a qualified attorney for personalized counsel."
        )
    else:
        system_prompt = (
            "You are an AI legal assistant. Provide clear and concise legal information. "
            "Begin by summarizing the legal issue, then outline relevant statutes or guidelines. "
            "Include a disclaimer stating that this is not legal advice and that users should consult a qualified attorney for personalized counsel."
        )
    headers = {
        "Authorization": f"Bearer {LEGAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": LEGAL_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }
    try:
        response = requests.post(LEGAL_ENDPOINT, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        error_message = f"Error: Unable to fetch legal response. {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_message += f"\nResponse details: {e.response.text}"
        print(error_message)
        return error_message

def stream_response_legal(user_input, token, language="en"):
    global legal_token
    if token != legal_token:
        return
    socketio.emit('thinking_status', {'status': True}, namespace='/legal')
    try:
        full_response = get_legal_response(user_input, language)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', full_response) if s.strip()]
        print(f"[LEGAL] Processing response with {len(sentences)} sentences")
        accumulated_text = ""
        for sentence in sentences:
            if token != legal_token:
                print("[LEGAL] Token changed, stopping response streaming")
                break
            accumulated_text += (" " if accumulated_text else "") + sentence
            socketio.emit('response_stream', {'text': accumulated_text, 'is_final': False}, namespace='/legal')
            print(f"[LEGAL] Adding sentence to TTS queue: '{sentence}'")
            legal_tts_queue.put((token, sentence))
            socketio.sleep(0.3)
        if token == legal_token:
            socketio.emit('response_stream', {'text': accumulated_text, 'is_final': True}, namespace='/legal')
    except Exception as e:
        print(f"[LEGAL] Error in stream_response: {str(e)}")
        socketio.emit('error_message', {'message': f'Error generating legal response: {str(e)}'}, namespace='/legal')
    finally:
        if token == legal_token:
            socketio.emit('thinking_status', {'status': False}, namespace='/legal')

# -------------------- Medical Assistant Setup --------------------
def get_medical_response(user_input, language="en"):
    if language != "en":
        system_prompt = (
            "You are an AI medical assistant. Provide your response in clear, short sentences separated by periods. "
            "First tell the user what you're going to explain, then provide the information. "
            "If symptoms are mentioned, suggest possible conditions and first-aid remedies. Recommend only OTC medicines. "
            "Respond in the same language as the user's query. If symptoms are severe, suggest consulting a doctor."
        )
    else:
        system_prompt = (
            "You are an AI medical assistant. Provide your response in clear, short sentences separated by periods. "
            "First tell the user what you're going to explain, then provide the information. "
            "If symptoms are mentioned, suggest possible conditions and first-aid remedies. Recommend only OTC medicines. "
            "If symptoms are severe, suggest consulting a doctor."
        )
    headers = {
        "Authorization": f"Bearer {LEGAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": LEGAL_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }
    try:
        response = requests.post(LEGAL_ENDPOINT, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        error_message = f"Error: Unable to fetch medical response. {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_message += f"\nResponse details: {e.response.text}"
        print(error_message)
        return error_message

medical_token = 0
medical_tts_queue = queue.Queue()

def stream_response_medical(user_input, token, language="en"):
    global medical_token
    if token != medical_token:
        return
    socketio.emit('thinking_status', {'status': True}, namespace='/medical')
    try:
        full_response = get_medical_response(user_input, language)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', full_response) if s.strip()]
        print(f"[MEDICAL] Processing response with {len(sentences)} sentences")
        accumulated_text = ""
        for sentence in sentences:
            if token != medical_token:
                print("[MEDICAL] Token changed, stopping response streaming")
                break
            accumulated_text += (" " if accumulated_text else "") + sentence
            socketio.emit('response_stream', {'text': accumulated_text, 'is_final': False}, namespace='/medical')
            print(f"[MEDICAL] Adding sentence to TTS queue: '{sentence}'")
            medical_tts_queue.put((token, sentence))
            socketio.sleep(0.3)
        if token == medical_token:
            socketio.emit('response_stream', {'text': accumulated_text, 'is_final': True}, namespace='/medical')
    except Exception as e:
        print(f"[MEDICAL] Error in stream_response: {str(e)}")
        socketio.emit('error_message', {'message': f'Error generating medical response: {str(e)}'}, namespace='/medical')
    finally:
        if token == medical_token:
            socketio.emit('thinking_status', {'status': False}, namespace='/medical')

# -------------------- Government Assistant Setup --------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCliqGdNtcYJY0f638LOfext7L-Hy4kxXw")  # Replace with your actual Gemini API key
GEMINI_MODEL = "gemini-1.5-pro"
genai.configure(api_key=GEMINI_API_KEY)
government_token = 0
government_tts_queue = queue.Queue()

def get_grievance_response(user_input):
    system_prompt = '''You are an empathetic and professional Grievance Filing Assistant. Please guide the user through the grievance filing process based on the following details.'''
    
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        chat = model.start_chat(history=[])
        response = chat.send_message(f"{system_prompt}\n\nUser input: {user_input}")
        return response.text  # Return the response text
    except Exception as e:
        print(f"Error with Government Assistant API: {str(e)}")
        return f"Error: Unable to fetch response. {str(e)}"

def stream_response_government(user_input, token):
    global government_token
    if token != government_token:
        return
    socketio.emit('thinking_status', {'status': True}, namespace='/government')
    
    try:
        full_response = get_grievance_response(user_input)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', full_response) if s.strip()]
        print(f"[GOVERNMENT] Processing response with {len(sentences)} sentences")
        
        accumulated_text = ""
        for sentence in sentences:
            if token != government_token:
                print("[GOVERNMENT] Token changed, stopping response streaming")
                break
            accumulated_text += (" " if accumulated_text else "") + sentence
            socketio.emit('response_stream', {'text': accumulated_text, 'is_final': False}, namespace='/government')
            print(f"[GOVERNMENT] Adding sentence to TTS queue: '{sentence}'")
            government_tts_queue.put((token, sentence))
            socketio.sleep(0.3)

        if token == government_token:
            socketio.emit('response_stream', {'text': accumulated_text, 'is_final': True}, namespace='/government')

    except Exception as e:
        print(f"[GOVERNMENT] Error in stream_response: {str(e)}")
        socketio.emit('error_message', {'message': f'Error generating response: {str(e)}'}, namespace='/government')
    finally:
        if token == government_token:
            socketio.emit('thinking_status', {'status': False}, namespace='/government')

# -------------------- Routes --------------------
@app.route('/services/legal.html')
def serve_legal():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(current_dir, "legal.html")

@app.route('/services/medical.html')
def serve_medical():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(current_dir, "medical.html")

@app.route('/services/government.html')
def serve_government():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(current_dir, "government.html")
# -------------------- Emergency Assistant Route --------------------
@app.route('/services/emergency.html')
def serve_emergency():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(current_dir, "emergency.html")


# -------------------- Socket.IO Legal Namespace --------------------
@socketio.on('send_message', namespace='/legal')
def handle_legal_message(data):
    global legal_token
    user_input = data['message'].strip()
    if not user_input:
        return
    try:
        detected_lang = detect(user_input)
        print(f"[LEGAL] Detected language: {detected_lang}")
    except LangDetectException:
        detected_lang = "en"
        print("[LEGAL] Could not detect language, defaulting to 'en'")

    print(f"[LEGAL] Received new message: '{user_input}'")
    legal_token += 1
    with legal_tts_queue.mutex:
        legal_tts_queue.queue.clear()
    socketio.emit('stop_audio', namespace='/legal')
    
    thread = threading.Thread(target=stream_response_legal, args=(user_input, legal_token, detected_lang))
    thread.daemon = True
    thread.start()

@socketio.on('start_voice_input', namespace='/legal')
def handle_legal_voice_input():
    thread = threading.Thread(target=recognize_speech, args=('/legal', stream_response_legal))
    thread.daemon = True
    thread.start()

# -------------------- Socket.IO Medical Namespace --------------------
@socketio.on('send_message', namespace='/medical')
def handle_medical_message(data):
    global medical_token
    user_input = data['message'].strip()
    if not user_input:
        return
    try:
        detected_lang = detect(user_input)
        print(f"[MEDICAL] Detected language: {detected_lang}")
    except LangDetectException:
        detected_lang = "en"
        print("[MEDICAL] Could not detect language, defaulting to 'en'")

    print(f"[MEDICAL] Received new message: '{user_input}'")
    medical_token += 1
    with medical_tts_queue.mutex:
        medical_tts_queue.queue.clear()
    socketio.emit('stop_audio', namespace='/medical')
    
    thread = threading.Thread(target=stream_response_medical, args=(user_input, medical_token, detected_lang))
    thread.daemon = True
    thread.start()

@socketio.on('start_voice_input', namespace='/medical')
def handle_medical_voice_input():
    thread = threading.Thread(target=recognize_speech, args=('/medical', stream_response_medical))
    thread.daemon = True
    thread.start()

# -------------------- Socket.IO Government Namespace --------------------
@socketio.on('send_message', namespace='/government')
def handle_government_message(data):
    global government_token
    user_input = data['message'].strip()
    if not user_input:
        return
    try:
        detected_lang = detect(user_input)
        print(f"[GOVERNMENT] Detected language: {detected_lang}")
    except LangDetectException:
        detected_lang = "en"
        print("[GOVERNMENT] Could not detect language, defaulting to 'en'")

    print(f"[GOVERNMENT] Received new message: '{user_input}'")
    government_token += 1
    with government_tts_queue.mutex:
        government_tts_queue.queue.clear()
    socketio.emit('stop_audio', namespace='/government')
    
    thread = threading.Thread(target=stream_response_government, args=(user_input, government_token))
    thread.daemon = True
    thread.start()

# -------------------- Main --------------------
@app.route('/')
def index():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return send_from_directory(base_dir, "index.html")

if __name__ == '__main__':
    print("Starting Combined Assistant Web App...")
    socketio.run(app, debug=True, port=5005)
