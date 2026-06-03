from flask import Flask, request, jsonify, render_template, send_file
from pytubefix import YouTube
import re
import os
import shutil
import subprocess
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_video_id(url):
    parsed = urlparse(url)
    hostname = (parsed.hostname or '').lower()

    if hostname in {'youtube.com', 'www.youtube.com', 'm.youtube.com'}:
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
        if parsed.path.startswith('/shorts/'):
            return parsed.path.split('/shorts/')[1].split('/')[0]

    if hostname in {'youtu.be', 'www.youtu.be'}:
        return parsed.path.strip('/').split('/')[0] or None

    return None

def download_video(url, resolution):
    try:
        yt = YouTube(url)
        video_id = get_video_id(url) or 'video'
        out_dir = os.path.join(BASE_DIR, 'downloads', video_id)
        
        # Debug: Print all available streams
        print(f"Available progressive streams for {url}:")
        for stream in yt.streams.filter(progressive=True, file_extension='mp4'):
            print(f"  - {stream.resolution} - {stream.mime_type}")
        
        # First try progressive (video+audio) streams
        stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution=resolution).first()
        os.makedirs(out_dir, exist_ok=True)
        if stream:
            final_path = stream.download(output_path=out_dir, filename=f'{video_id}_{resolution}.mp4')
            return True, None, final_path, 'progressive'

        # If not found, try adaptive (video-only) + best audio, then merge with ffmpeg
        print(f"\nTrying adaptive streams for {resolution}:")
        video_stream = yt.streams.filter(adaptive=True, file_extension='mp4', resolution=resolution).first()
        if not video_stream:
            # fallback: list available adaptive video streams for debugging
            for s in yt.streams.filter(adaptive=True, file_extension='mp4'):
                print(f"  - {getattr(s, 'resolution', None)} - itag:{s.itag} - audio:{getattr(s, 'includes_audio_track', False)}")
            return False, "Video with the specified resolution not found.", None, None

        audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
        if not audio_stream:
            return False, "No audio stream available to merge.", None, None

        video_path = os.path.join(out_dir, f'video_{resolution}.mp4')
        audio_path = os.path.join(out_dir, f'audio_{resolution}.mp4')
        merged_path = os.path.join(out_dir, f'merged_{resolution}.mp4')

        video_stream.download(output_path=out_dir, filename=f'video_{resolution}.mp4')
        audio_stream.download(output_path=out_dir, filename=f'audio_{resolution}.mp4')

        merged_ok, merge_err = merge_video_audio(video_path, audio_path, merged_path)
        if merged_ok:
            # Optionally remove intermediate files
            try:
                os.remove(video_path)
                os.remove(audio_path)
            except Exception:
                pass
            return True, None, merged_path, 'merged'
        else:
            return False, f"Failed to merge audio and video: {merge_err}", None, None
    except Exception as e:
        return False, str(e), None, None


def merge_video_audio(video_path, audio_path, out_path):
    """Merge video and audio using ffmpeg if available. Returns (True, None) on success."""
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        bundled_ffmpeg = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'ffmpeg', 'ffmpeg-8.1.1-essentials_build', 'bin', 'ffmpeg.exe'
        )
        if os.path.exists(bundled_ffmpeg):
            ffmpeg = bundled_ffmpeg
    if not ffmpeg:
        return False, 'ffmpeg not found on PATH'

    # Try stream copy first (fast, lossless)
    cmd = [ffmpeg, '-y', '-i', video_path, '-i', audio_path, '-c', 'copy', out_path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        return True, None

    # If copy fails, try re-encoding audio to AAC and video to h264
    cmd2 = [ffmpeg, '-y', '-i', video_path, '-i', audio_path, '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '192k', out_path]
    proc2 = subprocess.run(cmd2, capture_output=True, text=True)
    if proc2.returncode == 0:
        return True, None

    # Return stderr for debugging
    return False, (proc2.stderr or proc.stderr)

def get_video_info(url):
    try:
        yt = YouTube(url)
        stream = yt.streams.first()
        video_info = {
            "title": yt.title,
            "author": yt.author,
            "length": yt.length,
            "views": yt.views,
            "description": yt.description,
            "publish_date": yt.publish_date,
        }
        return video_info, None
    except Exception as e:
        return None, str(e)

def is_valid_youtube_url(url):
    # Accept full youtube URLs and youtu.be short links
    pattern = r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtube\.com/shorts/|youtu\.be/)[\w-]+(&\S*)?$"
    return re.match(pattern, url) is not None

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/download/<resolution>', methods=['POST', 'GET'])
def download_by_resolution(resolution):
    if request.method == 'GET':
        url = request.args.get('url')
    else:
        data = request.get_json() or {}
        url = data.get('url')

    if not url:
        return jsonify({"error": "Missing 'url' parameter (body JSON or ?url=...)."}), 400

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400

    success, error_message, output_path, mode = download_video(url, resolution)

    if success:
        return jsonify({
            "message": f"Video with resolution {resolution} downloaded successfully.",
            "mode": mode,
            "file": output_path,
        }), 200
    else:
        return jsonify({"error": error_message}), 500


@app.route('/download_file/<resolution>', methods=['POST', 'GET'])
def download_file(resolution):
    if request.method == 'GET':
        url = request.args.get('url')
    else:
        data = request.get_json() or {}
        url = data.get('url')

    if not url:
        return jsonify({"error": "Missing 'url' parameter (body JSON or ?url=...)."}), 400

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400

    success, error_message, output_path, mode = download_video(url, resolution)
    if not success or not output_path or not os.path.exists(output_path):
        return jsonify({"error": error_message or "Unable to prepare download."}), 500

    return send_file(
        output_path,
        as_attachment=True,
        download_name=os.path.basename(output_path),
        mimetype='video/mp4'
    )

@app.route('/video_info', methods=['POST', 'GET'])
def video_info():
    if request.method == 'GET':
        url = request.args.get('url')
    else:
        data = request.get_json() or {}
        url = data.get('url')

    if not url:
        return jsonify({"error": "Missing 'url' parameter (body JSON or ?url=...)."}), 400

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400

    video_info, error_message = get_video_info(url)

    if video_info:
        return jsonify(video_info), 200
    else:
        return jsonify({"error": error_message}), 500


@app.route('/available_resolutions', methods=['POST', 'GET'])
def available_resolutions():
    if request.method == 'GET':
        url = request.args.get('url')
    else:
        data = request.get_json() or {}
        url = data.get('url')

    if not url:
        return jsonify({"error": "Missing 'url' parameter (body JSON or ?url=...)."}), 400

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400

    try:
        yt = YouTube(url)
        progressive_resolutions = list(set([
            stream.resolution 
            for stream in yt.streams.filter(progressive=True, file_extension='mp4')
            if stream.resolution
        ]))
        all_resolutions = list(set([
            stream.resolution 
            for stream in yt.streams.filter(file_extension='mp4')
            if stream.resolution
        ]))
        return jsonify({
            "progressive": sorted(progressive_resolutions),
            "all": sorted(all_resolutions)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
