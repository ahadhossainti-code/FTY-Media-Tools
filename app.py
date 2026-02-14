from flask import Flask, request, send_file, jsonify, render_template, after_this_request, Response
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app)

# Render-এর জন্য /tmp ডিরেক্টরি ব্যবহার করা নিরাপদ
DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ১. গুগল ভেরিফিকেশন রুট
@app.route("/google9e2fb0bcc08994d3.html")
def google_verify():
    return "google-site-verification: google9e2fb0bcc08994d3.html"

# ২. রোবটস ফাইল (গুগলকে সাইট ক্রল করার অনুমতি দিতে এবং লাইন ব্রেক ঠিক করতে)
@app.route("/robots.txt")
def robots():
    # এখানে '\n' ব্যবহার করা হয়েছে এবং মিম-টাইপ 'text/plain' করা হয়েছে যাতে গুগল পড়তে পারে
    robots_content = "User-agent: *\nAllow: /\nSitemap: https://fty-media-tools-1.onrender.com/sitemap.xml"
    return Response(robots_content, mimetype='text/plain')

# ৩. সাইটম্যাপ রুট (গুগল সার্চ কনসোলের "Couldn't fetch" এরর ঠিক করতে)
@app.route("/sitemap.xml")
def sitemap():
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://fty-media-tools-1.onrender.com/</loc>
        <lastmod>2026-02-14</lastmod>
        <priority>1.0</priority>
      </url>
    </urlset>"""
    return Response(sitemap_xml, mimetype='application/xml')

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
    final_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp4")

    # yt-dlp এর জন্য আপডেট করা অপশন
    ydl_opts = {
        "format": f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best",
        "outtmpl": final_path,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
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
        if os.path.exists(final_path):
            os.remove(final_path)
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
