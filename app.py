import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from video_generator import generate_memorial_video
import json

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5GB limit

# Ensure folders exist
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/outputs/<path:filename>')
def serve_output(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/update_subtitles', methods=['POST'])
def update_subtitles():
    try:
        data = request.json
        srt_path = data.get('srt_path')
        srt_content = data.get('srt_content')
        
        if not srt_path or not srt_content:
            return jsonify({'status': 'error', 'message': 'Path or content missing'}), 400

        # Ensure the path is within the output folder for security
        if not srt_path.startswith(app.config['OUTPUT_FOLDER']):
             return jsonify({'status': 'error', 'message': 'Invalid path'}), 403

        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
            
        return jsonify({'status': 'success', 'message': '자막이 성공적으로 저장되었습니다.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # 1. Get Form Data
        deceased_name = request.form.get('deceased_name', '고인')
        deceased_bio = request.form.get('deceased_bio', '')
        user_bio = request.form.get('user_bio', '')
        video_speed = float(request.form.get('video_speed', 1.0))
        title_speed = float(request.form.get('title_speed', 1.0))
        body_speed = float(request.form.get('body_speed', 1.0))
        ending_speed = float(request.form.get('ending_speed', 1.0))
        print(f"DEBUG RECV: v_speed={video_speed}, t_speed={title_speed}, b_speed={body_speed}, e_speed={ending_speed}")

        # 2. Get Files
        photos = request.files.getlist('photos')
        music = request.files.get('music')
        # Subtitles can be uploaded as a file or from text input
        subtitle_file = request.files.get('subtitle_file')
        subtitle_text = request.form.get('subtitle_text', '')

        job_id = str(uuid.uuid4())[:8]
        job_dir = os.path.join(UPLOAD_FOLDER, job_id)
        os.makedirs(job_dir, exist_ok=True)

        # Save Photos
        saved_photos = []
        for photo in photos:
            if photo.filename:
                path = os.path.join(job_dir, photo.filename)
                photo.save(path)
                saved_photos.append(path)

        # Save Music
        music_path = None
        if music and music.filename:
            music_path = os.path.join(job_dir, music.filename)
            music.save(music_path)

        # Save Subtitles
        sub_path = None
        if subtitle_file and subtitle_file.filename:
            sub_path = os.path.join(job_dir, subtitle_file.filename)
            subtitle_file.save(sub_path)
        elif subtitle_text:
            sub_path = os.path.join(job_dir, 'subtitles.txt')
            with open(sub_path, 'w', encoding='utf-8') as f:
                f.write(subtitle_text)

        # 3. Create unique output directory
        output_dir = os.path.join(OUTPUT_FOLDER, f"memorial_{job_id}_{deceased_name}")
        os.makedirs(output_dir, exist_ok=True)

        # 4. Trigger Video Generation Logic
        result = generate_memorial_video(
            photos=saved_photos,
            music=music_path,
            subtitles=sub_path,
            deceased_info={'name': deceased_name, 'bio': deceased_bio, 'user_bio': user_bio},
            video_speed=video_speed,
            subtitle_speeds={'title': title_speed, 'body': body_speed, 'ending': ending_speed},
            output_dir=output_dir
        )

        return jsonify({
            'status': 'success',
            'message': '제작이 완료되었습니다.',
            'output_dir': output_dir,
            'files': os.listdir(output_dir)
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
