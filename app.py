from flask import Flask, request, redirect, render_template, send_from_directory
import os

app = Flask(__name__)

PHOTOS_DIR = '/home/piter/repo/pogoda/images'
ALLOWED = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

def allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED

@app.route('/')
def index():
    files = sorted(os.listdir(PHOTOS_DIR))
    photos = [f for f in files if allowed(f)]
    return render_template('index.html', photos=photos)

@app.route('/upload', methods=['POST'])
def upload():
    for file in request.files.getlist('photos'):
        if file and allowed(file.filename):
            file.save(os.path.join(PHOTOS_DIR, file.filename))
    return redirect('/')

@app.route('/photos/<filename>')
def photo(filename):
    return send_from_directory(PHOTOS_DIR, filename)

@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    path = os.path.join(PHOTOS_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)