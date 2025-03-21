from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
from flask_cors import CORS
import os
import tempfile
from pydub import AudioSegment
import speech_recognition as sr

app = Flask(__name__, static_folder=None)
CORS(app)

db = {
    "rutina": [],
    "proyectos": [],
    "pendientes": {
        "personal": [],
        "casa": [],
        "trabajo": []
    }
}

@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    try:
        # Save incoming audio
        audio_file = request.files['audio']
        _, temp_path = tempfile.mkstemp(suffix='.webm')
        audio_file.save(temp_path)
        # Convert to WAV format
        wav_path = temp_path + '.wav'
        audio = AudioSegment.from_file(temp_path)
        audio.export(wav_path, format='wav')
        # Recognize speech
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language='es-MX')
        # Cleanup
        os.remove(temp_path)
        os.remove(wav_path)
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": "Checa los permisos del navegador y si el micrófono en tu dispositivo está funcionando correctamente. No se logró obtener el audio de tu voz."}), 500

# ========== RUTINAS ==========
@app.route('/api/rutina', methods=['GET', 'POST'])
def manejar_rutina():
    if request.method == 'GET':
        return jsonify(db['rutina'])
    elif request.method == 'POST':
        nueva = request.json
        nueva['id'] = len(db['rutina']) + 1
        db['rutina'].append(nueva)
        return jsonify(nueva), 201

@app.route('/api/rutina/<int:id>', methods=['PUT', 'DELETE'])
def rutina_item(id):
    item = next((i for i in db['rutina'] if i['id'] == id), None)
    if not item:
        return jsonify({"error": "Actividad no encontrada"}), 404
    
    if request.method == 'PUT':
        data = request.json
        item.update(data)
        return jsonify(item)
    elif request.method == 'DELETE':
        db['rutina'].remove(item)
        return jsonify({"status": "deleted"})

# ========== PROYECTOS ==========
@app.route('/api/proyectos', methods=['GET', 'POST'])
def manejar_proyectos():
    if request.method == 'GET':
        return jsonify(db['proyectos'])
    elif request.method == 'POST':
        nuevo = request.json
        nuevo['id'] = len(db['proyectos']) + 1
        nuevo['creado'] = datetime.now().isoformat()
        db['proyectos'].append(nuevo)
        return jsonify(nuevo), 201

@app.route('/api/proyectos/<int:id>', methods=['PUT', 'DELETE'])
def proyectos_item(id):
    proyecto = next((p for p in db['proyectos'] if p['id'] == id), None)
    if not proyecto:
        return jsonify({"error": "Proyecto no encontrado"}), 404
    
    if request.method == 'PUT':
        data = request.json
        proyecto.update(data)
        proyecto['modificado'] = datetime.now().isoformat()
        return jsonify(proyecto)
    elif request.method == 'DELETE':
        db['proyectos'].remove(proyecto)
        return jsonify({"status": "deleted"})

# ========== PENDIENTES ==========
@app.route('/api/pendientes', methods=['GET', 'POST'])
def manejar_pendientes():
    categoria = request.args.get('categoria', 'personal')
    
    if request.method == 'GET':
        return jsonify(db['pendientes'].get(categoria, []))
    
    elif request.method == 'POST':
        nueva = request.json
        nueva['id'] = len(db['pendientes'][categoria]) + 1
        nueva['completada'] = False
        db['pendientes'][categoria].append(nueva)
        return jsonify(nueva), 201

@app.route('/api/pendientes/<categoria>/<int:id>', methods=['PUT', 'DELETE'])
def pendientes_item(categoria, id):
    if categoria not in db['pendientes']:
        return jsonify({"error": "Categoría inválida"}), 400
    
    tarea = next((t for t in db['pendientes'][categoria] if t['id'] == id), None)
    if not tarea:
        return jsonify({"error": "Tarea no encontrada"}), 404
    
    if request.method == 'PUT':
        data = request.json
        tarea.update(data)
        return jsonify(tarea)
    elif request.method == 'DELETE':
        db['pendientes'][categoria].remove(tarea)
        return jsonify({"status": "deleted"})

# Resto de endpoints estáticos
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index_gemini.test.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)