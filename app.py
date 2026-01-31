from flask import Flask, request, send_file, jsonify, render_template, after_this_request
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app)

# Render-এর জন্য /tmp ডিরেক্টরি ব্যবহার করা নিরাপদ
DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    url = data.get("url")
    quality = data.get("quality", "720") # HTML থেকে পাঠানো কোয়ালিটি রিসিভ করা

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    file_id = str(uuid.uuid4())
    final_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp4")

    # কোয়ালিটি অনুযায়ী ফরম্যাট সেট করা
    ydl_opts = {
        "format": f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best",
        "outtmpl": final_path,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "noplaylist": True,
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return jsonify({"error": "Could not download video. Check link."}), 500

            video_title = info.get("title", "video").replace("/", "_")

        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(final_path):
                    os.remove(final_path)
            except Exception as e:
                print(f"Error removing file: {e}")
            return response

        return send_file(final_path, as_attachment=True, download_name=f"{video_title}.mp4")

    except Exception as e:
        print("Download error:", e)
        # আংশিক ফাইল তৈরি হলে তা ডিলিট করা
        if os.path.exists(final_path):
            os.remove(final_path)
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
