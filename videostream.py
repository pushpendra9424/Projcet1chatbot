from flask import Flask, render_template, request, redirect, url_for, send_from_directory, abort
from werkzeug.utils import secure_filename
import os
import sqlite3
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'videos.db'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Initialize the database
def init_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            upload_time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Home route
@app.route('/')
def home():
    conn = sqlite3.connect(app.config['DATABASE'])
    videos = conn.execute('SELECT * FROM videos ORDER BY upload_time DESC').fetchall()
    conn.close()
    return render_template('home.html', videos=videos)

# Upload route
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form.get('title')
        file = request.files.get('file')
        if not title or not file:
            return "Title and file are required", 400
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            conn = sqlite3.connect(app.config['DATABASE'])
            conn.execute(
                'INSERT INTO videos (title, filename, upload_time) VALUES (?, ?, datetime("now"))',
                (title, unique_filename)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('home'))
        else:
            return "Invalid file type", 400
    return render_template('upload.html')

# Watch video route
@app.route('/watch/<int:video_id>')
def watch(video_id):
    conn = sqlite3.connect(app.config['DATABASE'])
    video = conn.execute('SELECT * FROM videos WHERE id = ?', (video_id,)).fetchone()
    conn.close()
    if not video:
        abort(404)
    return render_template('watch.html', video=video)

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Create HTML templates (overwrite if exist)
with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Video Streamer</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f2f2f2;
            margin: 0;
            padding: 0;
        }
        header {
            background-color: #4CAF50;
            padding: 20px;
            text-align: center;
            color: white;
        }
        main {
            max-width: 900px;
            margin: 20px auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
        }
        a {
            text-decoration: none;
            color: #4CAF50;
        }
        a:hover {
            text-decoration: underline;
        }
        .video-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .video-card {
            border: 1px solid #ccc;
            padding: 10px;
            background-color: #fafafa;
            border-radius: 6px;
        }
        .upload-btn {
            display: inline-block;
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            margin-bottom: 10px;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <header><h1>Video Streamer</h1></header>
    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>''')

with open('templates/home.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base.html" %}
{% block content %}
<a href="{{ url_for('upload') }}" class="upload-btn">Upload New Video</a>
<div class="video-list">
    {% for video in videos %}
    <div class="video-card">
        <h3>{{ video[1] }}</h3>
        <video width="100%" controls>
            <source src="{{ url_for('uploaded_file', filename=video[2]) }}" type="video/{{ video[2].rsplit('.', 1)[1].lower() }}">
            Your browser does not support the video tag.
        </video>
        <p><a href="{{ url_for('watch', video_id=video[0]) }}">Watch Fullscreen</a></p>
    </div>
    {% else %}
    <p>No videos uploaded yet.</p>
    {% endfor %}
</div>
{% endblock %}''')

with open('templates/upload.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base.html" %}
{% block content %}
<h2>Upload a New Video</h2>
<form method="post" enctype="multipart/form-data">
    <p>Title: <input type="text" name="title" required></p>
    <p>Video File: <input type="file" name="file" accept="video/*" required></p>
    <button type="submit">Upload</button>
</form>
{% endblock %}''')

with open('templates/watch.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base.html" %}
{% block content %}
<h2>{{ video[1] }}</h2>
<video width="100%" controls autoplay>
    <source src="{{ url_for('uploaded_file', filename=video[2]) }}" type="video/{{ video[2].rsplit('.', 1)[1].lower() }}">
    Your browser does not support the video tag.
</video>
<p><a href="{{ url_for('home') }}">Back to videos</a></p>
{% endblock %}''')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)