# ⚡ CYBERDEN

```text
 ██████╗██╗   ██╗██████╗ ███████╗██████╗ ██████╗ ███████╗███╗   ██╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝████╗  ██║
██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝██║  ██║█████╗  ██╔██╗ ██║
██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗██║  ██║██╔══╝  ██║╚██╗██║
╚██████╗   ██║   ██║  ██║███████╗██║  ██║██████╔╝███████╗██║ ╚████║
 ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝
```

> **A cyberpunk terminal UI for running local LLMs with Ollama.**

CYBERDEN is a fast, keyboard-driven **Python Textual application** for running and managing local AI models directly from your terminal.

It combines a futuristic cyberpunk interface with practical local-AI features such as persistent conversations, model management, GPU telemetry, vision input, download progress, prompt queues, and more.

---

## ✨ Features

### 🧠 Local AI

- Run local LLMs through **Ollama**
- Switch between installed models
- Persistent default model
- Reasoning mode support
- Prompt history
- Prompt queue while a model is generating
- Unload models from VRAM when finished

### 💬 Chat & Sessions

- Persistent chat sessions
- Automatically save conversations locally
- Create, reset, and delete sessions
- Export conversations
- Browse previous prompts with `↑` / `↓`
- Clear the current workspace instantly

### 🖼️ Vision & Image Input

Use compatible Ollama vision models to analyze images directly from CYBERDEN.

Images can be added through:

- `Ctrl + V`
- `/paste`
- `/clip`
- **📋 Paste Img** button
- Drag and drop

Attachments are stored locally in:

```text
attachments/
```

Compatible models may include:

- `llava`
- `qwen2.5-vl`
- `gemma4`

> Vision support depends on whether the selected Ollama model supports image input.

### 📊 Hardware Telemetry

CYBERDEN provides real-time hardware monitoring while you work.

#### NVIDIA

- GPU utilization
- VRAM usage
- GPU temperature

Powered by `pynvml`.

#### Intel

Supports telemetry for hardware such as:

- Intel Iris Xe
- Intel Arc

Information is collected through Linux DRM/sysfs interfaces.

#### System

- CPU utilization
- RAM usage

Powered by `psutil`.

### 📥 Model Download HUD

When downloading models through Ollama, CYBERDEN provides a live progress display including:

- Download progress
- Download speed
- Downloaded size
- Total size
- Estimated time remaining

### ⚡ Cyberpunk Terminal UI

Built with **Textual** for a modern terminal-native experience.

CYBERDEN is designed to stay keyboard-first while providing a visually rich interface for local AI workflows.

---

# 🛠️ Requirements

## Software

- **Python 3.10+**
- **Ollama**
- Linux recommended
- A terminal with Unicode/ANSI support

For image clipboard support, install the appropriate clipboard utilities:

- `wl-clipboard` for Wayland
- `xclip` for X11

## Hardware

CYBERDEN itself does not require a dedicated GPU.

However, the performance of local LLMs depends heavily on your available CPU, RAM, VRAM, and the model you choose.

---

# 📦 Installation

## 1. Install Ollama

Install Ollama from:

https://ollama.com

Verify that it is available:

```bash
ollama --version
```

Start the Ollama server:

```bash
ollama serve
```

> Keep the Ollama server running while using CYBERDEN.

---

## 2. Clone CYBERDEN

```bash
git clone https://github.com/your-username/cyberden.git
cd cyberden
```

Replace `your-username/cyberden` with the actual repository URL.

---

## 3. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

### Linux / macOS

```bash
source venv/bin/activate
```

### Windows

```powershell
venv\Scripts\activate
```

---

## 4. Install dependencies

```bash
pip install textual httpx psutil pynvml pillow
```

Or, if the repository includes `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

# 🐧 Linux Dependencies

## Arch Linux / CachyOS / Manjaro

```bash
sudo pacman -S --needed wl-clipboard xclip python-pillow
```

## Ubuntu / Debian

```bash
sudo apt install wl-clipboard xclip python3-pil
```

You only need the clipboard utility that matches your environment, although installing both is fine.

---

# 🚀 Running CYBERDEN

Start Ollama:

```bash
ollama serve
```

Then launch CYBERDEN:

```bash
python app.py
```

You should now be dropped into the CYBERDEN terminal interface.

---

# 🤖 Models

CYBERDEN works with compatible models available through Ollama.

For example:

```bash
ollama pull llama3.2
ollama pull qwen2.5
ollama pull qwen2.5-vl
ollama pull gemma4
```

List installed models:

```bash
ollama list
```

You can then select an installed model from inside CYBERDEN.

> Model names and availability depend on the current Ollama model registry.

---

# 🎮 Keybindings

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

---

# 💬 Slash Commands

CYBERDEN provides quick actions through slash commands.

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

---

# 🖼️ Image Input

CYBERDEN can stage images for models that support vision.

### Clipboard

Use:

```text
Ctrl + V
```

or:

```text
/paste
```

or:

```text
/clip
```

You can also use the **📋 Paste Img** interface button.

### Drag & Drop

Images can be dragged directly into the application when supported by the terminal environment.

### Removing an Image

Use:

```text
/clearimage
```

or:

```text
/detach
```

Images are stored locally:

```text
attachments/
```

---

# 💾 Sessions

CYBERDEN automatically stores conversations locally so you can continue your work later.

A typical project structure looks like:

```text
saved_chats/
├── session.json
├── session.md
└── ...
```

Sessions can be:

- Created
- Reset
- Deleted
- Exported
- Automatically persisted

Configuration is stored in:

```text
~/.cynosure_config.json
```

> Do not commit personal session data, attachments, or local configuration files to your public repository.

Consider adding them to `.gitignore`:

```gitignore
venv/
__pycache__/
*.pyc

