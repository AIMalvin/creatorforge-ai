import os
import io
import random
import requests
from pydub import AudioSegment
from moviepy.video.fx.MultiplySpeed import MultiplySpeed
from moviepy import AudioFileClip
from dotenv import load_dotenv


def speed_change(sound, speed=1.0):
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)


# Liste de voix disponibles
VOICE_IDS = [
    "aQROLel5sQbj1vuIVi6B",  # voix 1
    "FvmvwvObRqIHojkEGh5N",  # voix 2
    "ohItIVrXTBI80RrUECOD",  # voix 3
    "AmMsHJaCw4BtwV3KoUXF",
    "IHngRooVccHyPqB4uQkG",
    "KbaseEXyT9EE0CQLEfbB" 
]
load_dotenv()
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVEN_API_KEY:
    raise EnvironmentError("⚠️ ELEVEN_API_KEY manquant dans l'environnement.")


# Chemin FFMPEG (à adapter si nécessaire)
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"
AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"

def generate_voice(text: str, path: str):
    voice_id = random.choice(VOICE_IDS)  # 🎲 Choix aléatoire de la voix
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_API_KEY,
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.35,
            "similarity_boost": 1.0,
            "style": 0.75,
            "use_speaker_boost": True
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        audio_data = response.content

        if len(audio_data) < 1000:
            raise Exception("Audio reçu trop petit – probablement vide.")

        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        faster_audio = speed_change(audio_segment, 1.1)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        faster_audio.export(path, format="mp3")

        print(f"✅ Voix générée avec '{voice_id}' : {path}")
    except requests.HTTPError as http_err:
        print(f"⚠️ Erreur HTTP : {http_err.response.status_code} - {http_err.response.text}")
    except Exception as e:
        print(f"❌ Échec génération audio : {e}")
        if os.path.exists(path):
            os.remove(path)
            print("🗑️ Fichier audio vide supprimé.")
