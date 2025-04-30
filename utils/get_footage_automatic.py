import requests
import yaml
import os
import time
import math

from moviepy import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    vfx
)

def load_config():
    with open('./config/settings.yaml', 'r') as f:
        return yaml.safe_load(f)

def get_video_montage(query, audio_path="./assets/audio/voice.mp3", switch_duration=2):

    output_file = "./assets/backgrounds/video.mp4"

    # 1) Charger l'audio pour connaître la durée totale
    audio = AudioFileClip(audio_path)
    audio_duration = audio.duration
    print(f"🎧 Durée audio : {audio_duration:.2f} s")

    segments_needed = math.ceil(audio_duration / switch_duration)


    per_page = min(80, segments_needed * 2)

    config = load_config()
    headers = {"Authorization": config['pexels_api_key']}
    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": per_page
    }

    response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)
    response.raise_for_status()
    all_videos = response.json().get('videos', [])

    if not all_videos:
        print(f"⚠️ Aucune vidéo trouvée pour : {query}")
        return None

    print(f"🔍 {len(all_videos)} résultats retournés par Pexels (filtrage en cours).")

    temp_files = []
    opened_clips = []

    video_clips = []
    total_montage_time = 0.0

    for video_item in all_videos:


        best_link = None
        for vf in video_item.get('video_files', []):
            width, height = vf['width'], vf['height']
            if (width >= 1080
                and height >= 1920
                and abs((width / height) - (9 / 16)) < 0.01
            ):
                best_link = vf['link']
                break

        if not best_link:
            continue

        temp_file = f"temp_video_{len(temp_files)}.mp4"
        try:
            video_data = requests.get(best_link).content
            with open(temp_file, 'wb') as f:
                f.write(video_data)
            temp_files.append(temp_file)
        except Exception as e:
            print(f"❌ Erreur téléchargement vidéo : {best_link} → {e}")
            continue

        try:
            clip = VideoFileClip(temp_file)
            opened_clips.append(clip)

            clip_duration = clip.duration
            start_t = 0.0

            while start_t < clip_duration and total_montage_time < audio_duration:
                end_t = start_t + switch_duration

                if end_t > clip_duration:
                    end_t = clip_duration

                segment_length = end_t - start_t
                if total_montage_time + segment_length > audio_duration:
                    segment_length = audio_duration - total_montage_time
                    end_t = start_t + segment_length

                subclip = clip.subclipped(start_t, end_t)
                
                resized = subclip.with_effects([vfx.Resize((1080, 1920))])
                final_seg = resized.with_effects([
                    vfx.Crop(width=1080,
                             height=1920,
                             x_center=resized.w / 2,
                             y_center=resized.h / 2)
                ])

                video_clips.append(final_seg)
                total_montage_time += segment_length
                start_t += switch_duration

                # Si on a atteint la durée audio, on arrête de découper
                if total_montage_time >= audio_duration:
                    break

        except Exception as e:
            print(f"⚠️ Erreur lecture/traitement de la vidéo {temp_file}: {e}")

        # On quitte la boucle si l'audio est rempli
        if total_montage_time >= audio_duration:
            break

    if video_clips:
        print(f"🎬 Total segments générés : {len(video_clips)} → Durée cumulée : {total_montage_time:.2f} s")
        final_clip = concatenate_videoclips(video_clips, method="compose").with_audio(audio)
        final_clip.write_videofile(
            output_file,
            codec='libx264',
            audio_codec='aac',
            fps=30,
            threads=4,
            preset="medium",
            ffmpeg_params=["-pix_fmt", "yuv420p"]
        )
        print(f"✅ Montage final enregistré : {output_file}")
    else:
        print("❌ Aucun segment valide trouvé, montage annulé.")

    # 5) Nettoyage
    for c in opened_clips:
        c.close()
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)


if __name__ == "__main__":
    start = time.time()
    get_video_montage("café", audio_path="./assets/audio/voice.mp3", switch_duration=3)
    print("Temps d'exécution :", time.time() - start, "secondes.")
