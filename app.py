from flask import Flask, render_template, request, jsonify,  \
    send_from_directory, session, send_file, redirect, url_for
import os
import subprocess
import shutil
import os
import zipfile
from PIL import Image

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/compress-image', methods=['POST'])
def compress_image():
    # Создаем уникальную папку для каждого пользователя
    identifier = request.form.get('identifier')
    width_value = request.form.get('width_value') or 1000
    quality = request.form.get('quality') or 80
    save_format = request.form.get('save_format') or 'jpeg'

    user_folder = os.path.join('uploads/', identifier)
    os.makedirs(user_folder, exist_ok=True)

    if 'files' not in request.files:
        return jsonify({'status': 'error', 'message': 'No files uploaded'}), 400

    files = request.files.getlist('files')
    
    # Сохраняем загруженные файлы
    for file in files:
        file_path = os.path.join(user_folder, file.filename)
        original_extension = os.path.splitext(file_path)[1].lower().replace('.', '')
        file.save(file_path)

        print(file_path, original_extension)
        
        if original_extension == 'png' and save_format == 'jpeg':
            print('rgba convert')
            with Image.open(file_path) as img:
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(file_path, format=original_extension)


    params = {
        '-l': user_folder,
        '-d': user_folder + '/success',
        '-f': save_format,
        '-w': width_value,
        '-q': quality,
    }

    # Формируем параметры для команды
    param_str = ' '.join([f"{key} {value}" for key, value in params.items()])
    cmd_command = f'py-bulk-image-compressor {param_str}'

    try:
        # Выполняем команду
        result = subprocess.run(cmd_command, shell=True, capture_output=True, text=True, check=True)

        # Получаем список сжатых изображений
        compressed_images = []
        for img in os.listdir(user_folder + '/success'):
            if img.endswith(save_format):
                img_path = os.path.join(user_folder + '/success', img)
                img_size = os.path.getsize(img_path) / 1024  # Размер в КБ
                compressed_images.append({'filename': img, 'size': round(img_size, 2)})

        return jsonify({'status': 'success', 'output': result.stdout, 'images': compressed_images}), 200
    
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'output': e.stderr}), 500

@app.route('/<path:identifier>/<path:filename>')
def send_image(identifier, filename):
    return send_from_directory(f'uploads/{identifier}/success/', filename)

@app.route('/download-zip/<path:identifier>')
def download_zip(identifier):
    if identifier:
        user_folder = os.path.join(f'uploads/{identifier}/','success')
        zip_filename = f'images_{identifier}.zip'
        zip_filepath = os.path.join(f'uploads/{identifier}/', zip_filename)

        # Создаем ZIP-архив
        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            for root, _, files in os.walk(user_folder):
                for file in files:
                    if file == zip_filename:
                        continue
                    zipf.write(os.path.join(root, file), file)

        return send_file(zip_filepath, as_attachment=True)
    
@app.route('/cleanup/<path:identifier>', methods=['POST'])
def cleanup(identifier):
    if identifier:
        user_folder = os.path.join('uploads/', identifier)
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder)
    return jsonify({}), 200

@app.route('/<path:invalid_path>')
def redirect_wrong_url(invalid_path):
    return redirect(url_for('home'))


# if __name__ == '__main__':
#     app.run(debug=True)
