import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ffmpeg_path = os.path.join(BASE_DIR, "ffmpeg", "bin")

os.environ["PATH"] += os.pathsep + ffmpeg_path

import numpy as np
import soundfile as sf
import time
import random
import speech_recognition as sr
import pyttsx3
from transformers import pipeline
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta

# ===================== TIME (IST) =====================
IST = timezone(timedelta(hours=5, minutes=30))

# ===================== VOICE ENGINE =================
def speak(text):
    print("🤖", text)
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 170)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print("Voice error:", e)
    time.sleep(0.6)

# ===================== SPOTIFY =====================
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="63ae557f57cd4e31aeb8bcc0db1673d8",
    client_secret="93cc866850954c41a38d0f5b16925a03",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-read-playback-state,user-modify-playback-state"
))

# ===================== MONGODB =====================
uri = "mongodb+srv://emoheal_user:Emoheal123@cluster0.hwezm4z.mongodb.net/?appName=Cluster0"
client = MongoClient(uri)
db = client["emohealDB"]
voice_collection = db["voice_emotions"]

print("✅ MongoDB Connected")

# ===================== MIC =====================
recognizer = sr.Recognizer()
mic = sr.Microphone(device_index=1)

# ================= SAVE AUDIO =================
def save_audio(audio, filename="voice.wav"):
    with open(filename, "wb") as f:
        f.write(audio.get_wav_data())

# ================= RECORD =================
def record_voice():
    with mic as source:
        speak("Please tell me how you feel")
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)

        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)
            save_audio(audio)
            speak("Processing your emotion")
            return "voice.wav"

        except sr.WaitTimeoutError:
            speak("No voice detected, try again")
            return None

# ================= MODEL =================
print("⬇️ Loading emotion model...")
audio_emotion = pipeline(
    "audio-classification",
    model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
)

# ================= DETECT MOOD =================
def detect_mood(audio_path):
    speech, sr_rate = sf.read(audio_path)

    if len(speech.shape) > 1:
        speech = np.mean(speech, axis=1)

    volume = np.mean(np.abs(speech))
    print("🔊 Volume:", volume)

    if volume < 0.003:
        speak("Speak louder please")
        return None

    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio).lower()
            print("🗣️ You said:", text)

            happy_kw = [
                "good","happy","great","awesome","amazing","excited","relaxed","positive","chill",
                "joyful","delighted","pleased","content","satisfied","grateful","cheerful",
                "fantastic","wonderful","lovely","blessed","thrilled","on top of the world",
                "feeling good","super happy","so happy","feeling great","in a good mood",
                "smiling","laughing","feeling awesome","overjoyed","ecstatic","peaceful"
                ]
            sad_kw = [
                "sad","low","depressed","down","unhappy","lonely","not happy",
                "heartbroken","crying","feeling bad","miserable","gloomy","upset",
                "hurt","feeling empty","lost","hopeless","tired of everything",
                "feeling weak","broken","not okay","feeling sad","blue","melancholy",
                "feeling down","emotionally drained","feeling useless"
                ]
            angry_kw = [
                "angry","mad","frustrated","annoyed",
                "irritated","furious","rage","pissed","fed up",
                "losing temper","hate","so angry","very angry",
                "aggressive","outraged","triggered","boiling",
                "can't tolerate","sick of this","getting angry",
                "snapped","enraged"
                ]
            fear_kw = [
                "scared","fear","afraid","anxious",
                "worried","nervous","panic","panicking",
                "terrified","uneasy","restless","shaking",
                "fearful","insecure","overthinking","stressed",
                "tense","frightened","paranoid","doubtful",
                "uncertain","feeling unsafe","anxiety","panic attack"
                ]
            neutral_kw = [
                "okay","ok","normal","fine","nothing","nothing much",
                "as usual","same","routine","average",
                "so so","meh","just another day","no mood",
                "not sure","idk","nothing special","going on",
                "alright","fine I guess","just chilling",
                "just working","just studying","usual stuff"
                ]

            def count_match(keywords):
                return sum(1 for word in keywords if word in text)

            scores = {
                "happy": count_match(happy_kw),
                "sad": count_match(sad_kw),
                "angry": count_match(angry_kw),
                "fear": count_match(fear_kw),
                "neutral": count_match(neutral_kw)
            }

            print("📊 Scores:", scores)

            mood = max(scores, key=scores.get)

            if scores[mood] == 0:
                return "unknown"

            return mood

    except Exception as e:
        print("Speech error:", e)

    # ✅ SAFE MODEL FALLBACK (no crash now)
    try:
        result = audio_emotion({"array": speech, "sampling_rate": sr_rate})
        label = result[0]['label'].lower()
        score = result[0]['score']

        print("🔮 Emotion:", label, score)

        if score < 0.40:
            return None

        if "happy" in label: return "happy"
        if "sad" in label: return "sad"
        if "angry" in label: return "angry"
        if "fear" in label: return "fear"

    except Exception as e:
        print("Model error:", e)

    return "unknown"

# ================= TRACKS =================
def get_tracks(mood):
    try:
        mood_map = {
            "happy": "happy hindi songs",
            "sad": "sad hindi songs",
            "angry": "motivational relaxing music",
            "fear": "meditation music",
            "neutral": "top hindi songs"
        }

        results = sp.search(q=mood_map.get(mood, "top hindi songs"), type='track', limit=20)
        items = results['tracks']['items'] if results and results.get('tracks') else []

        return [item['uri'] for item in items if item and item.get('uri')]

    except Exception as e:
        print("Spotify error:", e)
        return []

# ================= PLAY =================
def play_song(mood):
    tracks = get_tracks(mood)

    if not tracks:
        speak("No songs found")
        return ""

    devices = sp.devices()

    if not devices.get("devices"):
        speak("Open Spotify first")
        return ""

    device_id = devices["devices"][0]["id"]
    sp.transfer_playback(device_id=device_id, force_play=True)

    song_uri = random.choice(tracks)
    sp.start_playback(device_id=device_id, uris=[song_uri])

    track = sp.track(song_uri.split(":")[-1])
    name = track["name"]

    speak(f"Playing {name}")
    return name

# ================= STOP / RESUME =================
def stop_song():
    try:
        sp.pause_playback()
        print("⏹ Song stopped")
    except Exception as e:
        print("Stop error:", e)

def resume_song():
    try:
        sp.start_playback()
        print("▶ Song resumed")
    except Exception as e:
        print("Resume error:", e)

# ================= MAIN (GUI FRIENDLY) =================
def run_voice_once():
    speak("Hello, I am your emotion music assistant")

    audio_path = record_voice()
    if not audio_path:
        return "No voice"

    mood = detect_mood(audio_path)

    if mood is None:
        return "Low volume"

    if mood == "unknown":
        speak("I could not understand your mood")
        return "unknown"

    song = play_song(mood)

    record = {
        "emotion": mood,
        "song": song,
        "time": datetime.now(IST)
    }

    voice_collection.insert_one(record)
    print("✅ Saved:", record)

    return mood, song
