# CitiVoice - A 24/7 Citizen Helpline

CitiVoice is a dynamic platform that connects citizens with vital support services around the clock. Whether you need medical assistance, legal advice, government services, emergency help, or a legal/medical document reader and summarizer, CitiVoice provides a simple and intuitive interface to access all the support you need.

## Important Files

Only these files are essential for running the application:

- `combined.py`
- `legal.html`
- `index.html`
- `government.html`
- `medical.html`
- `emergency.html`
- `solutionprovider.html`

> **Note:** Please do not delete any other files, as it might trigger errors.

## Setup Instructions

### 1. Create and Activate the Virtual Environment

Open your terminal, navigate to your project directory, and run:

```bash
# Create the virtual environment:
python -m venv env

# Activate the virtual environment:
Windows:
env\Scripts\activate

macOS/Linux:
source env/bin/activate
```
### 2. Install Dependencies

Install all required dependencies using pip. You can either refer to the `requirements.txt` file or run the following command:


```bash
pip install requests SpeechRecognition Flask flask-socketio pdf2image pytesseract Pillow PyMuPDF langdetect google-generativeai gTTS
```
### 3. Run the Application

### MIT License

Copyright (c) 2025 CitiVoice

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


1. Open the `combined.py` file in your preferred code editor.
2. Run the file to start the server.
3. Open your web browser and navigate to [http://127.0.0.1:5005](http://127.0.0.1:5005) to access the main website.
4. From the main website, you can navigate to the medical, problem solver, government, emergency, and legal sections to interact and use the services.

