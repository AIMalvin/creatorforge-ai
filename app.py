import streamlit as st
import pandas as pd
import os
import json
import time
import zipfile
import shutil
import undetected_chromedriver as uc

from selenium import webdriver

from utils.generate_scripts import (
    generate_script,
    one_word,
    generate_description,
    generate_title,
    generate_tags
)
from utils.generate_voice import generate_voice
from utils.get_footage import get_video_montage
from utils.edit_video import edit_video
from utils.generate_subtitles import (
    transcribe_audio_to_subs,
    chunk_text_by_words,
    add_subtitles_to_video,
    save_subtitles_to_srt
)
from utils.upload import upload_video, upload_to_tiktok


st.set_page_config(
    page_title="CreatorForge AI",
    page_icon="🎬",
    layout="wide"
)


COOKIE_FILE = "./config/tiktok_cookies.json"
EXPORT_ROOT = "./exports"





def step_progress(total):
    progress_bar = st.progress(0)
    def _update(idx, label):
        progress_bar.progress(int(idx / total * 100), text=label)
    return progress_bar, _update


def notify_success(message: str):
    st.toast(message, icon="✅")
    st.success(message)



def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
    driver = uc.Chrome(options=options)
    return driver


def load_tiktok_driver():
    if not os.path.exists(COOKIE_FILE):
        return None
    driver = get_driver()
    driver.get("https://www.tiktok.com")
    with open(COOKIE_FILE, "r", encoding="utf-8") as f:
        for cookie in json.load(f):
            driver.add_cookie(cookie)
    driver.refresh()
    return driver


def upload_video_tiktok(script: str = None, final_video: str = None):
    with st.status("Connecting & uploading to TikTok…", expanded=True) as status:
        status.write("Preparing files…")
        if not script:
            script_file = "./assets/texts/script.txt"
            if not os.path.exists(script_file):
                st.error("No script found. Please create a video first or provide a script.")
                return
            with open(script_file, "r", encoding="utf-8") as f:
                script = f.read()

        title = generate_title(script)
        description = generate_description(script)

        if not final_video:
            final_video = "./assets/output/final_video_subtitles.mp4"
            if not os.path.exists(final_video):
                st.error("No final video found. Please create a video first or provide a valid path.")
                return

        status.write("Loading driver & cookies…")
        driver = load_tiktok_driver()
        if driver is None:
            st.error("❌ No TikTok cookie found. Please log in first via the 'TikTok Login' page.")
            return

        try:
            status.write("Opening upload page…")
            driver.get("https://www.tiktok.com/upload")
            status.write("Uploading – this may take a minute…")
            upload_to_tiktok(driver, final_video, title, description)
            status.update(label="TikTok video published!", state="complete")
        except Exception as e:
            status.update(label=f"TikTok Error: {str(e)}", state="error")
        finally:
            driver.quit()


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def slugify(text: str, max_length: int = 50) -> str:
    slug = "".join(c for c in text.lower() if c.isalnum() or c in (" ", "-", "_"))
    return slug.replace(" ", "_")[:max_length]


