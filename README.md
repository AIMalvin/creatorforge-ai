# CreatorForge AI

> **CreatorForge AI** is an end‑to‑end, AI‑powered content factory that lets you turn a one‑line idea into a fully‑edited, subtitle‑ready vertical video—then publish it directly to YouTube Shorts and TikTok, all from a friendly Streamlit dashboard.

![Streamlit](https://img.shields.io/badge/Built_with-Streamlit-fc4c02?logo=streamlit) 
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python) 
![License](https://img.shields.io/github/license/your‑org/CreatorForgeAI)

---

## ✨ Features
- **Multi‑page Streamlit UI** with intuitive navigation
- **LLM‑driven script & metadata generation** (title, description, tags)
- **Neural TTS voice‑over** generation
- **Auto‑sourced stock footage** montage matching the topic
- **One‑click assembly & subtitle burn‑in**
- **Batch CSV mode** for processing dozens of ideas hands‑free
- **Direct upload** to *YouTube Shorts* (via YouTube Data API) and *TikTok* (via cookie‑based Selenium automation)
- **Dashboard** for browsing and downloading generated assets
- “**Quick Edit**” shortcut: drop in text → get a synced voice‑over & background video in seconds

<p align="center">
  <img src="docs/preview.gif" width="480" alt="CreatorForge AI demo"/>
</p>

---

## 🗂️ Project layout
```
.
├── app.py                 # Streamlit entry‑point
├── scripts/               # Core pipeline building blocks
│   ├── generate_scripts.py
│   ├── generate_voice.py
│   ├── get_footage.py
│   ├── edit_video.py
│   ├── generate_subtitles.py
│   └── upload.py
├── assets/
│   ├── data/prompts.csv   # Ideas queue for batch mode
│   └── texts/…            # Generated text assets
├── exports/               # Output videos & intermediates
├── config/
│   └── tiktok_cookies.json
└── requirements.txt
```

---

## ⚙️ Installation

### 1. Clone and enter the repo
```bash
git clone https://github.com/your‑org/CreatorForgeAI.git
cd CreatorForgeAI
```

### 2. Create a virtualenv & install Python deps
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### 3. Install system packages
| Tool      | macOS                            | Ubuntu / Debian               | Windows                              |
|-----------|----------------------------------|--------------------------------|--------------------------------------|
| **FFmpeg**| `brew install ffmpeg`            | `sudo apt install ffmpeg`      | [Download zip](https://ffmpeg.org/)  |
| **Chromium** (optional) | – | `sudo apt install chromium-browser` | Edge/Chrome already bundles driver   |

### 4. Add your API keys

Create `.env` at the repo root:

```env
OPENAI_API_KEY=sk‑…
YOUTUBE_API_KEY=AIza…
# ElevenLabs or other TTS keys
TTS_API_KEY=…
```

> *Tip:* The app will automatically pick up the environment variables on launch.

---

## 🚀 Running the app
```bash
streamlit run app.py
```
Your browser will open at `http://localhost:8501`.

---

## 🗺️ Using CreatorForge AI

| Page | What it does |
|------|--------------|
| **Dashboard** | Browse previous exports, preview files, download ZIPs |
| **CSV Processing** | Batch‑process ideas from `assets/data/prompts.csv` |
| **Full Video Creation** | Enter a topic → full pipeline → optional upload |
| **Script Generation** | Get script, title, description & tags only |
| **Voice Generation** | Generate and download just the voice‑over |
| **Subtitles on Video** | Burn subtitles onto any existing MP4 |
| **Quick Edit** | Fast audio + background montage |
| **Upload Video** | Upload any MP4 to YouTube Shorts / TikTok |
| **TikTok Login** | Store login cookies for automated posting |

Detailed walkthroughs for every page live in **[`docs/usage.md`](docs/usage.md)**.

---

## 🧩 Extending the pipeline
- Swap `generate_voice.py` for your favourite TTS provider
- Replace `get_footage.py` with a custom stock‑footage service
- Add new upload targets (Instagram Reels, Facebook, etc.)
- Connect Supabase or Firestore for prompt queues

---

## 🗒️ Roadmap
- [ ] Multi‑language subtitle support  
- [ ] Docker container for headless deployment  
- [ ] Built‑in analytics for published videos  
- [ ] Template system for different video styles  

---

## 🤝 Contributing
1. Fork the repo & create a branch
2. Make your changes (+ tests!)
3. Open a PR describing **what** & **why**

See `CONTRIBUTING.md` for linting & commit guidelines.

---

## 🛡️ License
Released under the **MIT License** — see [`LICENSE`](LICENSE) for details.

---

## 🙏 Acknowledgements
- The Streamlit team for the awesome UI framework
- OpenAI for the language & voice models
- The community behind `moviepy`, `yt‑dlp`, and other open‑source libraries

