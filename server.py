from fastapi import FastAPI, UploadFile, File
import uvicorn
import shutil
import os

app = FastAPI()

@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    file_location = f"uploaded_audios/{file.filename}"
    
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    # Ici, on lancerait le modèle IA pour analyser l'audio
    # simulate_processing(file_location)

    return {"message": "Audio received and being processed", "file": file.filename}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
