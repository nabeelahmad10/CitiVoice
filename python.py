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

# Mistral API Configuration
MISTRAL_API_KEY = "qCrx2JAOa9tDelNuVPhSusV5Fogl1NEL"
MISTRAL_MODEL = "mistral-medium"
MISTRAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"

# Queue for TTS processing; items will be tuples of (token, sentence)
tts_queue = queue.Queue()

# Global token to keep track of the current response
current_token = 0

# -----------------------------
# Mistral API call and streaming
# -----------------------------
def get_medical_response(user_input):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": "You are an AI medical assistant. Provide your response in clear, short sentences separated by periods. First tell the user what you're going to explain, then provide the information. If symptoms are mentioned, suggest possible conditions and first-aid remedies. Recommend only OTC (over-the-counter) medicines. If symptoms are severe, suggest consulting a doctor."},
            {"role": "user", "content": user_input}
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }
    try:
        response = requests.post(MISTRAL_ENDPOINT, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error: Unable to fetch response. {str(e)}"

def stream_response(user_input, token):
    global current_token
    if token != current_token:
        return  # Exit if this response is no longer current

    socketio.emit('thinking_status', {'status': True})
    try:
        full_response = get_medical_response(user_input)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', full_response) if s.strip()]
        print(f"Processing response with {len(sentences)} sentences")
        accumulated_text = ""
        for sentence in sentences:
            if token != current_token:
                print("Token changed, stopping response streaming")
                break
            accumulated_text += (" " if accumulated_text else "") + sentence
            socketio.emit('response_stream', {'text': accumulated_text, 'is_final': False})
            print(f"Adding sentence to TTS queue: '{sentence}'")
            tts_queue.put((token, sentence))
            socketio.sleep(0.3)
        if token == current_token:
            socketio.emit('response_stream', {'text': accumulated_text, 'is_final': True})
    except Exception as e:
        print(f"Error in stream_response: {str(e)}")
        socketio.emit('error_message', {'message': f'Error generating response: {str(e)}'})
    finally:
        if token == current_token:
            socketio.emit('thinking_status', {'status': False})

# -----------------------------
# Speech Recognition & TTS
# -----------------------------
def recognize_speech():
    global current_token, tts_queue
    recognizer = sr.Recognizer()
    try:
        print("Starting speech recognition")
        socketio.emit('listening_status', {'status': True})
        with sr.Microphone() as source:
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening for speech (waiting up to 10 sec)...")
            # Wait for speech for up to 10 seconds
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
            print("Audio captured")
        socketio.emit('listening_status', {'status': False})
        print("Recognizing speech...")
        user_input = recognizer.recognize_google(audio)
        print(f"Speech recognized: '{user_input}'")
        socketio.emit('speech_recognized', {'text': user_input})
        # Cancel previous processing before starting a new one
        current_token += 1
        print(f"Cancelling previous processing, new token: {current_token}")
        with tts_queue.mutex:
            queue_size = len(tts_queue.queue)
            tts_queue.queue.clear()
            print(f"Cleared TTS queue ({queue_size} items removed)")
        socketio.emit('stop_audio')
        print("Sent stop_audio signal to client")
        # Start response streaming for speech input
        thread = threading.Thread(target=stream_response, args=(user_input, current_token))
        thread.daemon = True
        thread.start()
    except sr.WaitTimeoutError:
        print("Speech recognition error: No speech detected within the allotted time.")
        socketio.emit('error_message', {'message': "No speech detected. Please tap the speak button and speak again."})
    except sr.UnknownValueError:
        print("Speech recognition could not understand audio")
        socketio.emit('error_message', {'message': "Sorry, I couldn't understand. Please try again."})
    except sr.RequestError as e:
        print(f"Speech recognition service error: {e}")
        socketio.emit('error_message', {'message': f"Error in speech recognition service: {str(e)}"})
    except Exception as e:
        print(f"Speech recognition error: {e}")
        import traceback
        traceback.print_exc()
        socketio.emit('error_message', {'message': f"An error occurred during speech recognition: {str(e)}"})

def text_to_speech(text):
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
        socketio.emit('play_audio', {'audio_data': audio_data})
        print("Audio data sent")
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        socketio.emit('error_message', {'message': f'Error generating speech: {str(e)}'})

def tts_worker():
    global current_token
    print("TTS worker thread started")
    while True:
        try:
            print("Waiting for sentence in TTS queue...")
            token, text = tts_queue.get()
            print(f"Got sentence from queue (token {token}): '{text}'")
            if token != current_token:
                print(f"Skipping TTS for outdated token {token} (current token is {current_token})")
                tts_queue.task_done()
                continue
            text_to_speech(text)
            tts_queue.task_done()
        except Exception as e:
            print(f"Error in TTS worker: {str(e)}")
            try:
                tts_queue.task_done()
            except:
                pass

# Start TTS worker thread
print("Starting TTS worker thread")
tts_thread = threading.Thread(target=tts_worker)
tts_thread.daemon = True
tts_thread.start()

# -----------------------------
# Flask Routes and SocketIO Events
# -----------------------------
@app.route('/')
def index():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(current_dir, "medical.html")

# RESTful endpoint to support text chat via fetch
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"response": "Please ask a medical question."})
    response_text = get_medical_response(user_message)
    return jsonify({"response": response_text})

@app.route('/test_tts')
def test_tts():
    print("Testing TTS functionality")
    text_to_speech("This is a test of the text to speech system.")
    return "Testing TTS functionality. Check console for logs."

@app.route('/test_mic')
def test_mic():
    print("Testing microphone setup")
    try:
        mic_list = sr.Microphone.list_microphone_names()
        return jsonify({
            'status': 'success',
            'microphones': mic_list,
            'count': len(mic_list)
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': error_trace
        })

@socketio.on('send_message')
def handle_message(data):
    global current_token, tts_queue
    user_input = data['message'].strip()
    if not user_input:
        return
    print(f"Received new message: '{user_input}'")
    current_token += 1
    print(f"Cancelling previous processing, new token: {current_token}")
    with tts_queue.mutex:
        queue_size = len(tts_queue.queue)
        tts_queue.queue.clear()
        print(f"Cleared TTS queue ({queue_size} items removed)")
    socketio.emit('stop_audio')
    print("Sent stop_audio signal to client")
    thread = threading.Thread(target=stream_response, args=(user_input, current_token))
    thread.daemon = True
    thread.start()

@socketio.on('start_voice_input')
def handle_voice_input():
    print("Starting voice input via socket")
    thread = threading.Thread(target=recognize_speech)
    thread.daemon = True
    thread.start()

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == '__main__':
    print("Starting Medical Assistant Web App...")
    print("Open your browser and go to http://127.0.0.1:3000")
    socketio.run(app, debug=True, port=3000)