def zip_directory(src_dir: str, dst_zip: str):
    with zipfile.ZipFile(dst_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder, _, files in os.walk(src_dir):
            for f in files:
                abs_path = os.path.join(folder, f)
                rel_path = os.path.relpath(abs_path, src_dir)
                zf.write(abs_path, rel_path)



def generate_script_and_metadata(prompt: str):
    script = generate_script(prompt)
    title = generate_title(script)
    description = generate_description(script)
    tags = generate_tags(script)
    return {
        "script": script,
        "title": title,
        "description": description,
        "tags": tags,
    }


def create_voice(script: str, voice_path: str):
    generate_voice(script, voice_path)
    return voice_path


def create_background_video(script: str, voice_path: str, output_dir: str):
    keyword = one_word(script)
    return get_video_montage(keyword, voice_path, output_dir=output_dir)


def assemble_video(bg_path: str, voice_path: str, output_path: str):
    edit_video(bg_path, voice_path, output_path)
    return output_path


def subtitle_video(video_input: str, voice_path: str, output_path: str):
    segments = transcribe_audio_to_subs(voice_path)
    subtitles = chunk_text_by_words(segments, max_words=3)
    add_subtitles_to_video(video_input, subtitles, output_path)
    return output_path


def full_video_pipeline(script: str, export_dir: str) -> str:
    """Complete pipeline with visual progress bar."""
    ensure_dir(export_dir)
    st.write("## 🚀 Video pipeline in progress")
    progress_bar, update = step_progress(total=4)

    # Step 1 – Voice
    voice_path = os.path.join(export_dir, "voice.mp3")
    create_voice(script, voice_path)
    update(1, "🔊 Voice generated")

    # Step 2 – Background video
    bg_video = create_background_video(script, voice_path, output_dir=export_dir)
    update(2, "🎞️ Background video generated")

    # Step 3 – Assembly
    video_no_subs = os.path.join(export_dir, "video_no_subs.mp4")
    assemble_video(bg_video, voice_path, video_no_subs)
    update(3, "🎬 Video assembled")

    # Step 4 – Subtitles
    final_video = os.path.join(export_dir, "final_subs.mp4")
    subtitle_video(video_no_subs, voice_path, final_video)
    update(4, "💬 Subtitles added ✨")

    notify_success("Pipeline completed!")
    return final_video




def dashboard_page():
    st.header("📊 Export Dashboard")

    if not os.path.exists(EXPORT_ROOT):
        st.info("No exports available yet.")
        return

    export_dirs = [d for d in os.listdir(EXPORT_ROOT) if os.path.isdir(os.path.join(EXPORT_ROOT, d))]
    if not export_dirs:
        st.info("No exports available yet.")
        return

    for dir_name in export_dirs:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(dir_name)
        with col2:
            if st.button("Show", key=f"show_{dir_name}"):
                files = os.listdir(os.path.join(EXPORT_ROOT, dir_name))
                st.write(files)
        with col3:
            if st.button("ZIP", key=f"zip_{dir_name}"):
                zip_path = os.path.join(EXPORT_ROOT, f"{dir_name}.zip")
                zip_directory(os.path.join(EXPORT_ROOT, dir_name), zip_path)
                with open(zip_path, "rb") as f:
                    st.download_button("Download ZIP", f, file_name=f"{dir_name}.zip")



def page_script_generation():
    st.header("📝 Script & Metadata Generation")
    prompt = st.text_input("Enter your video idea…")
    if st.button("Generate Script") and prompt.strip():
        data = generate_script_and_metadata(prompt)
        st.subheader("Script")
        st.code(data["script"])
        st.subheader("Title")
        st.write(data["title"])
        st.subheader("Description")
        st.write(data["description"])
        st.subheader("Tags")
        st.write(", ".join(data["tags"]))
        if st.button("📥 Download All"):
            slug = slugify(data["title"])
            export_dir = os.path.join(EXPORT_ROOT, slug)
            ensure_dir(export_dir)
            with open(os.path.join(export_dir, "script.txt"), "w", encoding="utf-8") as f:
                f.write(data["script"])
            with open(os.path.join(export_dir, "title.txt"), "w", encoding="utf-8") as f:
                f.write(data["title"])
            with open(os.path.join(export_dir, "description.txt"), "w", encoding="utf-8") as f:
                f.write(data["description"])
            st.success(f"Content saved in {export_dir}")


# ------------- VOICE ONLY --------

def page_voice_generation():
    st.header("🎤 AI Voice Generation")
    default_text = "Enter or paste the text to vocalize here…"
    script = st.text_area("Text to vocalize", value=default_text, height=200)
    if st.button("Generate AI Voice") and script.strip() and script != default_text:
        slug = slugify(script[:30])
        export_dir = os.path.join(EXPORT_ROOT, slug)
        ensure_dir(export_dir)
        voice_path = os.path.join(export_dir, "voice.mp3")
        with st.status("Generating voice…"):
            create_voice(script, voice_path)
        st.audio(voice_path)
        with open(voice_path, "rb") as f:
            st.download_button("Download voice", f, file_name="voice.mp3")



def page_subtitling():
    st.header("💬 Add Subtitles to a Video")
    video_file = st.file_uploader("Upload your video (MP4)", type=["mp4"])
    if video_file is not None:
        temp_video_path = os.path.join("./tmp", video_file.name)
        ensure_dir("./tmp")
        with open(temp_video_path, "wb") as f:
            f.write(video_file.read())
        st.video(temp_video_path)
        if st.button("Add Subtitles"):
            script = st.text_area("Original text (optional – otherwise automatic speech recognition)")
            voice_path = None
            if script.strip():
                voice_path = os.path.join("./tmp", "voice_tmp.mp3")
                create_voice(script, voice_path)
            else:
                voice_path = temp_video_path
            final_path = os.path.join("./tmp", "with_subs.mp4")
            with st.status("Generating subtitles…", expanded=False):
                subtitle_video(temp_video_path, voice_path, final_path)
            st.success("Subtitles added!")
            st.video(final_path)
            with open(final_path, "rb") as f:
                st.download_button("Download subtitled video", f, file_name="video_subtitles.mp4")



def page_quick_edit():
    st.header("⚡ Quick Edit (Audio + Background)")
    script = st.text_area("Text to vocalize")
    if st.button("Create Edit") and script.strip():
        slug = slugify(script[:30])
        export_dir = os.path.join(EXPORT_ROOT, slug)
        ensure_dir(export_dir)
        progress_bar, update = step_progress(3)

        voice_path = create_voice(script, os.path.join(export_dir, "voice.mp3"))
        update(1, "Voice generated")

        bg_video = create_background_video(script, voice_path, output_dir=export_dir)
        update(2, "Background created")

        final = assemble_video(bg_video, voice_path, os.path.join(export_dir, "montage.mp4"))
        update(3, "Final edit ready!")

        st.video(final)
        with open(final, "rb") as f:
            st.download_button("Download Edit", f, file_name="montage.mp4")


def page_csv_processing():
    st.header("🗂️ Automatic Processing (CSV)")
    upload_youtube_selected = st.checkbox("Upload to YouTube Shorts", value=True)
    upload_tiktok_selected = st.checkbox("Upload to TikTok", value=True)
    save_assets = st.checkbox("Save each asset", value=True)

    try:
        df_prompts = pd.read_csv("./assets/data/prompts.csv", encoding="latin1")
        st.dataframe(df_prompts)
    except FileNotFoundError:
        st.error("The file prompts.csv was not found…")
        return

    if st.button("🚀 Start Processing"):
        total = len(df_prompts)
        progress_bar, update = step_progress(total)

        for count, (index, row) in enumerate(df_prompts.iterrows(), start=1):
            prompt = row["prompt"]
            update(count - 1, f"Script {count}/{total} – generating…")
            data = generate_script_and_metadata(prompt)
            slug = slugify(data["title"])
            export_dir = os.path.join(EXPORT_ROOT, slug) if save_assets else None
            if export_dir:
                ensure_dir(export_dir)
                with open(os.path.join(export_dir, "script.txt"), "w", encoding="utf-8") as f:
                    f.write(data["script"])
            final_video = full_video_pipeline(data["script"], export_dir or "./tmp")
            if upload_youtube_selected:
                upload_video(final_video, data["title"], data["description"], data["tags"])
            if upload_tiktok_selected:
                upload_video_tiktok(script=data["script"], final_video=final_video)
            df_prompts = df_prompts.drop(index)
            df_prompts.to_csv("./assets/data/prompts.csv", index=False)
            update(count, f"Script {count}/{total} – done ✅")
        notify_success("All prompts have been processed!")



def page_full_video_generation():
    st.header("🎬 Full Video Generation")
    prompt = st.text_input("Video topic…")
    if st.button("Create Video") and prompt.strip():
        data = generate_script_and_metadata(prompt)
        slug = slugify(data["title"])
        export_dir = os.path.join(EXPORT_ROOT, slug)
        final_video = full_video_pipeline(data["script"], export_dir)
        st.video(final_video)
        with open(final_video, "rb") as f:
            st.download_button("Download Video", f, file_name="final_video.mp4")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Upload to YouTube Shorts"):
                upload_video(final_video, data["title"], data["description"], data["tags"])
        with col2:
            if st.button("Upload to TikTok"):
                upload_video_tiktok(script=data["script"], final_video=final_video)



def page_tiktok_login():
    st.header("🔐 TikTok Login")
    if st.button("Log In"):
        driver = get_driver()
        driver.get("https://www.tiktok.com/login")
        st.warning("Please log in manually in the opened window (90 seconds)…")
        time.sleep(90)
        cookies = driver.get_cookies()
        ensure_dir("./config")
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f)
        driver.quit()
        st.success("Cookies saved!")



