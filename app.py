from flask import Flask, request, render_template_string, send_file, jsonify
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import sys
import zipfile
import yt_dlp
import librosa
import soundfile as sf
import threading
import numpy as np

app = Flask(__name__)

# Global progress tracking
progress_data = {
    'status': 'idle',
    'progress': 0,
    'message': 'Ready',
    'current': 0,
    'total': 0
}

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Mashup</title>
    <style>
        body { font-family: Arial; max-width: 500px; margin: 50px auto; }
        input, button { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
        button { background: #ff9800; color: white; border: none; cursor: pointer; }
        button:hover { background: #e68900; }
        #progress-container { display: none; margin: 20px 0; }
        #progress-bar { width: 100%; height: 30px; background: #e0e0e0; border-radius: 15px; overflow: hidden; }
        #progress-fill { height: 100%; background: linear-gradient(90deg, #4caf50, #8bc34a); transition: width 0.3s; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; }
        #progress-text { margin-top: 10px; text-align: center; color: #555; }
    </style>
</head>
<body>
    <h2>Mashup</h2>
    <form method="POST">
        <input type="text" name="singer" placeholder="Singer Name" required>
        <input type="number" name="videos" placeholder="Number of Videos" min="11" required>
        <input type="number" name="duration" placeholder="Duration (sec)" min="21" required>
        <input type="email" name="email" placeholder="Email ID" required>
        <button type="submit">Submit</button>
    </form>
    {% if message %}
    <p>{{ message }}</p>
    {% endif %}
    <div id="progress-container">
        <div id="progress-bar">
            <div id="progress-fill" style="width: 0%;">0%</div>
        </div>
        <div id="progress-text">Initializing...</div>
    </div>
    <a href="/download" id="download-link" style="display:none;">Download Mashup</a>
    <button id="emailjs-btn" style="display:none; background:#2196f3; color:white; padding:10px; border:none; margin-top:10px; cursor:pointer;">Send Mashup via Email</button>
    <script src="https://cdn.jsdelivr.net/npm/emailjs-com@3/dist/email.min.js"></script>
    <script>
    // EmailJS setup
    emailjs.init('s0qz07TFYkGJPw_7Z'); // Public Key
    
    function sendMashupEmail(email) {
        var link = window.location.origin + '/download';
        emailjs.send('service_asstztj', 'template_vpx', {
            to_email: email,
            mashup_url: link
        }).then(function(response) {
            alert('Mashup link sent via email!');
        }, function(error) {
            alert('Failed to send email: ' + error.text);
        });
    }
    
    // Progress tracking
    var progressInterval = null;
    
    function startProgressTracking() {
        document.getElementById('progress-container').style.display = 'block';
        progressInterval = setInterval(function() {
            fetch('/progress').then(r => r.json()).then(data => {
                var progressFill = document.getElementById('progress-fill');
                var progressText = document.getElementById('progress-text');
                
                progressFill.style.width = data.progress + '%';
                progressFill.textContent = data.progress + '%';
                progressText.textContent = data.message;
                
                if (data.status === 'completed') {
                    clearInterval(progressInterval);
                    document.getElementById('download-link').style.display = 'block';
                    document.getElementById('emailjs-btn').style.display = 'block';
                    setTimeout(function() {
                        document.getElementById('progress-container').style.display = 'none';
                    }, 2000);
                } else if (data.status === 'error') {
                    clearInterval(progressInterval);
                    progressText.textContent = 'Error: ' + data.message;
                    progressFill.style.background = '#f44336';
                }
            });
        }, 500);
    }
    
    // Check if processing started
    var checkInterval = setInterval(function() {
        fetch('/progress').then(r => r.json()).then(data => {
            if (data.status === 'processing' && progressInterval === null) {
                startProgressTracking();
                clearInterval(checkInterval);
            }
        });
    }, 500);
    
    // EmailJS button click handler
    document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('emailjs-btn').onclick = function() {
            var email = document.querySelector('input[name="email"]').value;
            if (email) {
                sendMashupEmail(email);
            } else {
                alert('Please enter an email address');
            }
        };
    });
    </script>
</body>
</html>
'''

# Route to download mashup zip
@app.route('/download')
def download():
    zip_path = 'mashup_result.zip'
    if os.path.exists(zip_path):
        return send_file(zip_path, as_attachment=True)
    return 'Mashup not ready', 404

# Route to check if mashup zip is ready
@app.route('/check_mashup')
def check_mashup():
    zip_path = 'mashup_result.zip'
    return jsonify({'ready': os.path.exists(zip_path)})

# Route to get progress status
@app.route('/progress')
def get_progress():
    return jsonify(progress_data)

def process_mashup(singer, num_videos, duration, email, output_zip):
    global progress_data
    print(f"\n{'='*60}", flush=True)
    print(f"THREAD STARTED - Creating mashup for: {singer}", flush=True)
    print(f"Videos: {num_videos}, Duration: {duration}s", flush=True)
    print(f"{'='*60}\n", flush=True)
    sys.stdout.flush()
    
    progress_data = {'status': 'processing', 'progress': 0, 'message': 'Initializing...', 'current': 0, 'total': num_videos}
    print(f"[START] Mashup generation started", flush=True)
    sys.stdout.flush()
    
    # Clean up any leftover temp files
    import glob
    for temp_file in glob.glob('temp_*.*'):
        try:
            os.remove(temp_file)
            print(f"[CLEANUP] Removed old temp file: {temp_file}", flush=True)
        except:
            pass
    
    # Progress tracking for metadata extraction
    metadata_count = {'extracted': 0}
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            # Update progress during actual file downloads
            pass
        elif d.get('info_dict'):
            # Metadata extraction progress
            metadata_count['extracted'] += 1
            pct = 7 + int((metadata_count['extracted'] / num_videos) * 3)  # 7% to 10%
            progress_data['progress'] = pct
            progress_data['message'] = f"Fetching metadata {metadata_count['extracted']}/{num_videos}..."
            print(f"[PROGRESS {pct}%] Metadata {metadata_count['extracted']}/{num_videos}", flush=True)
            sys.stdout.flush()
    
    try:
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
            'quiet': False,
            'outtmpl': 'temp_%(id)s.%(ext)s',
            'noplaylist': True,
            'no_warnings': False,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'progress_hooks': [progress_hook],
            'playlistend': num_videos,  # Only extract metadata for the videos we need
            'extract_flat': False,  # Need full info to download
            'keepvideo': False,
            'postprocessors': [],  # No post-processing to speed things up
        }
        search_query = f"ytsearch{num_videos}:{singer}"
        combined_audio = None
        sr = 16000  # Lower sample rate for faster processing (was 22050)
        duration_sec = duration
        
        progress_data['message'] = f'Searching for {singer}...'
        progress_data['progress'] = 5
        print(f"[PROGRESS 5%] Searching for videos: {search_query}", flush=True)
        sys.stdout.flush()
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                progress_data['message'] = f'Fetching metadata for {num_videos} videos...'
                progress_data['progress'] = 7
                print(f"[PROGRESS 7%] Fetching search results from YouTube (this may take a minute)...", flush=True)
                sys.stdout.flush()
                
                # Extract info - yt-dlp will only process up to playlistend items
                info = ydl.extract_info(search_query, download=False)
                
                progress_data['message'] = 'Metadata retrieved successfully'
                progress_data['progress'] = 10
                print(f"[PROGRESS 10%] Metadata extracted, processing results...", flush=True)
                sys.stdout.flush()
                
                entries = info.get('entries', [])
                print(f"Extracted {len(entries)} videos (requested {num_videos})", flush=True)
                
                # Slice to exact number needed
                entries = entries[:num_videos]
                
                if not entries:
                    raise Exception(f"No videos found for '{singer}'")
                
                progress_data['message'] = f'Found {len(entries)} videos'
                progress_data['progress'] = 10
                progress_data['total'] = len(entries)
                print(f"[PROGRESS 10%] Found {len(entries)} videos", flush=True)
                sys.stdout.flush()
            except Exception as search_error:
                print(f"[SEARCH ERROR] {search_error}", flush=True)
                sys.stdout.flush()
                raise
            
            for i, entry in enumerate(entries):
                try:
                    progress_data['current'] = i + 1
                    base_progress = 10 + int((i / len(entries)) * 80)
                    video_title = entry.get('title', 'Unknown')[:50]
                    
                    progress_data['message'] = f'Downloading {i+1}/{len(entries)}...'
                    progress_data['progress'] = base_progress
                    print(f"[PROGRESS {base_progress}%] Downloading video {i+1}/{len(entries)}: {video_title}", flush=True)
                    sys.stdout.flush()
                    
                    ydl.download([entry['webpage_url']])
                    
                    progress_data['message'] = f'Processing {i+1}/{len(entries)}...'
                    progress_data['progress'] = base_progress + 2
                    print(f"[PROGRESS {base_progress + 2}%] Download complete, processing audio...", flush=True)
                    sys.stdout.flush()
                    
                    # Find the downloaded file
                    exts = ['webm', 'm4a', 'mp3', 'mp4', 'opus']
                    file = None
                    for ext in exts:
                        candidate = f"temp_{entry['id']}.{ext}"
                        if os.path.exists(candidate):
                            file = candidate
                            break
                    
                    if not file:
                        print(f"[WARNING] File not found for {entry['id']}, skipping...", flush=True)
                        sys.stdout.flush()
                        continue
                    
                    print(f"[INFO] Loading audio from {file} (size: {os.path.getsize(file)} bytes)...", flush=True)
                    sys.stdout.flush()
                    
                    try:
                        y, loaded_sr = librosa.load(file, sr=sr, mono=True, duration=duration_sec)
                        print(f"[INFO] Audio loaded successfully: {len(y)} samples at {loaded_sr}Hz", flush=True)
                        sys.stdout.flush()
                    except Exception as load_error:
                        print(f"[ERROR] Failed to load audio: {load_error}", flush=True)
                        sys.stdout.flush()
                        os.remove(file)
                        continue
                    
                    if combined_audio is None:
                        combined_audio = y
                    else:
                        combined_audio = np.concatenate((combined_audio, y))
                    
                    os.remove(file)
                    progress_data['message'] = f'Completed {i+1}/{len(entries)}'
                    print(f"[SUCCESS] Video {i+1}/{len(entries)} processed successfully!", flush=True)
                    sys.stdout.flush()
                except Exception as e:
                    print(f"[ERROR] Failed to process video {i+1}: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    sys.stdout.flush()
                    # Continue with next video
                    continue
        
        temp_mp3 = "mashup.wav"
        if combined_audio is not None and len(combined_audio) > 0:
            progress_data['message'] = 'Creating final mashup...'
            progress_data['progress'] = 95
            print(f"[PROGRESS 95%] Writing final mashup file...", flush=True)
            sys.stdout.flush()
            sf.write(temp_mp3, combined_audio, sr)
            with zipfile.ZipFile(output_zip, 'w') as zf:
                zf.write(temp_mp3, "mashup.wav")
            os.remove(temp_mp3)
            progress_data['status'] = 'completed'
            progress_data['progress'] = 100
            progress_data['message'] = 'Mashup ready for download!'
            print(f"[PROGRESS 100%] ✓ Mashup created successfully: {output_zip}", flush=True)
            print(f"\n{'='*60}", flush=True)
            print(f"MASHUP COMPLETE!", flush=True)
            print(f"{'='*60}\n", flush=True)
            sys.stdout.flush()
        else:
            progress_data['status'] = 'error'
            progress_data['message'] = 'No audio was combined'
            print("[ERROR] No audio was combined. Mashup failed.", flush=True)
            sys.stdout.flush()
    except Exception as e:
        progress_data['status'] = 'error'
        progress_data['message'] = f'Error: {str(e)[:100]}'
        print(f"\n[CRITICAL ERROR] {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.stdout.flush()

## send_email removed; now handled by frontend

@app.route('/', methods=['GET', 'POST'])
def index():
    global progress_data
    if request.method == 'POST':
        print("\n>>> FORM SUBMITTED <<<", flush=True)
        # Reset progress
        progress_data = {'status': 'idle', 'progress': 0, 'message': 'Ready', 'current': 0, 'total': 0}
        
        singer = request.form['singer']
        num_videos = int(request.form['videos'])
        duration = int(request.form['duration'])
        email = request.form['email']
        
        print(f"Singer: {singer}, Videos: {num_videos}, Duration: {duration}s", flush=True)
        
        output_zip = "mashup_result.zip"
        # Remove old mashup if exists
        if os.path.exists(output_zip):
            os.remove(output_zip)
            print(f"Removed old mashup file", flush=True)
        
        print(f"Starting background thread...", flush=True)
        sys.stdout.flush()
        threading.Thread(target=process_mashup, args=(singer, num_videos, duration, email, output_zip), daemon=True).start()
        print(f"Thread started successfully!", flush=True)
        sys.stdout.flush()
        return render_template_string(HTML, message="Processing started! Watch the progress bar below.")
    
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(debug=True)
