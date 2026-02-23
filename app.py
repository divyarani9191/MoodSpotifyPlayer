from flask import Flask, jsonify, render_template
from mood_spotify_player_debug import record_voice, detect_mood, play_song

app = Flask(__name__)

# ---------- GUI PAGE ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- DETECT ROUTE ----------
@app.route("/detect", methods=["GET"])
def detect():

    audio_path = record_voice()

    if not audio_path:
        return jsonify({"status": "no_voice"})

    mood = detect_mood(audio_path)

    if not mood:
        return jsonify({"status": "no_mood"})

    song_name, artist = play_song(mood)

    if not song_name:
        return jsonify({"status": "error"})

    return jsonify({
        "status": "ok",
        "mood": mood,
        "song": song_name,
        "artist": artist
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)