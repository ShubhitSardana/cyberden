# ⚡ CYBERDEN

```text
 ██████╗██╗   ██╗██████╗ ███████╗██████╗ ██████╗ ███████╗███╗   ██╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝████╗  ██║
██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝██║  ██║█████╗  ██╔██╗ ██║
██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗██║  ██║██╔══╝  ██║╚██╗██║
╚██████╗   ██║   ██║  ██║███████╗██║  ██║██████╔╝███████╗██║ ╚████║
 ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝
```

> A cyberpunk terminal UI for running local LLMs with Ollama.

CYBERDEN is a Python **Textual** application for running and managing local AI models directly from the terminal.

## ✨ Features

- ⚡ Cyberpunk terminal UI
- 🧠 Local LLMs through Ollama
- 🖼️ Image input for vision models
- 📊 NVIDIA / Intel GPU telemetry
- 💻 CPU & RAM monitoring
- 📥 Model download progress
- 📋 Prompt queue while generating
- 💾 Persistent chat sessions
- 📌 Persistent default model
- 🔄 Prompt history
- 🗑️ Session management
- ⏏️ Model VRAM unloading

## 🛠️ Requirements

- Python **3.10+**
- [Ollama](https://ollama.com)
- Linux recommended
- `wl-clipboard` for Wayland clipboard support
- `xclip` for X11 clipboard support

### Arch Linux / CachyOS / Manjaro

```bash
sudo pacman -S --needed wl-clipboard xclip python-pillow
```

### Ubuntu / Debian

```bash
sudo apt install wl-clipboard xclip python3-pil
```

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/cyberden.git
cd cyberden
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install textual httpx psutil pynvml pillow
```

### 4. Start Ollama

```bash
ollama serve
```

### 5. Launch CYBERDEN

```bash
python app.py
```

## 📦 Models

CYBERDEN works with any compatible model available through Ollama.

Example models:

```bash
ollama pull llama3.2
ollama pull qwen2.5
ollama pull qwen2.5-vl
ollama pull gemma4
```

Check installed models:

```bash
ollama list
```

## 🎮 Keybindings

| Key | Action |
|---|---|
| `Ctrl + Q` | Exit CYBERDEN |
| `Ctrl + V` | Paste image |
| `Ctrl + N` | Start a new session |
| `Ctrl + S` | Export current chat |
| `Ctrl + L` | Clear workspace |
| `Ctrl + R` | Refresh model registry |
| `Ctrl + U` | Unload active model |
| `Escape` | Stop generation |
| `↑ / ↓` | Browse prompt history |

## 💬 Slash Commands

| Command | Action |
|---|---|
| `/paste` | Paste image from clipboard |
| `/clip` | Paste image from clipboard |
| `/clearimage` | Remove staged image |
| `/detach` | Remove staged image |
| `/clearqueue` | Clear prompt queue |
| `/cq` | Clear prompt queue |
| `/default` | Set active model as default |
| `/new` | Start a new session |
| `/reset` | Start a new session |
| `/delete` | Delete current session |
| `/del` | Delete current session |
| `/unload` | Unload active model |
| `/eject` | Unload active model |
| `/think` | Enable reasoning |
| `/nothink` | Disable reasoning |
| `/export` | Export current chat |

## 📊 Hardware Telemetry

CYBERDEN provides real-time system monitoring.

### NVIDIA

- GPU utilization
- VRAM usage
- GPU temperature

Powered by `pynvml`.

### Intel

- Intel Iris Xe
- Intel Arc
- GPU information through Linux DRM sysfs

### System

- CPU utilization
- RAM usage

Powered by `psutil`.

## 🖼️ Image Support

CYBERDEN supports image input for compatible Ollama vision models.

Images can be added through:

- `Ctrl + V`
- `/paste`
- `/clip`
- `📋 Paste Img`
- Drag and drop

Compatible models may include:

- `llava`
- `qwen2.5-vl`
- `gemma4`

Images are stored locally in:

```text
attachments/
```

## 📥 Model Downloads

CYBERDEN provides a download HUD when pulling models through Ollama.

It displays:

- Download progress
- Download speed
- Downloaded size
- Total size
- ETA

## 💾 Sessions

Conversations are automatically saved locally.

```text
saved_chats/
├── session.json
├── session.md
└── ...
```

Configuration is stored at:

```text
~/.cynosure_config.json
```

## 📂 Project Structure

```text
cyberden/
├── app.py
├── saved_chats/
├── attachments/
├── README.md
└── requirements.txt
```

## 🤖 Vibe Coded

CYBERDEN was **vibe coded**.

Built through AI-assisted development, experimentation, iteration, debugging, and a lot of terminal chaos.

> Built for the vibes. Powered locally. ⚡

## 📜 License

MIT License

See the `LICENSE` file for details.
```
