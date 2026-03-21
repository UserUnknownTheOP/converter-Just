from flask import Flask, request, jsonify, send_file
import subprocess, os, uuid, threading, time

app = Flask(__name__)
FILES = {}

def cleanup(fid, delay=300):
    def _clean():
        time.sleep(delay)
        for ext in ["gif", "wav", "mp4"]:
            try: os.remove(f"/tmp/{fid}.{ext}")
            except: pass
        FILES.pop(fid, None)
    threading.Thread(target=_clean, daemon=True).start()

@app.route("/gifsplit")
def gifsplit():
    url     = request.args.get("url")
    scale   = request.args.get("maxscale", 64, type=int)
    start   = request.args.get("start", 0, type=int)
    duration= request.args.get("duration", 0, type=int)
    fps     = request.args.get("fps", 8, type=int)

    if not url:
        return jsonify({"error": "no url"}), 400

    fid = str(uuid.uuid4())
    mp4 = f"/tmp/{fid}.mp4"
    gif = f"/tmp/{fid}.gif"
    wav = f"/tmp/{fid}.wav"

    # download
    dl_cmd = ["yt-dlp", "-o", mp4, "--no-playlist"]
    if url.endswith(".mp4") or "catbox" in url:
        dl_cmd = ["wget", "-O", mp4, url]
    result = subprocess.run(dl_cmd + ([url] if "yt-dlp" in dl_cmd[0] else []), capture_output=True)
    if result.returncode != 0:
        return jsonify({"error": "download failed: " + result.stderr.decode()}), 500

    # trim + convert to gif
    ff_args = ["ffmpeg", "-y"]
    if start: ff_args += ["-ss", str(start)]
    if duration: ff_args += ["-t", str(duration)]
    ff_args += [
        "-i", mp4,
        "-vf", f"scale={scale}:-1:flags=lanczos,fps={fps}",
        gif
    ]
    subprocess.run(ff_args, capture_output=True)

    # extract wav
    wa_args = ["ffmpeg", "-y"]
    if start: wa_args += ["-ss", str(start)]
    if duration: wa_args += ["-t", str(duration)]
    wa_args += ["-i", mp4, "-ac", "1", "-ar", "22050", wav]
    subprocess.run(wa_args, capture_output=True)

    FILES[fid] = True
    cleanup(fid)

    base = request.host_url.rstrip("/")
    return jsonify({
        "gif": f"{base}/file/{fid}/gif",
        "wav": f"{base}/file/{fid}/wav"
    })

@app.route("/file/<fid>/<ext>")
def serve_file(fid, ext):
    path = f"/tmp/{fid}.{ext}"
    if not os.path.exists(path):
        return "not found", 404
    mime = "image/gif" if ext == "gif" else "audio/wav"
    return send_file(path, mimetype=mime)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
