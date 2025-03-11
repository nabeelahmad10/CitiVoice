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

app = Flask(__name__)
socketio = SocketIO(app)

# -------------------- Legal Assistant Setup --------------------
LEGAL_API_KEY = "qCrx2JAOa9tDelNuVPhSusV5Fogl1NEL"
LEGAL_MODEL = "mistral-medium"
LEGAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
legal_token = 0
legal_tts_queue = queue.Queue()

def get_legal_response(user_input):
    headers = {
        "Authorization": f"Bearer {LEGAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": LEGAL_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI legal assistant. Provide clear and concise legal information. "
                    "Begin by summarizing the legal issue, then outline relevant statutes or guidelines dont mention summarise in response "
                    "in simple language. Include a disclaimer stating that this is not legal advice "
                    "and that users should consult a qualified attorney for personalized counsel."
                )
            },
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

def stream_response_legal(user_input, token):
    global legal_token
    if token != legal_token:
        return
    socketio.emit('thinking_status', {'status': True}, namespace='/legal')
    try:
        full_response = get_legal_response(user_input)
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
# (Using the same API key, model, and endpoint here as an example; adjust if needed.)
def get_medical_response(user_input):
    headers = {
        "Authorization": f"Bearer {LEGAL_API_KEY}",  # using same key for demo purposes
        "Content-Type": "application/json"
    }
    data = {
        "model": LEGAL_MODEL,
        "messages": [
            {"role": "system", "content": (
                "You are an AI medical assistant. Provide your response in clear, short sentences separated by periods. "
                "First tell the user what you're going to explain, then provide the information. If symptoms are mentioned, "
                "suggest possible conditions and first-aid remedies. Recommend only OTC medicines. If symptoms are severe, suggest consulting a doctor."
            )},
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

def stream_response_medical(user_input, token):
    global medical_token
    if token != medical_token:
        return
    socketio.emit('thinking_status', {'status': True}, namespace='/medical')
    try:
        full_response = get_medical_response(user_input)
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

# -------------------- Common TTS and Speech Functions --------------------
def text_to_speech(text, namespace):
    try:
        if not text or len(text.strip()) < 2:
            print("Empty text received, skipping TTS")
            return
        print(f"Converting to speech: '{text}'")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_filename = temp_file.name
            print(f"Temp file created: {temp_filename}")
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(temp_filename)
        print("Audio saved to temp file")
        time.sleep(0.2)
        with open(temp_filename, 'rb') as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
            print(f"Audio file read, size: {len(audio_data)} chars")
        try:
            os.unlink(temp_filename)
            print("Temp file deleted")
        except Exception as e:
            print(f"Warning: Could not delete temp file: {str(e)}")
        print("Sending audio data to client")
        socketio.emit('play_audio', {'audio_data': audio_data}, namespace=namespace)
        print("Audio data sent")
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        socketio.emit('error_message', {'message': f'Error generating speech: {str(e)}'}, namespace=namespace)

def tts_worker(queue_obj, token_getter, namespace):
    print(f"TTS worker thread for {namespace} started")
    while True:
        try:
            token, text = queue_obj.get()
            if token != token_getter():
                queue_obj.task_done()
                continue
            text_to_speech(text, namespace)
            queue_obj.task_done()
        except Exception as e:
            print(f"Error in TTS worker ({namespace}): {str(e)}")
            try:
                queue_obj.task_done()
            except:
                pass

def recognize_speech(namespace, stream_func):
    # stream_func should be the function to stream responses for the given domain.
    recognizer = sr.Recognizer()
    try:
        print(f"Starting speech recognition for {namespace}")
        socketio.emit('listening_status', {'status': True}, namespace=namespace)
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
        socketio.emit('listening_status', {'status': False}, namespace=namespace)
        user_input = recognizer.recognize_google(audio)
        print(f"Speech recognized for {namespace}: '{user_input}'")
        socketio.emit('speech_recognized', {'text': user_input}, namespace=namespace)
        # Cancel previous processing before starting a new one
        if namespace == '/legal':
            global legal_token
            legal_token += 1
            token = legal_token
        else:
            global medical_token
            medical_token += 1
            token = medical_token
        # Clear corresponding TTS queue
        if namespace == '/legal':
            with legal_tts_queue.mutex:
                legal_tts_queue.queue.clear()
        else:
            with medical_tts_queue.mutex:
                medical_tts_queue.queue.clear()
        socketio.emit('stop_audio', namespace=namespace)
        thread = threading.Thread(target=stream_func, args=(user_input, token))
        thread.daemon = True
        thread.start()
    except sr.WaitTimeoutError:
        print(f"Speech recognition error for {namespace}: No speech detected within the allotted time.")
        socketio.emit('error_message', {'message': "No speech detected. Please tap the speak button and try again."}, namespace=namespace)
    except sr.UnknownValueError:
        print(f"Speech recognition could not understand audio for {namespace}")
        socketio.emit('error_message', {'message': "Sorry, I couldn't understand. Please try again."}, namespace=namespace)
    except sr.RequestError as e:
        print(f"Speech recognition service error for {namespace}: {e}")
        socketio.emit('error_message', {'message': f"Error in speech recognition service: {str(e)}"}, namespace=namespace)
    except Exception as e:
        print(f"Speech recognition error for {namespace}: {e}")
        import traceback
        traceback.print_exc()
        socketio.emit('error_message', {'message': f"An error occurred during speech recognition: {str(e)}"}, namespace=namespace)

# -------------------- Routes --------------------
# Serve index.html from the project root
@app.route('/')
def index():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return send_from_directory(base_dir, "index.html")

# Serve legal.html from the services folder
@app.route('/services/legal.html')
def serve_legal():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(current_dir, "legal.html")

# Serve medical.html from the services folder
@app.route('/services/medical.html')
def serve_medical():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(current_dir, "medical.html")

# -------------------- Socket.IO Legal Namespace --------------------
@socketio.on('send_message', namespace='/legal')
def handle_legal_message(data):
    global legal_token
    user_input = data['message'].strip()
    if not user_input:
        return
    print(f"[LEGAL] Received new message: '{user_input}'")
    legal_token += 1
    with legal_tts_queue.mutex:
        legal_tts_queue.queue.clear()
    socketio.emit('stop_audio', namespace='/legal')
    thread = threading.Thread(target=stream_response_legal, args=(user_input, legal_token))
    thread.daemon = True
    thread.start()

@socketio.on('start_voice_input', namespace='/legal')
def handle_legal_voice_input():
    thread = threading.Thread(target=recognize_speech, args=('/legal', stream_response_legal))
    thread.daemon = True
    thread.start()

@socketio.on('connect', namespace='/legal')
def legal_connect():
    print("[LEGAL] Client connected")

@socketio.on('disconnect', namespace='/legal')
def legal_disconnect():
    print("[LEGAL] Client disconnected")

# -------------------- Socket.IO Medical Namespace --------------------
@socketio.on('send_message', namespace='/medical')
def handle_medical_message(data):
    global medical_token
    user_input = data['message'].strip()
    if not user_input:
        return
    print(f"[MEDICAL] Received new message: '{user_input}'")
    medical_token += 1
    with medical_tts_queue.mutex:
        medical_tts_queue.queue.clear()
    socketio.emit('stop_audio', namespace='/medical')
    thread = threading.Thread(target=stream_response_medical, args=(user_input, medical_token))
    thread.daemon = True
    thread.start()

@socketio.on('start_voice_input', namespace='/medical')
def handle_medical_voice_input():
    thread = threading.Thread(target=recognize_speech, args=('/medical', stream_response_medical))
    thread.daemon = True
    thread.start()

@socketio.on('connect', namespace='/medical')
def medical_connect():
    print("[MEDICAL] Client connected")

@socketio.on('disconnect', namespace='/medical')
def medical_disconnect():
    print("[MEDICAL] Client disconnected")

# -------------------- Start TTS Workers --------------------
legal_tts_thread = threading.Thread(target=tts_worker, args=(legal_tts_queue, lambda: legal_token, '/legal'))
legal_tts_thread.daemon = True
legal_tts_thread.start()

medical_tts_thread = threading.Thread(target=tts_worker, args=(medical_tts_queue, lambda: medical_token, '/medical'))
medical_tts_thread.daemon = True
medical_tts_thread.start()

# -------------------- Main --------------------
if __name__ == '__main__':
    print("Starting Combined Assistant Web App...")
    print("Legal Assistant: http://127.0.0.1:5000/services/legal.html")
    print("Medical Assistant: http://127.0.0.1:5000/services/medical.html")
    socketio.run(app, debug=True, port=5005)
