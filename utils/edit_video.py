from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip
import os
import random

def choose_random_music_path():
    """
    Choisit un fichier musical aléatoire depuis ./assets/music/
    """
    music_path = "./assets/music/"
    music_files = [f for f in os.listdir(music_path) if f.lower().endswith(('.mp3', '.wav', '.aac'))]

    if not music_files:
        raise FileNotFoundError("❌ Aucun fichier audio trouvé dans ./assets/music/")

    chosen_music = random.choice(music_files)
    return os.path.join(music_path, chosen_music)

def edit_video(video_path, audio_path, output_path):
    music_path = choose_random_music_path()
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path).with_volume_scaled(1.0)
    audio_duration = audio.duration
    music = AudioFileClip(music_path).with_volume_scaled(0.10)
    music = music.subclipped(0, audio_duration)
    mixed_audio = CompositeAudioClip([audio, music])
    final = video.with_audio(mixed_audio)
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")
    print(f"✅ Vidéo générée : {output_path}")

# example
# edit_video("./assets/backgrounds/video.mp4", "./assets/audio/voice.mp3", "./assets/output/final_video.mp4")