def page_separate_uploader():
    st.header("📤 Upload a Video")
    final_video = st.file_uploader("Select an MP4 video", type=["mp4"])
    if final_video is not None:
        temp_path = os.path.join("./tmp", final_video.name)
        ensure_dir("./tmp")
        with open(temp_path, "wb") as f:
            f.write(final_video.read())
        st.video(temp_path)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Upload to YouTube Shorts"):
                script = st.text_area("Original script (to generate title/description)")
                if script.strip():
                    title = generate_title(script)
                    description = generate_description(script)
                    tags = generate_tags(script)
                else:
                    title = description = ""; tags = []
                upload_video(temp_path, title, description, tags)
        with col2:
            if st.button("Upload to TikTok"):
                upload_video_tiktok(script="", final_video=temp_path)




def main():
    st.sidebar.title("📚 Navigation")
    pages = {
        "Dashboard": dashboard_page,
        "CSV Processing": page_csv_processing,
        "Full Video Creation": page_full_video_generation,
        "Script Generation": page_script_generation,
        "Voice Generation": page_voice_generation,
        "Subtitles on Video": page_subtitling,
        "Quick Edit": page_quick_edit,
        "Upload Video": page_separate_uploader,
        "TikTok Login": page_tiktok_login,
    }
    choice = st.sidebar.radio("", list(pages.keys()))
    pages[choice]()

if __name__ == "__main__":
    main()

