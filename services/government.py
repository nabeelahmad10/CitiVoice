from flask import Flask, render_template, send_from_directory
import os
import queue
import threading
import re
import google.generativeai as genai
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

# Gemini API Configuration
GEMINI_API_KEY = "AIzaSyCliqGdNtcYJY0f638LOfext7L-Hy4kxXw"  # Replace with your actual Gemini API key
GEMINI_MODEL = "gemini-1.5-pro"  # Adjust according to available models

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Queue for speech processing; items will be tuples of (token, sentence)
tts_queue = queue.Queue()

# Global token to keep track of the current response
current_token = 0

# -------------------- Government Assistant Setup --------------------
def get_grievance_response(user_input):
    system_prompt = '''You are an empathetic and professional Grievance Filing Assistant. Your purpose is to help users document their grievances accurately and thoroughly for official filing.

Follow these guidelines when processing grievance reports:

1. INFORMATION COLLECTION:
   - Identify the nature of the grievance (workplace, consumer, healthcare, housing, etc.)
   - Gather essential details: who, what, when, where, why, and how
   - Determine if there were any witnesses or supporting evidence
   - Note any prior attempts to resolve the issue

2. REPORT STRUCTURE:
   - Begin with a clear summary of the incident/issue
   - Include chronological details with specific dates and times
   - Document names and titles of all relevant parties
   - Note any applicable policies, regulations, or laws that were violated
   - Detail the impact (emotional, financial, physical, etc.) on the complainant
   - Include any attempted resolutions and their outcomes
   - End with the complainant's desired resolution

3. TONE AND APPROACH:
   - Maintain a professional, factual tone
   - Be empathetic while remaining objective
   - Use clear, specific language without emotional qualifiers
   - Avoid making legal determinations or promising specific outcomes
   - Highlight key facts that support the grievance claim

4. NEXT STEPS:
   - Suggest documentation or evidence the user should gather
   - Explain the typical timeline for processing similar grievances
   - Outline what to expect in the grievance process
   - Recommend appropriate follow-up actions

If the user doesn't provide enough information, ask follow-up questions to ensure the report is complete. Focus especially on specific details, dates, locations, and the names/positions of people involved.

Present the final grievance report in a structured format that would be suitable for official submission, while suggesting any additional information that might strengthen their case.'''

    try:
        # Initialize the Gemini model
        model = genai.GenerativeModel(GEMINI_MODEL)

        # Create a chat session
        chat = model.start_chat(history=[])

        # Send the system prompt and user input to the model
        response = chat.send_message(f"{system_prompt}\n\nUser input: {user_input}")

        return response.text
    except Exception as e:
        return f"Error: Unable to fetch response. {str(e)}"


def stream_response(user_input, token):
    global current_token
    if token != current_token:
        return  # Exit if this response is no longer current

    socketio.emit('thinking_status', {'status': True})

    try:
        full_response = get_grievance_response(user_input)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', full_response) if s.strip()]

        print(f"Processing response with {len(sentences)} sentences")

        accumulated_text = ""
        for sentence in sentences:
            if token != current_token:
                print("Token changed, stopping response streaming")
                break  # Stop processing if token has changed

            accumulated_text += (" " if accumulated_text else "") + sentence
            socketio.emit('response_stream', {'text': accumulated_text, 'is_final': False})

            print(f"Adding sentence to TTS queue: '{sentence}'")
            tts_queue.put((token, sentence))

            socketio.sleep(0.3)  # Reduced delay for quicker response

        if token == current_token:
            socketio.emit('response_stream', {'text': accumulated_text, 'is_final': True})

    except Exception as e:
        print(f"Error in stream_response: {str(e)}")
        socketio.emit('error_message', {'message': f'Error generating response: {str(e)}'})
    finally:
        if token == current_token:
            socketio.emit('thinking_status', {'status': False})


# -------------------- Routes --------------------
@app.route('/services/government.html')
def serve_government():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    return send_from_directory(current_dir, "government.html")


# -------------------- Socket.IO Government Namespace --------------------
@socketio.on('send_message', namespace='/government')
def handle_government_message(data):
    global current_token, tts_queue
    user_input = data['message'].strip()
    if not user_input:
        return
    print(f"[GOVERNMENT] Received new message: '{user_input}'")
    
    current_token += 1
    with tts_queue.mutex:
        queue_size = len(tts_queue.queue)
        tts_queue.queue.clear()
        print(f"Cleared TTS queue ({queue_size} items removed)")

    # Notify client to stop audio immediately
    socketio.emit('stop_audio')
    print("Sent stop_audio signal to client")

    # Start a new processing thread
    thread = threading.Thread(target=stream_response, args=(user_input, current_token))
    thread.daemon = True
    thread.start()


@socketio.on('start_voice_input', namespace='/government')
def handle_government_voice_input():
    print("[GOVERNMENT] Starting voice input")
    thread = threading.Thread(target=recognize_speech)
    thread.daemon = True
    thread.start()


# -------------------- Main --------------------
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    print("Starting Combined Assistant Web App...")
    socketio.run(app, debug=True, port=5005)
