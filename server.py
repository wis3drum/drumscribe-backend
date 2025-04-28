from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import uvicorn
import os
import shutil
import youtube_dl
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
    if not file.filename.endswith(('.wav', '.mp3', '.ogg', '.flac')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only audio files are allowed.")

    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail="File too large. Max 20MB allowed.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    num_hits = simulate_detect_hits(file_path)
    partition_image_path = generate_partition_image(file_path, num_hits)
    image_url = f"https://drumscribe.onrender.com/{partition_image_path}"

    return {
        "message": "Audio processed.",
        "file_name": file.filename,
        "estimated_hits": num_hits,
        "partition_image_url": image_url
    }

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

        # After download
        num_hits = simulate_detect_hits(filename)
        partition_image_path = generate_partition_image(filename, num_hits)
        image_url = f"https://drumscribe.onrender.com/{partition_image_path}"

        return {
            "message": "Link processed.",
            "file_name": os.path.basename(filename),
            "estimated_hits": num_hits,
            "partition_image_url": image_url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def simulate_detect_hits(file_path):
    try:
        audio = AudioSegment.from_file(file_path)
        duration_seconds = len(audio) / 1000
        estimated_hits = int(duration_seconds * 2)
        return estimated_hits
    except Exception as e:
        return f"Error processing audio: {str(e)}"

def generate_partition_image(file_path, num_hits):
    output_image_path = os.path.join(PARTITION_DIR, f"{os.path.basename(file_path)}_partition.png")

    plt.figure(figsize=(12, 2))
    plt.plot([i for i in range(num_hits)], [0 for _ in range(num_hits)], 'ro')
    plt.title("DrumScribe AI - Estimated Drum Hits")
    plt.yticks([])
    plt.xticks(range(0, num_hits, max(1, num_hits // 10)))
    plt.grid(True)
    plt.savefig(output_image_path)
    plt.close()

    return output_image_path

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
