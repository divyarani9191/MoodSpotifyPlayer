import time
import random
import speech_recognition as sr
from transformers import pipeline
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pymongo import MongoClient
from datetime import datetime

# -------------------- Spotify Setup --------------------
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="63ae557f57cd4e31aeb8bcc0db1673d8",
    client_secret="93cc866850954c41a38d0f5b16925a03",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-read-playback-state,user-modify-playback-state"
))

# -------------------- MongoDB Setup --------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["EmoHeal"]
collection = db["mood_music_history"]

# -------------------- Mood → Playlist mapping --------------------
mood_playlist = {
    "happy": "spotify:playlist:3bQy66sMaRDIUIsS7UQnuO",
    "sad": "spotify:playlist:37i9dQZF1DXdFesNN9TzXT",
    "angry": "spotify:playlist:4jlbTgG7gqClTD2MjpUDqI",
    "neutral": "spotify:playlist:1b6Lj2j6z1cUg2WWsuGGk0",
    "surprised": "spotify:playlist:6YAW8Q4YPBL1obegSiARTU",
    "fear": "spotify:playlist:00QmsX0u0NrSZsZbofJgsB"
}

# -------------------- Voice Setup --------------------
r = sr.Recognizer()
mic = sr.Microphone()

# -------------------- WAIT FOR COMMAND --------------------
def wait_for_command():
    while True:
        with mic as source:
            print("🛑 Say 'play music' or 'start music' to continue...")
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source)

        try:
            command = r.recognize_google(audio).lower()
            print("🗣 Command:", command)

            if any(word in command for word in ["play", "start", "music"]):
                print("✅ Command accepted\n")
                return
            else:
                print("❌ Wrong command, try again\n")
        except:
            print("❌ Could not understand command\n")

# -------------------- VOICE TO TEXT --------------------
def get_voice_input():
    with mic as source:
        print("🎤 Speak how you feel...")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio)
        print("📝 You said:", text)
        return text
    except:
        print("❌ Could not understand voice")
        return ""

# -------------------- MOOD DETECTION --------------------
print("⬇️ Loading emotion model...")
classifier = pipeline(
    "text-classification",
    model="bhadresh-savani/distilbert-base-uncased-emotion",
    return_all_scores=True  # Get all scores for reliable detection
)

def detect_mood(text):
    text = text.strip()
    if text == "":
        return "neutral"

    # Pad very short inputs to help model
    if len(text.split()) < 2:
        text += " ."

    results = classifier(text)[0]  # List of dicts with 'label' and 'score'
    print("🔮 Raw model output (all scores):", results)

    # Pick the label with max score
    label = max(results, key=lambda x: x['score'])['label'].lower()

    # Map model labels to our moods
    if label == "joy":
        return "happy"
    elif label == "sadness":
        return "sad"
    elif label == "anger":
        return "angry"
    elif label == "surprise":
        return "surprised"
    elif label == "fear":
        return "fear"
    else:
        return "neutral"

# -------------------- PLAY MUSIC --------------------
def get_playlist_tracks(playlist_uri):
    tracks = []
    results = sp.playlist_items(playlist_uri)
    while results:
        for item in results['items']:
            if item['track'] and item['track']['uri']:
                tracks.append(item['track']['uri'])
        if results['next']:
            results = sp.next(results)
        else:
            results = None
    return tracks

def play_song_by_mood(mood):
    playlist_uri = mood_playlist.get(mood, mood_playlist["neutral"])
    tracks = get_playlist_tracks(playlist_uri)

    if not tracks:
        print(f"⚠️ No tracks found for mood '{mood}'")
        return

    devices = sp.devices()['devices']
    if not devices:
        print("⚠️ Open Spotify on any device first")
        return

    # Use first active device
    device_id = devices[0]['id']
    # Optionally transfer playback to this device
    sp.transfer_playback(device_id=device_id, force_play=True)

    # Play a random track
    song = random.choice(tracks)
    sp.start_playback(device_id=device_id, uris=[song])
    print(f"🎵 Playing {mood} song: {song}\n")

    # -------------------- SAVE TO DATABASE --------------------
    data = {
        "mood": mood,
        "song_uri": song,
        "timestamp": datetime.now()
    }
    collection.insert_one(data)
    print("💾 Mood & song saved to database")

# -------------------- MAIN LOOP --------------------
def main():
    print("🎶 Mood-Based Spotify Player Started\n")
    while True:
        wait_for_command()
        text = get_voice_input()
        mood = detect_mood(text)
        print(f"✨ Detected mood: {mood}\n")
        play_song_by_mood(mood)
        print("🛑 Say command again to change song\n")
        time.sleep(2)

if __name__ == "__main__":
    main()















