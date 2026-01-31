from flask import Flask, render_template, request, send_file, jsonify, after_this_request
import yt_dlp
import os
import uuid

app = Flask(__name__)

# Safe directory for temporary files on cloud servers like Render
DOWNLOAD_DIR = "/tmp/downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    quality = data.get("quality")
    
    if not url or not quality:
        return jsonify({"error": "Missing video link or quality selection!"}), 400
    
    # Generate unique filename to avoid conflicts between users
    unique_id = uuid.uuid4().hex
    filename = f"FTY_VIDEO_{quality}p_{unique_id}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    try:
        ydl_opts = {
            # Logic to merge best video and audio based on selected quality
            "format": f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": filepath,
            "quiet": True,
            "noplaylist": True,
            "merge_output_format": "mp4",
        }
        
        # Start downloading the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # --- File Cleanup Logic ---
        # This function runs automatically after the file is sent to the user
        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                app.logger.error(f"Error cleaning up file: {e}")
            return response

        # Send the file to the user's browser
        return send_file(filepath, as_attachment=True)
    
    except Exception as e:
        # Delete partial file if download fails
        if os.path.exists(filepath):
            os.remove(filepath)
        print(f"Download error: {e}")
        return jsonify({"error": "Download failed! Please check the link or try another quality."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
