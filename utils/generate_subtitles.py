#generate_subtitles.py

import random
import os
import whisper
from moviepy import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    ImageClip,
    vfx
)
from moviepy.video.fx import FadeIn, Resize


SUBTITLE_COLORS = [
    "white", "yellow", "cyan", "deeppink", "gold"
]
FONT_PATH = "C:/Windows/Fonts/arialbd.ttf"


SUBTITLE_COLORS = [
    "white", "yellow", "cyan", "deeppink", "gold", "lightgreen", "magenta", "orange"
]

EMOJI_IMAGE_MAP = {
    "💰": "./assets/emojis/money.png",
    "📈": "./assets/emojis/chart.png",
    "🔥": "./assets/emojis/fire.png",
    "🤖": "./assets/emojis/robot.png"
}

SEMANTIC_EMOJI_COLOR_MAP = {
    "argent": {
        "keywords": ["argent", "revenu", "salaire", "cash", "monnaie", "paiement", "euro", "dollar", "crypto", "financement", "bitcoin"],
        "emoji": "💰", "color": "gold"
    },
    "croissance": {
        "keywords": ["croissance", "hausse", "explose", "augmente", "evolue", "monter", "scaler", "expansion", "ameliore", "boom"],
        "emoji": "📈", "color": "lightgreen"
    },
    "motivation": {
        "keywords": ["motivation", "ambition", "determination", "discipline", "focus", "reve", "vision", "objectif", "mental", "courage", "succès", "confiance"],
        "emoji": "🔥", "color": "yellow"
    },
    "intelligence_artificielle": {
        "keywords": ["ia", "intelligence", "artificielle", "gpt", "chatgpt", "machine", "neurone", "openai", "modele", "deep"],
        "emoji": "🤖", "color": "cyan"
    }
}

def get_emoji_and_color_for_word(word):
    word = word.lower()
    for values in SEMANTIC_EMOJI_COLOR_MAP.values():
        if any(keyword in word for keyword in values["keywords"]):
            return values["emoji"], values["color"]
    return "", random.choice(SUBTITLE_COLORS)



def create_emoji_clip(emoji, start, end, video_w, video_h):
    if emoji not in EMOJI_IMAGE_MAP:
        return None
    
    emoji_path = EMOJI_IMAGE_MAP[emoji]
    emoji_clip = (
        ImageClip(emoji_path)
        .resized(height=150)  # taille ajustable
        .with_start(start)
        .with_end(end+0.5)
        .with_position(("center", int(video_h * 0.70)))  # au-dessous du mot
    )
    emoji_clip = FadeIn(0.2).apply(emoji_clip)
    return emoji_clip


def chunk_text_by_words(segments, max_words=1):
    """
    Découpe chaque segment Whisper en mini sous-titres de max_words mots
    pour un affichage plus dynamique.
    """
    print("✂️ Découpage en sous-titres dynamiques (4 mots max)...")
    subs = []
    for seg in segments:
        words = seg['text'].strip().split()
        seg_duration = seg['end'] - seg['start']
        if not words or seg_duration <= 0:
            continue

        word_duration = seg_duration / len(words)

        for i in range(0, len(words), max_words):
            chunk_words = words[i:i + max_words]
            chunk_text = " ".join(chunk_words)
            start_time = seg['start'] + i * word_duration
            end_time = start_time + len(chunk_words) * word_duration

            subs.append({
                "start": start_time,
                "end": end_time,
                "text": chunk_text
            })

    print(f"🧩 {len(subs)} sous-titres créés (dynamiques).")
    return subs


def save_subtitles_to_srt(subtitles, output_path):
    """
    Sauvegarde les sous-titres au format .srt
    """
    def format_timestamp(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    with open(output_path, "w", encoding="utf-8") as f:
        for i, sub in enumerate(subtitles, 1):
            f.write(f"{i}\n")
            f.write(f"{format_timestamp(sub['start'])} --> {format_timestamp(sub['end'])}\n")
            f.write(f"{sub['text'].strip()}\n\n")

def transcribe_audio_to_subs(audio_path):
    """
    Transcrit le fichier audio en texte (via Whisper), retourne la liste
    des segments start/end/text, et sauvegarde en .srt.
    """
    print("🎙️ Transcription avec Whisper...")
    model = whisper.load_model("medium")  # ou "small"/"large" selon ton besoin
    result = model.transcribe(audio_path)

    subtitles = [{
        "start": seg['start'],
        "end": seg['end'],
        "text": seg['text']
    } for seg in result['segments']]

    print(f"📝 {len(subtitles)} sous-titres générés.")

    # Sauvegarde .srt
    base_name = os.path.splitext(audio_path)[0]
    srt_path = f"{base_name}.srt"
    save_subtitles_to_srt(subtitles, srt_path)
    print(f"💾 Sous-titres enregistrés dans : {srt_path}")

    return subtitles

def format_subtitle_text(text, max_chars=50):
    """
    Coupe le texte en 2 lignes max (~50 caractères max par ligne)
    pour mieux remplir la vidéo verticale sans déborder.
    """
    words = text.strip().split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line + " " + word) <= max_chars:
            current_line += (" " + word if current_line else word)
        else:
            lines.append(current_line.strip())
            current_line = word
    # Ajout de la dernière ligne
    lines.append(current_line.strip())

    # Retourne uniquement 2 lignes max
    return "\n".join(lines[:2])


