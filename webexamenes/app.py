from flask import Flask, request, jsonify , send_from_directory
from werkzeug.utils import secure_filename
import os
import requests  # <-- Cambiamos OpenAI por requests
import PyPDF2
from docx import Document

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
DEEPSEEK_API_KEY = "TU_API_KEY_DE_DEEPSEEK"  # <-- Reemplaza con tu clave

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

# Función para extraer texto (igual que antes)
def extract_text(file_path, filename):
    if filename.endswith('.pdf'):
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = " ".join([page.extract_text() for page in reader.pages])
    elif filename.endswith('.docx'):
        doc = Document(file_path)
        text = " ".join([para.text for para in doc.paragraphs])
    else:
        text = ""
    return text

# Función para generar preguntas con DeepSeek
def generate_questions(text):
    prompt = f"""
    Genera 5 preguntas de verdadero o falso basadas en este texto. 
    Formato JSON requerido:
    {{
        "questions": [
            {{ "question": "pregunta", "answer": true/false }},
            ...
        ]
    }}
    Texto: {text}
    """
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "model": "deepseek-chat"  # Asegúrate de usar el modelo correcto
    }
    
    response = requests.post(
        "https://api.deepseek.com/v1/chat/completions",  # Endpoint de DeepSeek
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.text}"

# Ruta para subir documentos (igual que antes)
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    text = extract_text(file_path, filename)
    questions_json = generate_questions(text)
    
    return jsonify(questions_json)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)