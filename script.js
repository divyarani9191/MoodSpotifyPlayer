async function detectMood() {

    document.getElementById("status").innerText = "Listening...";
    document.getElementById("mood").innerText = "";
    document.getElementById("song").innerText = "";

    try {
        const response = await fetch("http://127.0.0.1:5000/detect");
        const data = await response.json();

        if (data.status === "success") {
            document.getElementById("status").innerText = "Music playing 🎵";
            document.getElementById("mood").innerText = "Mood: " + data.mood;
            document.getElementById("song").innerText = "Song: " + data.song;
        } else {
            document.getElementById("status").innerText = data.message;
        }

    } catch (error) {
        document.getElementById("status").innerText = "Server error";
    }
}