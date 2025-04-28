from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import uvicorn
import os
import shutil
import youtube_dl
import librosa
import numpy as np
from pydub import AudioSegment
import matplotlib.pyplot as plt

app = FastAPI()

UPLOAD_DIR = "uploaded_audios"
PARTITION_DIR = "generated_scores"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PARTITION_DIR, exist_ok=True)

MAX_FILE_SIZE_MB = 20

@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(('.wav', '.mp3', '.ogg', '.flac', '.webm')):
            raise HTTPException(status_code=400, detail="Invalid file type. Only audio files are allowed (.wav, .mp3, .ogg, .flac, .webm).")

        contents = await file.read()
        file_size_mb = len(contents) / (1024 * 1024)

        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(status_code=400, detail="File too large. Max 20MB allowed.")

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        num_hits = detect_drum_hits(file_path)
        partition_image_path = generate_partition_image(file_path, num_hits)
        image_url = f"https://drumscribe.onrender.com/{partition_image_path}"

        return {
            "message": "Audio processed successfully.",
            "file_name": file.filename,
            "estimated_hits": num_hits,
            "partition_image_url": image_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error during upload: {str(e)}")

@app.post("/process-link/")
async def process_link(link: str = Form(...)):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{UPLOAD_DIR}/%(title)s.%(ext)s',
            'quiet': True
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)

            if not os.path.exists(filename):
                raise HTTPException(status_code=400, detail="Error downloading audio file.")

        num_hits = detect_drum_hits(filename)
        partition_image_path = generate_partition_image(filename, num_hits)
        image_url = f"https://drumscribe.onrender.com/{partition_image_path}"

        return {
            "message": "Link processed successfully.",
            "file_name": os.path.basename(filename),
            "estimated_hits": num_hits,
            "partition_image_url": image_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error during link processing: {str(e)}")

def detect_drum_hits(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None, mono=True)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, backtrack=True)
        return len(onsets)
    except Exception as e:
        print(f"Error during hit detection: {e}")
        return 0

def generate_partition_image(file_path, num_hits):
    output_image_path = os.path.join(PARTITION_DIR, f"{os.path.basename(file_path)}_partition.png")

    plt.figure(figsize=(12, 2))
    plt.plot([i for i in range(num_hits)], [0 for _ in range(num_hits)], 'ro')
    plt.title("DrumScribe AI - Detected Drum Hits")
    plt.yticks([])
    plt.xticks(range(0, max(1, num_hits), max(1, num_hits // 10)))
    plt.grid(True)
    plt.savefig(output_image_path)
    plt.close()

    return output_image_path

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
