from flask import Flask, request, send_file, jsonify, render_template, after_this_request
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route("/")
def home():
    # index.html অবশ্যই templates ফোল্ডারে থাকতে হবে
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    url = data.get("url")
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    file_id = str(uuid.uuid4())
    # টিকটক/ফেসবুকের জন্য সহজ ফরম্যাট
    final_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp4")

    ydl_opts = {
        "format": "best",
        "outtmpl": final_path,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'video').replace('/', '_')

        @after_this_request
        def remove_file(response):
            if os.path.exists(final_path):
                os.remove(final_path)
            return response

        return send_file(final_path, as_attachment=True, download_name=f"{video_title}.mp4")

    except Exception as e:
        return jsonify({"error": "ডাউনলোড ব্যর্থ হয়েছে। লিঙ্কটি আবার চেক করুন।"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
