import time
import random
import speech_recognition as sr
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# -------------------- Spotify Setup --------------------
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="63ae557f57cd4e31aeb8bcc0db1673d8",         # <-- Your Client ID
    client_secret="93cc866850954c41a38d0f5b16925a03",   # <-- Your Client Secret
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-read-playback-state,user-modify-playback-state"
))

# Mood → Bollywood Playlist mapping
mood_playlist = {
    "happy": "spotify:playlist:3bQy66sMaRDIUIsS7UQnuO",    # Cheerful Bollywood hits
    "sad": "spotify:playlist:37i9dQZF1DXdFesNN9TzXT",      # Sad Hindi melodies
    "angry": "spotify:playlist:4jlbTgG7gqClTD2MjpUDqI",    # Intense Bollywood tracks
    "neutral": "spotify:playlist:1b6Lj2j6z1cUg2WWsuGGk0",  # Calm / feel-good
    "surprised": "spotify:playlist:6YAW8Q4YPBL1obegSiARTU",# Happy vibes
    "fear": "spotify:playlist:00QmsX0u0NrSZsZbofJgsB"      # Soft / soothing tracks
}

# -------------------- Voice to Text --------------------
r = sr.Recognizer()
mic = sr.Microphone()

def get_voice_input():
    with mic as source:
        print("🎤 Adjusting for ambient noise... please wait 1-2 seconds")
        r.adjust_for_ambient_noise(source)
        print("🎤 Now listening! Speak something into the microphone...")
        audio = r.listen(source)
        print("✅ Audio captured, processing...")
        try:
            text = r.recognize_google(audio)
            print("📝 You said:", text)
            return text
        except sr.UnknownValueError:
            print("❌ Could not understand voice. Try again.")
            return ""
        except sr.RequestError as e:
            print(f"❌ Google API error: {e}")
            return ""

# -------------------- Mood Detection --------------------
print("⬇️ Loading Hugging Face emotion model... this may take a minute")

model_name = "mrm8488/t5-base-finetuned-emotion"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
classifier = TextClassificationPipeline(model=model, tokenizer=tokenizer, return_all_scores=False)

def detect_mood(text):
    if text == "":
        return "neutral"
    result = classifier(text)
    mood = result[0]['label'].lower()
    print("🔮 Detected mood:", mood)
    if mood in ["joy", "happy", "excited"]:
        return "happy"
    elif mood in ["sad", "disappointed"]:
        return "sad"
    elif mood in ["anger", "angry", "annoyed"]:
        return "angry"
    elif mood in ["surprise", "amazed"]:
        return "surprised"
    elif mood in ["fear", "anxious"]:
        return "fear"
    else:
        return "neutral"

# -------------------- Spotify — Random Track Playback --------------------
def get_playlist_tracks(playlist_uri):
    """Fetch all track URIs from a playlist"""
    results = sp.playlist_items(playlist_uri, fields="items.track.uri,total", additional_types=['track'])
    track_uris = [item['track']['uri'] for item in results['items'] if item['track']]
    return track_uris

def play_song_by_mood(mood):
    playlist_uri = mood_playlist.get(mood, mood_playlist["neutral"])
    devices = sp.devices()
    if len(devices['devices']) == 0:
        print("⚠️ No active Spotify device found. Open Spotify on your device!")
        return

    device_id = devices['devices'][0]['id']

    # Get all tracks from playlist
    track_uris = get_playlist_tracks(playlist_uri)
    if not track_uris:
        print("⚠️ No tracks found in playlist!")
        return

    # Pick a random track
    random_track = random.choice(track_uris)
    sp.start_playback(device_id=device_id, uris=[random_track])
    print(f"🎵 Playing a random {mood} Bollywood song...")

# -------------------- Continuous Listening --------------------
def main():
    print("🎶 Bollywood Mood-Based Spotify Player Started")
    while True:
        text = get_voice_input()
        mood = detect_mood(text)
        play_song_by_mood(mood)
        print("⏳ Waiting for next voice input...\n")
        time.sleep(2)

if __name__ == "__main__":
    main()




