from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import os
import shutil
from pydub import AudioSegment

app = FastAPI()

# Crée un dossier pour stocker les fichiers uploadés s'il n'existe pas
UPLOAD_DIR = "uploaded_audios"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Limite de taille en Mo
MAX_FILE_SIZE_MB = 20

@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    # Sécurité : vérifier type de fichier
    if not file.filename.endswith(('.wav', '.mp3', '.ogg', '.flac')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only audio files are allowed.")

    # Lire la taille du fichier
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail="File too large. Maximum allowed size is 20MB.")

    # Sauvegarder le fichier uploadé
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    # Lancer traitement IA (version simplifiée pour commencer)
    num_hits = simulate_detect_hits(file_path)

    return {
        "message": "File uploaded successfully.",
        "file_name": file.filename,
        "estimated_hits": num_hits
    }

def simulate_detect_hits(file_path):
    # Simulation d'une détection de coups
    try:
        audio = AudioSegment.from_file(file_path)
        duration_seconds = len(audio) / 1000  # durée en secondes
        estimated_hits = int(duration_seconds * 2)  # Exemple simple : 2 coups/seconde
        return estimated_hits
    except Exception as e:
        return f"Error during audio processing: {str(e)}"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