saved_chats/
attachments/

.cynosure_config.json
```

---

# 📊 Hardware Telemetry

CYBERDEN can display hardware information while generating responses.

### NVIDIA

Telemetry is provided through `pynvml` and can include:

```text
GPU Usage
VRAM Usage
GPU Temperature
```

### Intel

Linux DRM/sysfs information can be used to expose information from supported Intel GPUs, including:

```text
Intel Iris Xe
Intel Arc
```

### System

System statistics are provided through `psutil`:

```text
CPU Usage
RAM Usage
```

---

# 🧩 Project Structure

```text
cyberden/
│
├── app.py
├── README.md
├── LICENSE
├── requirements.txt
│
├── saved_chats/
│   └── ...
│
└── attachments/
    └── ...
```

The runtime-generated directories should generally remain outside version control.

---

# 🏗️ Tech Stack

CYBERDEN is built around a small set of lightweight technologies:

| Technology | Purpose |
|---|---|
| Python | Application runtime |
| Textual | Terminal UI |
| Ollama | Local LLM inference |
| HTTPX | HTTP/API communication |
| psutil | CPU & RAM telemetry |
| pynvml | NVIDIA GPU telemetry |
| Pillow | Image processing |

---

# 🔧 Troubleshooting

## Ollama is not responding

Make sure Ollama is running:

```bash
ollama serve
```

Then verify:

```bash
ollama list
```

---

## No models are available

Pull a model first:

```bash
ollama pull llama3.2
```

Then check:

```bash
ollama list
```

---

## Clipboard paste does not work

On Linux, make sure the appropriate clipboard package is installed.

### Wayland

```bash
sudo pacman -S wl-clipboard
```

or:

```bash
sudo apt install wl-clipboard
```

### X11

```bash
sudo pacman -S xclip
```

or:

```bash
sudo apt install xclip
```

---

## NVIDIA telemetry is unavailable

Make sure your NVIDIA drivers are working correctly and that `pynvml` is installed:

```bash
pip install pynvml
```

You can test NVIDIA GPU availability with:

```bash
nvidia-smi
```

---

# 🛡️ Privacy

CYBERDEN is designed around local AI.

Your prompts are sent to your local Ollama instance rather than a remote AI API, assuming your Ollama configuration itself is local.

Chat sessions and image attachments are stored locally on your machine.

Check the project's source code and Ollama configuration to understand exactly what data is processed in your environment.

---

# 🤝 Contributing

Contributions, bug reports, ideas, and improvements are welcome.

A typical workflow:

```bash
git clone https://github.com/your-username/cyberden.git
cd cyberden

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

Then make your changes, test them locally, and open a pull request.

### Ideas for future improvements

- [ ] Model search and filtering
- [ ] Better model metadata
- [ ] Multi-model conversations
- [ ] Token/response statistics
- [ ] Custom themes
- [ ] Configurable keybindings
- [ ] Conversation search
- [ ] Model presets
- [ ] Better cross-platform clipboard support
- [ ] Remote Ollama server support
- [ ] Plugin architecture
- [ ] Additional GPU telemetry

---

# ⚡ Why CYBERDEN?

Local AI does not have to feel like a collection of shell commands.

CYBERDEN aims to provide a focused environment where you can:

```text
    ┌─────────────────────────────────────────┐
    │                                         │
    │        LOCAL MODELS                     │
    │              ↓                          │
    │        ┌───────────┐                    │
    │        │  OLLAMA   │                    │
    │        └─────┬─────┘                    │
    │              ↓                          │
    │        ┌───────────┐                    │
    │        │ CYBERDEN  │                    │
    │        │    TUI    │                    │
    │        └─────┬─────┘                    │
    │              ↓                          │
    │      CHAT • VISION • GPU               │
    │      SESSIONS • QUEUES                  │
    │      MODELS • TELEMETRY                 │
    │                                         │
    └─────────────────────────────────────────┘
```

**No cloud required. No browser required. Just your terminal and your models.**

---

# 🤖 Vibe Coded

CYBERDEN was **vibe coded**.

Built through AI-assisted development, experimentation, iteration, debugging, refactoring, and a healthy amount of terminal chaos.

> **Built for the vibes. Powered locally. ⚡**

---

# 📜 License

CYBERDEN is released under the **MIT License**.

See [`LICENSE`](LICENSE) for the full license text.

---

<p align="center">

**⚡ CYBERDEN**

*Local AI. Terminal Power. Cyberpunk Energy.*

</p>
