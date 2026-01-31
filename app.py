from flask import Flask, request, send_file, jsonify, after_this_request, render_template
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app)

# ডিরেক্টরি সেটআপ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    url = data.get("url")
    quality = data.get("quality", "720")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    # ইউটিউব ব্লক এড়াতে শক্তিশালী কনফিগারেশন
    ydl_opts = {
        "format": f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best",
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "cookiefile": "cookies.txt",  # গিটহাবে অবশ্যই cookies.txt ফাইল থাকতে হবে
        "quiet": True,
        "noplaylist": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "po_token": ["web+web_embedded"]
            }
        },
        "http_headers": {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            original_filename = ydl.prepare_filename(info)
            final_path = original_filename.rsplit(".", 1)[0] + ".mp4"
            video_title = info.get('title', 'video').replace('/', '_')

        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(final_path):
                    os.remove(final_path)
            except Exception as error:
                app.logger.error(f"Error removing file: {error}")
            return response

        return send_file(
            final_path, 
            as_attachment=True, 
            download_name=f"{video_title}.mp4"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
