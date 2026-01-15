# ---------------- Imports ----------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import librosa
import numpy as np
from tensorflow.keras.models import load_model
from pydub import AudioSegment
import io
import base64

# ---------------- FastAPI Setup ----------------
app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Spotify Setup ----------------
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="63ae557f57cd4e31aeb8bcc0db1673d8",
    client_secret="93cc866850954c41a38d0f5b16925a03",
    redirect_uri="http://localhost:8888/callback",
    scope="user-modify-playback-state user-read-playback-state"
))

mood_playlist = {
    "happy": "spotify:playlist:37i9dQZF1DXdPec7aLTmlC",
    "sad": "spotify:playlist:37i9dQZF1DX7qK8ma5wgG1",
    "neutral": "spotify:playlist:37i9dQZF1DX4sWSpwq3LiO"
}

# ---------------- ML Model Setup ----------------
model = load_model("voice_mood_model.h5")  # aapka pre-trained model
mood_labels = ["happy", "sad", "neutral"]

# ---------------- Request Models ----------------
class MoodRequest(BaseModel):
    mood: str

class AudioRequest(BaseModel):
    audio: str

# ---------------- Routes ----------------
@app.get("/")
def root():
    return {"status": "Backend is running"}

@app.post("/detect_mood")
def detect_mood(data: AudioRequest):
    try:
        audio_bytes = base64.b64decode(data.audio.split(",")[1])
        audio_file = io.BytesIO(audio_bytes)
        audio_segment = AudioSegment.from_file(audio_file, format="webm")  # ya "wav"
        audio_segment.export("temp.wav", format="wav")

        y, sr = librosa.load("temp.wav", sr=22050)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        mfccs_scaled = np.mean(mfccs.T, axis=0).reshape(1, -1)

        pred = model.predict(mfccs_scaled)
        detected_mood = mood_labels[np.argmax(pred)]

        print("🎤 Detected mood:", detected_mood)
        return {"mood": detected_mood}
    except Exception as e:
        print("⚠ Mood detection error:", e)
        return {"mood": "neutral"}

@app.post("/play")
def play_song(data: MoodRequest):
    mood = data.mood.lower()
    print("🎵 Mood received:", mood)

    playlist_uri = mood_playlist.get(mood)
    if playlist_uri:
        try:
            devices = sp.devices()
            if devices["devices"]:
                device_id = devices["devices"][0]["id"]
                sp.start_playback(device_id=device_id, context_uri=playlist_uri)
                print(f"✅ Playing {mood} playlist on Spotify")
            else:
                print("⚠ No active Spotify device found")
        except Exception as e:
            print("⚠ Spotify playback error:", e)

    return {
        "success": True,
        "mood": mood,
        "message": f"Song will play for {mood} mood"
    }



