# get_footage.py
import requests
import yaml
import os
import math
import random
from moviepy.video.fx.Resize import Resize
from moviepy.video.fx.LumContrast import LumContrast
from moviepy.video.fx.CrossFadeIn import CrossFadeIn
from moviepy.video.fx.CrossFadeOut import CrossFadeOut
from moviepy.video.fx.GammaCorrection import GammaCorrection
from moviepy.video.fx.MultiplyColor import MultiplyColor
from moviepy.video.fx.Scroll import Scroll
from moviepy.video.fx.MultiplySpeed import MultiplySpeed
import numpy as np
#charger l'environnement variables depuis le fichier .env
from dotenv import load_dotenv
load_dotenv()

from moviepy import (
    VideoFileClip,
    TextClip,
    AudioFileClip,
    ImageClip,
    VideoClip,
    concatenate_videoclips,
    CompositeVideoClip
)

FONT_PATH = "C:/Windows/Fonts/arialbd.ttf"


def load_config():
    """
    Lit le fichier YAML contenant la clé Pexels
    et autres paramètres éventuels.
    """
    with open('./config/settings.yaml', 'r') as f:
        return yaml.safe_load(f)

def add_pan_effect(clip):
    return Scroll(x_speed=random.uniform(-5, 5), y_speed=0)(clip)


def dynamic_effect(clip):
    """
    Applique un ensemble d'effets "dynamiques" :
    - Zoom progressif
    - Luminosité/contraste random
    - Gamma random
    - Léger filtre coloré
    - Pan horizontal léger
    - Optionnel : speed up/down
    
    Pour apporter de la variété, on randomise un peu
    plus de paramètres que dans la version initiale.
    """
    duration = clip.duration

    # On définit un zoom plus ou moins rapide
    max_zoom_factor = random.uniform(0.02, 0.05)  # 5% à 12% d'agrandissement
    zoomed_clip = clip.with_effects([
        Resize(lambda t: 1 + max_zoom_factor * (t / duration))
    ])

    # On applique LumContrast avec un range élargi
    lum_value = random.uniform(2, 12)        # + ou - lumineux
    contrast_value = random.uniform(0.8, 1.1)
    lum_clip = zoomed_clip.with_effects([
        LumContrast(lum=lum_value, contrast=contrast_value)
    ])

    # Gamma aléatoire pour rendre le résultat moins monotone
    gamma_clip = lum_clip.with_effects([
        GammaCorrection(random.uniform(0.7, 1.4))
    ])

    # Filtre coloré subtil
    # (1.0,1.0,1.0) = pas de changement
    # On prend une légère teinte vintage (ex: (1.08, 1.04, 0.95)) + petit random
    color_shift = (
        1.0 + random.uniform(-0.02, 0.05),
        1.0 + random.uniform(-0.03, 0.03),
        1.0 + random.uniform(-0.05, 0.01)
    )
    color_clip = gamma_clip.with_effects([
        MultiplyColor(color_shift)
    ])

    # On applique le pan horizontal
    final_clip = color_clip

    # (Optionnel) On peut randomiser la vitesse : x0.9 à x1.2
    # => Ralenti ou accéléré pour casser la monotonie
    speed_factor = random.uniform(0.9, 1.2)
    speedx = MultiplySpeed(speed_factor)
    # On applique la vitesse
    final_clip = final_clip.with_effects([speedx])

    return final_clip


