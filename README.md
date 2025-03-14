# About CitiVoice

CitiVoice is a dynamic, multi-service platform that connects citizens with vital support areas around the clock. Whether you need medical assistance, legal advice, government services, emergency help, or a legal/medical document-reader and summariser, CitiVoice provides a user-friendly interface to get you all the support you need.

HOW TO RUN:

NOTE: ONLY THESE FILES ARE IMPORTANT AND RESPONSIBLE FOR RUNNING -: COMBINED.PY, LEGAL.HTML, INDEX.HTML, GOVERNMENT.HTML, MEDICAL.HTML, EMERGENCY.HTML, SOLUTIONPROVIDER.HTML
(BUT DONT DELETE OTHER FILES PLEASE AS IT MIGHT TRIGGER SOME ERROR)

OPEN YOUR TERMINAL
CREATE THE VIRTUAL ENV FOR PYTHON:
1) python -m venv env
2) env\Scripts\activate

KEEP THE TERMINAL OPEN,

NOW INSTALL ALL THE DEPENDENCIES USING PIP INSTALL, YOU CAN FIND IT IN REQUIREMENTS.TXT OR JUST PASTE THIS LINE IN YOUR TERMINAL:
1) pip install requests SpeechRecognition Flask flask-socketio pdf2image pytesseract Pillow PyMuPDF langdetect google-generativeai gTTS

OPEN THE COMBINED.PY FILE AND RUN IT. ONCE ITS RUNNING OPEN THE  http://127.0.0.1:5005 SERVER AND IT WILL SHOW THE MAIN WEBSITE.
 YOU CAN NAVIGATE THROUGH TO THE MEDICAL, PROBLEM SOLVER, GOVERNMENT EMERGENCY AND LEGAL AREA AND USE THE CHATBOT IT WILL RUN PERFECTLY
