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
    return render_template("index.html")  # index.html অবশ্যই templates ফোল্ডারে থাকতে হবে

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    url = data.get("url")
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    file_id = str(uuid.uuid4())
    final_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp4")

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": final_path,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "noplaylist": True,
        "merge_output_format": "mp4",  # video+audio merge
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return jsonify({"error": "ভিডিও ডাউনলোড করতে পারছি না। লিঙ্ক চেক করুন।"}), 500

            video_title = info.get("title", "video").replace("/", "_")

        @after_this_request
        def remove_file(response):
            if os.path.exists(final_path):
                os.remove(final_path)
            return response

        return send_file(final_path, as_attachment=True, download_name=f"{video_title}.mp4")

    except Exception as e:
        print("Download error:", e)  # debug এর জন্য
        return jsonify({"error": f"ডাউনলোড ব্যর্থ হয়েছে। কারন: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