def add_timer_overlay(clip):
    """
    Amélioration du timer overlay :
    - Texte de décompte fluide (mise à jour chaque frame)
    - Barre de progression animée (sans flicker)
    """
    duration = clip.duration
    overlay_clips = []

    # -----------
    # Timer texte dynamique (mise à jour à chaque frame)
    # -----------
    def make_timer_frame(t):
        time_left = int(duration - t)
        text = f"{time_left}s restantes"
        return TextClip(
            text=text,
            font=FONT_PATH,
            font_size=70,
            color="white",
            stroke_color="black",
            stroke_width=5,
            method="label"
        ).get_frame(t)

    #timer_clip = VideoClip(make_timer_frame, duration=duration)
    #timer_clip = timer_clip.with_position(('center', int(clip.h * 0.05)))
    #overlay_clips.append(timer_clip)

    # -----------
    # Progress bar
    # -----------
    bar_height = 50
    bar_width = int(clip.w * 0.8)
    bar_x = (clip.w - bar_width) // 2
    bar_y = int(clip.h * 0.25)

    def make_bar_frame(t):
        progress = min(t / duration, 1.0)
        current_width = int(bar_width * progress)
        frame = np.zeros((bar_height, bar_width, 3), dtype=np.uint8)
        frame[:, :current_width] = [0, 255, 0]
        return frame

    bar_clip = VideoClip(make_bar_frame, duration=duration)
    bar_clip = bar_clip.with_position((bar_x, bar_y))
    overlay_clips.append(bar_clip)

    # -----------
    # Composition finale
    # -----------
    final = CompositeVideoClip([clip, *overlay_clips], size=clip.size)
    return final





def apply_crossfade_effects(clips, duration=0.12):
    """
    Applique un crossfade visuel (fondu entrée/sortie) entre les clips.
    """
    clips_with_fades = []

    for i, clip in enumerate(clips):
        effects = []

        if i != 0:
            effects.append(CrossFadeIn(duration))  # ✅ correct
        if i != len(clips) - 1:
            effects.append(CrossFadeOut(duration))  # ✅ correct

        clip_with_effects = clip.with_effects(effects)
        clips_with_fades.append(clip_with_effects)

    return clips_with_fades

