import os
os.environ["PATH"] += os.pathsep + r"C:\Users\divya\Downloads\ffmpeg-8.0.1-essentials_build\bin"

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
from datetime import datetime

# ================= VOICE ENGINE =================
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

# ================= SPOTIFY =================
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="63ae557f57cd4e31aeb8bcc0db1673d8",
    client_secret="93cc866850954c41a38d0f5b16925a03",
    redirect_uri="http://localhost:8888/callback",
    scope="user-read-playback-state,user-modify-playback-state"
))

# ================= DATABASE =================
client = MongoClient("mongodb://localhost:27017/")
db = client["EmoHeal"]
collection = db["mood_music_history"]

# ================= MICROPHONE =================
recognizer = sr.Recognizer()
mic = sr.Microphone(device_index=1)

# ================= SAVE AUDIO =================
def save_audio(audio, filename="voice.wav"):
    with open(filename, "wb") as f:
        f.write(audio.get_wav_data())

# ================= RECORD VOICE =================
def record_voice():
    with mic as source:
        speak("Please tell me how you feel")
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)

        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)
            save_audio(audio)
            time.sleep(1)
            speak("Thank you. Processing your emotion.")
            return "voice.wav"

        except sr.WaitTimeoutError:
            speak("No voice detected. Please tell how you are feeling right now.")
            return None

# ================= LOAD MODEL =================
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
    print("🔊 Volume level:", volume)

    if volume < 0.003:
        speak("I could not hear anything. Please speak louder.")
        return None

    # ===== TRY SPEECH TEXT =====
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio).lower()
            print("🗣️ You said:", text)

            if any(word in text for word in [
                "good","happy","great","awesome","amazing","excited",
                "fine","relaxed","positive","wonderful","nice", "fantastic",
                 "joy", "joyful", "glad", "fine", "better",
                "relaxed", "peaceful", "positive", "wonderful", "nice",
                "feeling good", "feeling great", "feeling awesome",
                 "i am feeling good", "i feel good",
                "i feel great","i am fine",
                "doing well", "content"
            ]):
                return "happy"

            elif any(word in text for word in [
                "sad","low","depressed","down","unhappy",
                "upset","lonely","tired","bad day",
                "cry", "crying", "upset", "heartbroken",
                "lonely", "tired", "bad day", "feeling bad",
                "not good"
            ]):
                return "sad"

            elif any(word in text for word in [
                "angry","mad","frustrated","annoyed",
                "irritated", "furious", "rage", "hate",
                "i feel angry", "pissed", "fed up"
            ]):
                return "angry"

            elif any(word in text for word in [
                "scared","fear","afraid","anxious","suicide", "terrified",
                "nervous", "anxious", "worried",
                "panic", "panicking", "i am scared",
                "i feel scared", "so scared"
            ]):
                return "fear"

            else:
                return "neutral"

    except Exception as e:
        print("Speech recognition error:", e)

    # ===== FALLBACK EMOTION MODEL =====
    result = audio_emotion({"array": speech, "sampling_rate": sr_rate})
    label = result[0]['label'].lower()
    score = result[0]['score']

    print("🔮 Emotion:", label, "| confidence:", score)

    if score < 0.40:
        speak("I am not sure about your emotion. Please try again.")
        return None

    if "happy" in label: return "happy"
    if "sad" in label: return "sad"
    if "angry" in label: return "angry"
    if "fear" in label: return "fear"
    return "neutral"

# ================= GET TRACKS =================
def get_tracks(mood):
    try:
        mood_map = {
            "happy": "happy hindi",
            "sad": "sad hindi",
            "angry": "calm relaxing music",
            "fear": "meditation music",
            "neutral": "top hits hindi"
        }

        query = mood_map.get(mood, "top hits hindi")

        results = sp.search(q=query, type='playlist', limit=5)

        if not results or not results.get('playlists'):
            return []

        playlists = results['playlists']['items']
        if not playlists:
            return []

        # first valid playlist lo
        playlist_id = None
        for p in playlists:
            if p and p.get('id'):
                playlist_id = p['id']
                break

        if not playlist_id:
            return []

        tracks_data = sp.playlist_items(playlist_id)

        if not tracks_data or not tracks_data.get('items'):
            return []

        tracks = []

        for item in tracks_data['items']:
            track = item.get('track') if item else None
            if track and track.get('uri'):
                tracks.append(track['uri'])

        print("🎶 Tracks found:", len(tracks))
        return tracks

    except Exception as e:
        print("Spotify playlist error:", e)
        return []

# ================= PLAY SONG =================
def play_song(mood):

    tracks = get_tracks(mood)

    if not tracks:
        speak("Could not find songs")
        return

    # ===== GET ACTIVE DEVICE =====
    try:
        devices_data = sp.devices()

        if not devices_data or not devices_data.get("devices"):
            speak("Please open Spotify and play any song once")
            print("❌ No Spotify device found")
            return

        device_id = None

        # active device dhundo
        for d in devices_data["devices"]:
            if d.get("is_active"):
                device_id = d["id"]
                break

        # agar active nahi mila → first device use karo
        if not device_id:
            device_id = devices_data["devices"][0]["id"]

        sp.transfer_playback(device_id=device_id, force_play=True)

    except Exception as e:
        print("Device error:", e)
        speak("Spotify device connection problem")
        return

    # ===== PLAY RANDOM SONG =====
    song_uri = random.choice(tracks)

    try:
        sp.start_playback(device_id=device_id, uris=[song_uri])

        # URI → track id extract karo
        track_id = song_uri.split(":")[-1]
        track = sp.track(track_id)

        song_name = track["name"]
        artist = track["artists"][0]["name"]

        print(f"🎵 Playing: {song_name} - {artist}")
        speak(f"Playing {song_name}")

    except Exception as e:
        print("Playback error:", e)
        speak("Could not play song")

# ================= MAIN =================
def main():
    speak("Hello. I am your emotion based music assistant")

    while True:
        audio_path = record_voice()

        if audio_path is None:
            continue

        mood = detect_mood(audio_path)
        if mood is None:
            continue

        play_song(mood)
        time.sleep(2)
        speak("Press enter if you want another song")
        input()

if __name__ == "__main__":
    main()