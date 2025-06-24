import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from processing.tumor_detector import TumorDetector
from processing.image_processor import generate_visualizations
from flask import jsonify, send_file

app = Flask(__name__)

# Configuración
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'dcm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# Crear directorios si no existen
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Procesamiento de la imagen
            detector = TumorDetector()
            result = detector.detect_tumor(filepath)
            
            # Generar visualizaciones
            base_name = os.path.splitext(filename)[0]
            result_images = generate_visualizations(
                filepath, 
                app.config['RESULT_FOLDER'], 
                base_name
            )
            
            return render_template('index.html',
                                original_image=filepath,
                                result_images=result_images,
                                has_tumor=result['has_tumor'],
                                confidence=f"{result['confidence']:.2f}%")
    
    return render_template('index.html')

@app.route('/api/detect', methods=['POST'])
def api_detect():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Procesamiento
    detector = TumorDetector()
    result = detector.detect_tumor(filepath)

    # Visualización
    base_name = os.path.splitext(filename)[0]
    result_images = generate_visualizations(filepath, app.config['RESULT_FOLDER'], base_name)

    result_image_url = request.host_url + result_images[0]  # Ruta absoluta para usar en Telegram

    return jsonify({
        'has_tumor': result['has_tumor'],
        'confidence': f"{result['confidence']:.2f}%",
        'image_url': result_image_url
    })


if __name__ == '__main__':
    app.run(debug=True)