def create_animated_subtitle_clip(text, start, end, video_w, video_h):
    """
    Crée un TextClip avec :
      - Couleur aléatoire
      - Fade-in / pop (resize progressif)
      - Position verticale fixe (ajustable) ou légèrement aléatoire
    """
    word = text.strip()
    emoji, color = get_emoji_and_color_for_word(word)


    # Mise en forme du texte

    # Création du clip texte de base
    txt_clip = TextClip(
        text=text,
        font=FONT_PATH,
        font_size=100,
        color=color,
        stroke_color="black",
        stroke_width=6,
        method="caption",
        size=(int(video_w * 0.8), None),  # 80% de la largeur, hauteur auto
        text_align="center",             # alignement dans la box
        horizontal_align="center",       # box centrée horizontalement
        vertical_align="center",         # box centrée verticalement
        interline=4,
        transparent=True
    )


    y_choices = [int(video_h * 0.45), int(video_h * 0.55), int(video_h * 0.6)]
    base_y = random.choice(y_choices)

    txt_clip = txt_clip.with_position(("center", base_y))
    txt_clip = txt_clip.with_start(start).with_end(end)

    # On applique un fadein + un petit effet "pop" qui grandit de 5% sur la durée du chunk
    # 1) fadein de 0.2s
    clip_fadein = FadeIn(duration=0.2).apply(txt_clip)

    # 2) agrandissement progressif (ex: 1.0 → 1.05 sur la durée)
    duration_subtitle = end - start
    def pop_effect(t):
        if duration_subtitle > 0:
            progress = t / duration_subtitle
            scale = 1.0 + 0.07 * (1 - (1 - progress) ** 3)  # easing out cubic
        else:
            scale = 1.0
        return scale

    resize_effect = Resize(pop_effect)
    clip_pop = resize_effect.apply(clip_fadein)  # ✅ Utilisation correcte



    return clip_pop, emoji


def add_subtitles_to_video(video_path, subtitles, output_file="./assets/output/video_with_subs.mp4"):
    """
    Insère les sous-titres animés/couleur dans la vidéo,
    recadre en 1080x1920 si besoin et exporte le résultat.
    """
    print("🎬 Insertion des sous-titres optimisés SHORTS...")

    video = VideoFileClip(video_path)

    '''
    # Force le format vertical 1080×1920 si non conforme
    if (video.w, video.h) != (1080, 1920):
        print("📐 Recadrage vidéo en 1080×1920...")
        video = video.resized((1080, 1920))
    '''

    clips = [video]

    for sub in subtitles:
        start_time = sub['start']
        end_time = sub['end']
        text_chunk = sub['text']

        animated_sub_clip, emoji = create_animated_subtitle_clip(
            text_chunk, start_time, end_time, video_w=video.w, video_h=video.h
        )
        clips.append(animated_sub_clip)
        emoji_clip = create_emoji_clip(emoji, start_time, end_time, video.w, video.h)
        if emoji_clip:
            clips.append(emoji_clip)

    final = CompositeVideoClip(clips, size=(1080, 1920)).with_duration(video.duration)

    # Export en MP4 H.264 + AAC, 30 fps
    final.write_videofile(
        output_file,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        threads=4,
        preset="medium",
        ffmpeg_params=["-pix_fmt", "yuv420p"]
    )

    print(f"✅ Vidéo Shorts/TikTok prête : {output_file}")


# -----------------------------
#    EXEMPLE D'UTILISATION
# -----------------------------
if __name__ == "__main__":
    AUDIO_PATH = "./assets/audio/voice.mp3"
    VIDEO_PATH = "./assets/output/final_video.mp4"
    OUTPUT_PATH = "./assets/output/video_with_subs.mp4"

    # 1. Transcription via Whisper
    segments = transcribe_audio_to_subs(AUDIO_PATH)

    # 2. Découpage en mini-chunks (4 mots max) 
    subtitles = chunk_text_by_words(segments, max_words=1)

    # 3. Ajout des sous-titres animés
    add_subtitles_to_video(VIDEO_PATH, subtitles, OUTPUT_PATH)


# -----------------------------
#    EXEMPLE D'UTILISATION
# -----------------------------
if __name__ == "__main__":
    AUDIO_PATH = "./assets/audio/voice.mp3"
    VIDEO_PATH = "./assets/output/final_video.mp4"
    OUTPUT_PATH = "./assets/output/video_with_subs.mp4"

    # 1. Transcription via Whisper
    segments = transcribe_audio_to_subs(AUDIO_PATH)

    # 2. Découpage en mini-chunks (4 mots max) 
    subtitles = chunk_text_by_words(segments, max_words=1)

    # 3. Ajout des sous-titres animés
    add_subtitles_to_video(VIDEO_PATH, subtitles, OUTPUT_PATH)