def get_video_montage(query, audio_path="./assets/audio/voice.mp3", output_dir="./assets/backgrounds"):
    """
    1) Télécharge plusieurs vidéos verticales depuis Pexels (via 'query')
    2) Sélectionne des segments courts (1 à 2s) dans chaque clip
    3) Applique divers effets dynamiques (zoom, lum, gamma, pan, speed)
    4) Concatène en un montage vertical dont la durée = durée de l'audio
    5) Exporte 2 versions : avec audio et sans audio
    """

    # Fichiers de sortie
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_with_audio = os.path.join(output_dir, "video_with_audio.mp4")
        output_no_audio   = os.path.join(output_dir, "video_silent.mp4")
    else:
        # Fallback, ou bien on stocke quand même dans un dossier temporaire par défaut :
        output_with_audio = "./assets/backgrounds/video_with_audio.mp4"
        output_no_audio   = "./assets/backgrounds/video_silent.mp4"

    # Charge l'audio pour connaître la durée cible
    voiceover = AudioFileClip(audio_path)
    audio_duration = voiceover.duration
    print(f"🎧 Durée audio : {audio_duration:.2f} s")

    # Calcul du nb de segments vidéo nécessaires
    segment_min, segment_max = 1.0, 2.0
    segments_needed = math.ceil(audio_duration / ((segment_min + segment_max) / 2))
    per_page = min(80, segments_needed * 3)

    config = load_config()  # À adapter selon votre config
    load_dotenv()
    headers = {"Authorization": os.getenv("PEXELS_API_KEY")}
    params = {"query": query, "orientation": "portrait", "per_page": per_page}

    response = requests.get(
        "https://api.pexels.com/videos/search",
        headers=headers,
        params=params
    )
    response.raise_for_status()
    all_videos = response.json().get('videos', [])

    if not all_videos:
        print(f"⚠️ Aucune vidéo trouvée pour : {query}")
        return

    clips, temp_files, total_duration = [], [], 0.0

    for video_item in all_videos:
        # On recherche un fichier vidéo ~ vertical (1080x1920 => ratio ~0.5625)
        possible_files = sorted(
            video_item.get('video_files', []),
            key=lambda vf: (vf['width'] * vf['height']),
            reverse=True
        )

        best_link = None
        for vf in possible_files:
            ratio = vf['width'] / vf['height']
            if 0.54 < ratio < 0.58:  # tolérance autour de 0.5625
                best_link = vf['link']
                break

        if not best_link:
            continue

        # Téléchargement du clip
        temp_file = f"temp_dynamic_{len(temp_files)}.mp4"
        try:
            video_data = requests.get(best_link).content
            with open(temp_file, 'wb') as f:
                f.write(video_data)
            temp_files.append(temp_file)

            clip = VideoFileClip(temp_file)
            seg_duration = random.uniform(segment_min, min(segment_max, clip.duration))

            max_start = max(0, clip.duration - seg_duration)
            start_time = random.uniform(0, max_start)
            subclip = clip.subclipped(start_time, start_time + seg_duration)

            # Redimensionnement: on force du 1080x1920
            target_width, target_height = 1080, 1920
            clip_aspect_ratio = subclip.w / subclip.h
            target_aspect_ratio = target_width / target_height

            if clip_aspect_ratio > target_aspect_ratio:
                subclip = subclip.resized(height=target_height)
                subclip = subclip.cropped(width=target_width, x_center=subclip.w / 2)
            else:
                subclip = subclip.resized(width=target_width)
                subclip = subclip.cropped(height=target_height, y_center=subclip.h / 2)

            # Applique l'effet dynamique
            dynamic_clip = dynamic_effect(subclip)
            clips.append(dynamic_clip)
            total_duration += dynamic_clip.duration

            # On arrête si on couvre déjà la durée audio
            if total_duration >= audio_duration:
                break

        except Exception as e:
            print(f"⚠️ Erreur téléchargement/traitement : {temp_file} | {e}")

    if not clips:
        print("❌ Aucun clip valide. Montage impossible.")
        return

    # Crossfade entre les clips (optionnel)
    clips = apply_crossfade_effects(clips, duration=0.15)

    # Concaténation, on borne la durée au temps de l'audio
    final_clip = concatenate_videoclips(clips, method="compose").subclipped(0, audio_duration)
    final_clip = add_timer_overlay(final_clip)


    # (Facultatif) Ajout overlay (timer, watermark, etc.)
    # final_clip = add_timer_overlay(final_clip)

    # ------------------------------------------------------------------
    # 1) Version AVEC audio : on associe la piste voiceover
    # ------------------------------------------------------------------
    final_clip_with_audio = final_clip.with_audio(voiceover)

    final_clip_with_audio.write_videofile(
        output_with_audio,
        codec='libx264',
        audio_codec='aac',
        fps=30,
        threads=4,
        preset="medium",
        ffmpeg_params=["-pix_fmt", "yuv420p"]
    )
    print(f"✅ Montage dynamique créé (AVEC audio) : {output_with_audio}")

    # ------------------------------------------------------------------
    # 2) Version SANS audio
    # ------------------------------------------------------------------
    # Ici, on prend final_clip (qui n’avait pas d’audio fixé),
    # et on désactive explicitement l’audio lors de l’export
    final_clip.write_videofile(
        output_no_audio,
        codec='libx264',
        fps=30,
        threads=4,
        preset="medium",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
        audio=False  # <- désactivation de la piste audio
    )
    print(f"✅ Montage dynamique créé (SANS audio) : {output_no_audio}")

    # On ferme les clips pour libérer la mémoire
    for c in clips:
        c.close()
    voiceover.close()
    final_clip.close()
    final_clip_with_audio.close()

    # On supprime les fichiers temporaires
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)

    return output_with_audio


'''
if __name__ == "__main__":
    # Exemple d'utilisation
    query = "nature"
    audio_path = "./assets/audio/voice.mp3"
    output_with_audio = get_video_montage(query, audio_path)

'''
    
