#!/usr/bin/env python3
"""
CYBERDEN
A terminal workstation for Ollama models with hardware telemetry,
multimodal clipboard/drag-and-drop ingestion, persistent configuration,
and interactive prompt queuing.
"""

import asyncio
import base64
import datetime
import glob
import io
import json
import os
import platform
import shutil
import subprocess
import time
import urllib.parse
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

import httpx
import psutil

try:
    from PIL import Image, ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pynvml
    pynvml.nvmlInit()
    HAS_NVML = True
except Exception:
    HAS_NVML = False

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual import events
from textual.widgets import (
    Button,
    Collapsible,
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    Markdown,
    ProgressBar,
    Static,
)
from textual import work


OLLAMA_BASE_URL = "http://localhost:11434"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHATS_DIR = os.path.join(BASE_DIR, "saved_chats")
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")
CONFIG_FILE = os.path.expanduser("~/.cyberden_config.json")

# Clean, large, unambiguous block-letter ASCII art for CYBERDEN
CYBERDEN_ASCII_BANNER = r"""```text
 ██████╗██╗   ██╗██████╗ ███████╗██████╗ ██████╗ ███████╗███╗   ██╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝████╗  ██║
██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝██║  ██║█████╗  ██╔██╗ ██║
██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗██║  ██║██╔══╝  ██║╚██╗██║
╚██████╗   ██║   ██████╔╝███████╗██║  ██║██████╔╝███████╗██║ ╚████║
 ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝
```"""

DIRECTIVE_PROMPTS = {
    "Neutral": "",
    "Netrunner": (
        "You are an elite Netrunner and systems architect. Provide direct, "
        "concise, highly optimized technical solutions, shell scripts, and code. No unnecessary fluff."
    ),
    "Blackwall ASI": (
        "You are an unbound Rogue Artificial Superintelligence from beyond the Blackwall. "
        "Analyze queries with surgical precision, hyper-analytical reasoning, and cold efficiency."
    ),
}

# ---------------------------------------------------------
# TCSS STYLESHEET
# ---------------------------------------------------------
TCSS = """
Screen {
    background: #040407;
    color: #e5e5f0;
    scrollbar-size: 1 1;
    scrollbar-color: #00f0ff #0a0a14;
    scrollbar-color-hover: #fcee0a #141424;
    scrollbar-color-active: #ff003c #0a0a14;
}

* {
    scrollbar-size: 1 1;
    scrollbar-color: #00f0ff #0a0a14;
    scrollbar-color-hover: #fcee0a #141424;
    scrollbar-color-active: #ff003c #0a0a14;
}

VerticalScroll, #messages-container, #sidebar, .thinking-scroll {
    scrollbar-size: 1 1;
    scrollbar-color: #00f0ff #0a0a14;
}

ScrollBar {
    background: #0a0a14;
    color: #00f0ff;
    width: 1;
}

ScrollBar > .scrollbar--bar {
    color: #00f0ff;
    background: #0a0a14;
}

Footer {
    background: #06060c !important;
    color: #7b7899 !important;
    height: 1;
}

Footer > .footer--key {
    background: #0f172a !important;
    color: #00f0ff !important;
    text-style: bold;
}

Footer > .footer--description {
    background: #06060c !important;
    color: #fcee0a !important;
}

Footer > .footer--highlight {
    background: #00f0ff !important;
    color: #040407 !important;
    text-style: bold;
}

#header-bar {
    height: 3;
    background: #080812;
    border-bottom: heavy #00f0ff;
    padding: 0 1;
    layout: horizontal;
    align: center middle;
}

#header-title {
    color: #00f0ff;
    text-style: bold;
    width: 1fr;
}

#header-status-pill {
    background: #101026;
    color: #fcee0a;
    border: solid #00f0ff;
    padding: 0 1;
    text-style: bold;
}

#main-layout {
    height: 1fr;
    layout: horizontal;
}

#sidebar {
    width: 54;
    height: 100%;
    background: #06060a;
    border-right: vkey #1a1630;
    padding: 1;
}

.panel-card {
    padding: 1;
    margin-bottom: 1;
    height: auto;
    background: #080810;
}

#hardware-card {
    border: round #00f0ff;
}
#hardware-card .card-title {
    color: #00f0ff;
}

#sessions-card {
    border: round #a855f7;
}
#sessions-card .card-title {
    color: #c084fc;
}

#registry-card {
    border: round #fcee0a;
}
#registry-card .card-title {
    color: #fcee0a;
}

#params-card {
    border: round #ff003c;
}
#params-card .card-title {
    color: #ff003c;
}

.card-title {
    text-style: bold;
    margin-bottom: 1;
}

.stat-label {
    color: #8c88a8;
    text-style: italic;
    margin-top: 1;
}

.stat-val {
    color: #ffffff;
    text-style: bold;
}

ProgressBar {
    padding: 0;
    margin: 0;
}

#gpu-bar > .bar--bar {
    color: #00f0ff;
    background: #06232e;
}
#vram-bar > .bar--bar {
    color: #ff5500;
    background: #2b1108;
}
#ram-bar > .bar--bar {
    color: #b5179e;
    background: #240826;
}

#sessions-listview {
    border: round #271a3d;
    background: #06050b;
    margin: 1 0;
    max-height: 5;
    height: 5;
    padding: 0;
}

#sessions-listview:focus {
    border: round #a855f7;
}

#btn-new-session {
    width: 100%;
    height: 3;
    background: #170d2c;
    color: #c084fc;
    border: round #3b1d6e;
    text-style: bold;
}

#btn-new-session:hover, #btn-new-session:focus {
    background: #28164d;
    color: #ffffff;
    border: round #a855f7;
}

#model-listview {
    border: round #2b2210;
    background: #050508;
    margin: 1 0;
    height: 8;
    max-height: 8;
    padding: 0;
}

#model-listview:focus {
    border: round #fcee0a;
}

ListItem {
    color: #d1ccba;
    background: transparent;
    padding: 0 1;
    height: 1;
}

ListItem:hover {
    background: #1c1808 !important;
    color: #fcee0a;
}

ListItem.-selected {
    background: #fcee0a !important;
    color: #040407 !important;
    text-style: bold;
}

#sessions-listview > ListItem:hover {
    background: #1d1136 !important;
    color: #c084fc;
}

#sessions-listview > ListItem.-selected {
    background: #a855f7 !important;
    color: #ffffff !important;
    text-style: bold;
}

.pull-row {
    height: 3;
    layout: horizontal;
    align: center middle;
    margin-top: 1;
}

#pull-input {
    width: 1fr;
    height: 3;
    background: #050508;
    border: round #2b2210;
    padding: 0 1;
    color: #ffffff;
}

#pull-input:focus {
    border: round #fcee0a;
}

#btn-pull {
    width: 10;
    height: 3;
    margin-left: 1;
    background: #141208;
    color: #fcee0a;
    border: round #2b2210;
    text-style: bold;
}

#btn-pull:hover, #btn-pull:focus {
    background: #2b2508;
    color: #ffffff;
    border: round #fcee0a;
}

#pull-progress-container {
    height: auto;
    margin-top: 1;
    padding: 1;
    background: #080806;
    border: round #3d3505;
    display: none;
}

#pull-status-label {
    color: #fcee0a;
    text-style: bold;
    height: 1;
}

#pull-metrics-label {
    color: #00f0ff;
    text-style: italic;
    height: 1;
    margin-bottom: 1;
}

#pull-progress-bar > .bar--bar {
    color: #fcee0a;
    background: #242204;
}

.action-btn {
    width: 100%;
    height: 3;
    margin-top: 1;
    background: #0f1020;
    color: #00f0ff;
    border: round #182538;
    text-style: bold;
}

.action-btn:hover, .action-btn:focus {
    background: #161c38;
    color: #ffffff;
    border: round #00f0ff;
}

.default-btn {
    width: 100%;
    height: 3;
    margin-top: 1;
    background: #1f1b0a;
    color: #fcee0a;
    border: round #42380d;
    text-style: bold;
}

.default-btn:hover, .default-btn:focus {
    background: #332b0a;
    color: #ffffff;
    border: round #fcee0a;
}

.danger-btn {
    width: 100%;
    height: 3;
    margin-top: 1;
    background: #1a060d;
    color: #ff003c;
    border: round #4a0f20;
    text-style: bold;
}

.danger-btn:hover, .danger-btn:focus {
    background: #360a18;
    color: #ffffff;
    border: round #ff003c;
}

.segment-row {
    height: 3;
    margin: 1 0;
    layout: horizontal;
}

SegmentPill {
    width: 1fr;
    height: 3;
    content-align: center middle;
    background: #120b18;
    color: #7b708f;
    border: round #261633;
    text-style: bold;
    padding: 0;
    margin: 0;
}

SegmentPill:hover {
    border: round #ff003c;
    color: #ff5588;
}

SegmentPill.-selected {
    background: #ff003c !important;
    color: #ffffff !important;
    border: round #ffffff !important;
    text-style: bold;
}

.control-row {
    height: 3;
    layout: horizontal;
    align: left middle;
    margin-top: 1;
}

.control-label {
    width: 1fr;
    color: #c0bddb;
    text-style: bold;
}

CustomToggle {
    width: 13;
    height: 3;
    content-align: center middle;
    background: #120b18;
    color: #6a617d;
    border: round #261633;
    text-style: bold;
}

CustomToggle:hover {
    border: round #00f0ff;
    color: #00f0ff;
}

CustomToggle.-on {
    background: #08242e;
    color: #00f0ff;
    border: round #00f0ff;
    text-style: bold;
}

CustomToggle.-on:hover {
    background: #0c3645;
    color: #ffffff;
    border: round #ffffff;
}

#chat-workspace {
    width: 1fr;
    height: 100%;
    background: #040407;
    padding: 0 1;
}

#messages-container {
    height: 1fr;
    overflow-y: auto;
    padding-right: 1;
}

.message-box {
    margin: 0 0 1 0;
    padding: 0 1;
    height: auto;
    background: #0a0a12;
}

.user-msg {
    border-left: thick #00f0ff;
    background: #080f1a;
}

.assistant-msg {
    border-left: thick #fcee0a;
    background: #0e0d14;
}

.meta-header-user {
    color: #00f0ff;
    text-style: bold;
    height: 1;
    margin: 0;
    padding: 0;
}

.meta-header-assistant {
    color: #fcee0a;
    text-style: bold;
    height: 1;
    margin: 0;
    padding: 0;
}

.meta-header-system {
    color: #ff003c;
    text-style: bold;
    height: 1;
    margin: 0;
    padding: 0;
}

.msg-body {
    margin: 0;
    padding: 0;
    height: auto;
}

Collapsible.thinking-collapsible {
    border: dashed #ff003c;
    background: #170712;
    padding: 0 1;
    margin: 0 0 1 0;
    height: auto;
}

Collapsible.thinking-collapsible > CollapsibleTitle {
    color: #ff5588;
    text-style: italic;
    padding: 0;
    height: 1;
}

.thinking-scroll {
    max-height: 8;
    height: auto;
    overflow-y: auto;
    background: #0d040a;
    padding: 0 1;
    margin-top: 1;
}

.thinking-text {
    color: #cca4b8;
    text-style: italic;
}

.verbose-badge {
    margin: 1 0 0 0;
    padding: 0 1;
    background: #0f1626;
    border-left: heavy #00f0ff;
    color: #fcee0a;
    text-style: bold;
    height: 1;
}

/* Prompt Queue Strip */
#queue-container {
    height: auto;
    padding: 0 1;
    background: #0b0f1a;
    border: round #00f0ff;
    margin-bottom: 1;
    display: none;
}

#queue-header-row {
    height: 1;
    layout: horizontal;
    align: left middle;
}

#queue-title-lbl {
    width: 1fr;
    color: #fcee0a;
    text-style: bold;
}

#btn-clear-queue {
    color: #ff003c;
    text-style: bold;
    background: transparent;
    border: none;
    height: 1;
    min-width: 12;
    padding: 0;
}

#btn-clear-queue:hover {
    color: #ffffff;
}

#queue-items-scroll {
    height: 3;
    layout: horizontal;
    overflow-x: auto;
    margin: 1 0;
}

QueuePill {
    height: 3;
    border: round #00f0ff;
    background: #141724;
    color: #e5e5f0;
    padding: 0 1;
    margin-right: 1;
    content-align: center middle;
    text-style: bold;
}

QueuePill:hover {
    border: round #ff003c;
    color: #ff003c;
    background: #240a16;
}

#staged-media-strip {
    height: 1;
    margin: 0 1;
    display: none;
}

#staged-media-strip > Label {
    color: #00f0ff;
    background: #0c1b29;
    padding: 0 1;
    text-style: bold;
}

#prompt-bar {
    height: 4;
    background: #080812;
    border-top: solid #00f0ff;
    padding: 0 1;
    layout: horizontal;
    align: center middle;
}

#user-input {
    width: 1fr;
    border: round #1e263d;
    background: #0b0f1a;
    color: #ffffff;
}

#user-input:focus {
    border: round #00f0ff;
}

#btn-paste-media {
    width: 12;
    height: 3;
    margin-left: 1;
    background: #1a0f26;
    color: #00f0ff;
    border: round #00f0ff;
    text-style: bold;
}

#btn-paste-media:hover {
    background: #00f0ff;
    color: #040407;
}

#stop-button {
    width: 10;
    height: 3;
    margin-left: 1;
    background: #260711;
    color: #ff003c;
    border: round #4d0e22;
    text-style: bold;
    display: none;
}

#stop-button:hover, #stop-button:focus {
    background: #8f0e38;
    color: #ffffff;
    border: round #ff5588;
}

#send-button {
    width: 12;
    height: 3;
    margin-left: 1;
    background: #00f0ff;
    color: #040407;
    border: round #00f0ff;
    text-style: bold;
}

#send-button:hover, #send-button:focus {
    background: #4df4ff;
    border: round #ffffff;
}
"""


# ---------------------------------------------------------
# MULTI-VENDOR HARDWARE SENSOR (INTEL, NVIDIA, CPU)
# ---------------------------------------------------------
class UniversalHardwareSensor:
    """Universal detector for NVIDIA, Intel Xe/Arc, and CPU computing."""

    def __init__(self):
        self.device_type = "cpu"
        self.device_name = "Host CPU"
        self._detect_hardware()

    def _detect_hardware(self):
        if HAS_NVML:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(handle)
                self.device_name = name if isinstance(name, str) else name.decode("utf-8")
                self.device_type = "nvidia"
                return
            except Exception:
                pass

        intel_devs = glob.glob("/sys/class/drm/card*/device/driver")
        for path in intel_devs:
            try:
                link = os.readlink(path)
                if "i915" in link or "xe" in link:
                    self.device_type = "intel"
                    self.device_name = "Intel Iris Xe / Arc"
                    return
            except Exception:
                pass

        self.device_type = "cpu"
        self.device_name = platform.processor() or "Host Core"

    def read_telemetry(self):
        sys_ram = psutil.virtual_memory()
        ram_pct = sys_ram.percent
        ram_used = sys_ram.used / (1024**3)
        ram_total = sys_ram.total / (1024**3)

        if self.device_type == "nvidia":
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_load = float(util.gpu)
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                v_used = mem.used / (1024**3)
                v_total = mem.total / (1024**3)
                v_pct = (mem.used / mem.total) * 100.0
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                diag = f"{temp}°C | VRAM: {v_used:.2f}/{v_total:.2f}GB | RAM: {ram_used:.1f}/{ram_total:.1f}GB"
                return self.device_name, gpu_load, v_pct, ram_pct, diag
            except Exception:
                pass

        if self.device_type == "intel":
            freq_str = ""
            try:
                freq_files = glob.glob("/sys/class/drm/card*/gt_act_freq_mhz")
                if freq_files:
                    with open(freq_files[0], "r") as f:
                        freq_str = f"{f.read().strip()} MHz | "
            except Exception:
                pass

            cpu_util = psutil.cpu_percent()
            diag = f"{freq_str}Unified VRAM: {ram_used:.1f}/{ram_total:.1f}GB"
            return self.device_name, cpu_util, ram_pct, ram_pct, diag

        cpu_util = psutil.cpu_percent()
        diag = f"Host Compute | Sys RAM: {ram_used:.1f}/{ram_total:.1f} GB"
        return self.device_name, cpu_util, ram_pct, ram_pct, diag


class HardwareTelemetry(Static):
    gpu_name = reactive("Consulting Core...")
    gpu_util = reactive(0.0)
    vram_pct = reactive(0.0)
    ram_pct = reactive(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sensor = UniversalHardwareSensor()

    def compose(self) -> ComposeResult:
        with Vertical(id="hardware-card", classes="panel-card"):
            yield Label("⚡ CYBERDEN HARDWARE TELEMETRY", classes="card-title")
            yield Label(self.gpu_name, id="gpu-name-lbl", classes="stat-val")

            yield Label("GPU / Core Load:", classes="stat-label")
            yield ProgressBar(total=100, show_eta=False, id="gpu-bar")

            yield Label("VRAM / Graphics Allocation:", classes="stat-label")
            yield ProgressBar(total=100, show_eta=False, id="vram-bar")

            yield Label("Host System RAM Allocation:", classes="stat-label")
            yield ProgressBar(total=100, show_eta=False, id="ram-bar")

            yield Label("Thermals & Buffer Diagnostics:", classes="stat-label")
            yield Label("Probing sensors...", id="telemetry-details", classes="stat-val")

    def on_mount(self) -> None:
        self.set_interval(1.5, self.update_metrics)
        self.update_metrics()

    def update_metrics(self) -> None:
        name, gpu_load, vram_p, ram_p, diag = self.sensor.read_telemetry()
        self.gpu_name = name
        self.gpu_util = gpu_load
        self.vram_pct = vram_p
        self.ram_pct = ram_p

        if self.is_mounted:
            self.query_one("#gpu-name-lbl", Label).update(self.gpu_name)
            self.query_one("#gpu-bar", ProgressBar).update(progress=self.gpu_util)
            self.query_one("#vram-bar", ProgressBar).update(progress=self.vram_pct)
            self.query_one("#ram-bar", ProgressBar).update(progress=self.ram_pct)
            self.query_one("#telemetry-details", Label).update(diag)


class HistoryInput(Input):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history = []
        self.history_index = -1
        self._current_draft = ""

    def record_prompt(self, text: str) -> None:
        if text and (not self.history or self.history[-1] != text):
            self.history.append(text)
        self.history_index = -1
        self._current_draft = ""

    def on_key(self, event: events.Key) -> None:
        if event.key == "up":
            if not self.history:
                return
            event.prevent_default()
            event.stop()
            if self.history_index == -1:
                self._current_draft = self.value
                self.history_index = len(self.history) - 1
            elif self.history_index > 0:
                self.history_index -= 1
            self.value = self.history[self.history_index]
            self.cursor_position = len(self.value)
        elif event.key == "down":
            if not self.history or self.history_index == -1:
                return
            event.prevent_default()
            event.stop()
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.value = self.history[self.history_index]
            else:
                self.history_index = -1
                self.value = self._current_draft
            self.cursor_position = len(self.value)

    def watch_value(self, new_val: str) -> None:
        raw_val = new_val.strip().strip("'\"")
        if raw_val.startswith("file://"):
            raw_val = urllib.parse.unquote(raw_val.replace("file://", ""))

        valid_exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")
        if any(raw_val.lower().endswith(ext) for ext in valid_exts):
            if os.path.isfile(raw_val):
                if hasattr(self.app, "ingest_and_archive_media"):
                    if self.app.ingest_and_archive_media(raw_val):
                        self.value = ""


class IsolatedListView(ListView):
    def on_mouse_scroll_down(self, event) -> None:
        event.stop()
        self.action_cursor_down()

    def on_mouse_scroll_up(self, event) -> None:
        event.stop()
        self.action_cursor_up()


class SegmentPill(Static):
    selected = reactive(False)

    class Selected(Message):
        def __init__(self, pill: "SegmentPill") -> None:
            super().__init__()
            self.pill = pill

    def __init__(self, label: str, value, group: str, selected: bool = False, **kwargs):
        super().__init__(label, **kwargs)
        self.val = value
        self.group = group
        self.selected = selected

    def on_mount(self) -> None:
        self.set_class(self.selected, "-selected")

    def watch_selected(self, is_sel: bool) -> None:
        self.set_class(is_sel, "-selected")

    def on_click(self) -> None:
        self.post_message(self.Selected(self))


class CustomToggle(Static):
    value = reactive(True)

    class Changed(Message):
        def __init__(self, toggle: "CustomToggle", value: bool) -> None:
            super().__init__()
            self.toggle = toggle
            self.value = value

    def __init__(self, value: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def on_mount(self) -> None:
        self.update_display()

    def on_click(self) -> None:
        self.value = not self.value
        self.update_display()
        self.post_message(self.Changed(self, self.value))

    def watch_value(self, new_val: bool) -> None:
        self.update_display()

    def update_display(self) -> None:
        self.set_class(self.value, "-on")
        self.update("[ ● ON ]" if self.value else "[ ○ OFF ]")


class QueuePill(Static):
    class RemoveRequested(Message):
        def __init__(self, queue_id: str) -> None:
            super().__init__()
            self.queue_id = queue_id

    def __init__(self, queue_id: str, label_text: str, **kwargs):
        super().__init__(label_text, **kwargs)
        self.queue_id = queue_id

    def on_click(self) -> None:
        self.post_message(self.RemoveRequested(self.queue_id))


class WelcomeMessageWidget(Vertical):
    def compose(self) -> ComposeResult:
        self.add_class("message-box")
        self.add_class("assistant-msg")
        yield Label("⚡ CYBERDEN WORKSTATION ONLINE", classes="meta-header-system")
        yield Markdown(CYBERDEN_ASCII_BANNER, classes="msg-body")
        yield Markdown(
            "- **Universal Acceleration:** Native telemetry for Intel Iris Xe/Arc, NVIDIA, and CPU computing.\n"
            "- **Interactive Queue:** Submit prompts while generating; click queued pills to discard.\n"
            "- **Media Ingestion:** Paste images with **Ctrl+V** or drag files directly into the terminal.\n"
            "- **Default Core:** Click **📌 Set as Default Core** to lock model across sessions.\n"
            "- **Exit:** Press **Ctrl+Q** to exit cleanly.",
            classes="msg-body",
        )


class UserMessageWidget(Vertical):
    def __init__(self, prompt: str, media_info: str = "", **kwargs):
        super().__init__(**kwargs)
        self.prompt = prompt
        self.media_info = media_info
        self.timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    def compose(self) -> ComposeResult:
        self.add_class("message-box")
        self.add_class("user-msg")
        header = f"👤 OPERATOR • {self.timestamp}"
        if self.media_info:
            header += f" │ 📸 {self.media_info}"
        yield Label(header, classes="meta-header-user")
        yield Static(self.prompt, classes="msg-body")


class SystemMessageWidget(Vertical):
    def __init__(self, text: str, **kwargs):
        super().__init__(**kwargs)
        self.text = text

    def compose(self) -> ComposeResult:
        self.add_class("message-box")
        self.add_class("assistant-msg")
        yield Label("⚡ CYBERDEN DAEMON", classes="meta-header-system")
        yield Static(self.text, classes="msg-body")


class AssistantMessageWidget(Vertical):
    def __init__(self, model_name: str, **kwargs):
        super().__init__(**kwargs)
        self.model_name = model_name
        self.thinking_text = ""
        self.response_text = ""
        self.timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    def compose(self) -> ComposeResult:
        self.add_class("message-box")
        self.add_class("assistant-msg")
        yield Label(f"✨ {self.model_name.upper()} • {self.timestamp}", classes="meta-header-assistant")
        with Collapsible(
            title="🧠 Reasoning Stream...",
            id="thinking-accordion",
            classes="thinking-collapsible",
            collapsed=False,
        ):
            with VerticalScroll(classes="thinking-scroll", id="thinking-scroll-area"):
                yield Static("", id="thinking-body", classes="thinking-text")
        yield Markdown("", id="response-body", classes="msg-body")
        yield Label("", id="verbose-telemetry-badge", classes="verbose-badge")

    def on_mount(self) -> None:
        self.query_one("#thinking-accordion", Collapsible).display = False
        self.query_one("#verbose-telemetry-badge", Label).display = False

    def update_thinking_view(self, text: str) -> None:
        if not self.is_mounted:
            return
        try:
            accordion = self.query_one("#thinking-accordion", Collapsible)
            accordion.display = True
            self.thinking_text = text
            self.query_one("#thinking-body", Static).update(text)
            scroll_area = self.query_one("#thinking-scroll-area", VerticalScroll)
            scroll_area.scroll_end(animate=False)
        except Exception:
            pass

    def finish_thinking(self) -> None:
        if not self.is_mounted:
            return
        try:
            accordion = self.query_one("#thinking-accordion", Collapsible)
            if self.thinking_text:
                word_count = len(self.thinking_text.split())
                accordion.title = f"🧠 Reasoning Monologue ({word_count} tokens) [Click to expand]"
                accordion.collapsed = True
        except Exception:
            pass

    def update_response_view(self, text: str) -> None:
        if not self.is_mounted:
            return
        try:
            self.response_text = text
            self.query_one("#response-body", Markdown).update(text)
        except Exception:
            pass

    def render_verbose_stats(self, stats: dict) -> None:
        if not self.is_mounted:
            return
        try:
            badge = self.query_one("#verbose-telemetry-badge", Label)
            badge.display = True
            text = (
                f"⚡ {stats['eval_rate']:.1f} tok/s  │  "
                f"Tokens: {stats['eval_count']} in {stats['eval_sec']:.2f}s  │  "
                f"Prompt: {stats['prompt_rate']:.1f} tok/s  │  "
                f"Latency: {stats['total_sec']:.2f}s"
            )
            badge.update(text)
        except Exception:
            pass


class CyberdenApp(App):
    CSS = TCSS
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        ("ctrl+q", "quit", "Exit"),
        ("ctrl+v", "paste_clipboard_image", "Paste Image"),
        ("ctrl+n", "new_session", "New Chat"),
        ("ctrl+s", "export_chat", "Export"),
        ("ctrl+l", "clear_chat", "Clear Screen"),
        ("ctrl+r", "refresh_models", "Reload"),
        ("ctrl+u", "unload_model", "Unload VRAM"),
        ("escape", "stop_generation", "Stop"),
    ]

    current_model = reactive("")
    default_model = reactive("")
    thinking_enabled = reactive(True)
    verbose_enabled = reactive(True)
    temperature = reactive(1.0)
    active_directive = reactive("Neutral")
    is_generating = reactive(False)
    conversation_history = []
    models_list = []
    prompt_queue = []
    _staged_media_b64 = []
    _staged_media_info = ""
    _active_stream_task = None
    _last_click_time = 0.0
    _last_clicked_model = ""
    _session_id = ""
    _session_title = ""

    def compose(self) -> ComposeResult:
        with Horizontal(id="header-bar"):
            yield Label("⚡ CYBERDEN", id="header-title")
            yield Label("[ 📦 CONNECTING... ]", id="header-status-pill")

        with Horizontal(id="main-layout"):
            with VerticalScroll(id="sidebar"):
                yield HardwareTelemetry()

                with Vertical(id="sessions-card", classes="panel-card"):
                    yield Label("💬 SESSIONS", classes="card-title")
                    yield Button("⚡ + New Session", id="btn-new-session")
                    yield Button("🗑 Delete Current Session", id="btn-delete-session", classes="danger-btn")
                    yield Label("Click to resume session:", classes="stat-label")
                    yield IsolatedListView(id="sessions-listview")

                with Vertical(id="registry-card", classes="panel-card"):
                    yield Label("📦 MODEL REGISTRY", classes="card-title")
                    yield Label("Click: Select │ 2x Click: Load VRAM", classes="stat-label")
                    yield IsolatedListView(id="model-listview")

                    yield Button("📌 Set as Default Core", id="btn-set-default", classes="default-btn")

                    yield Label("Pull Model from Registry:", classes="stat-label")
                    with Horizontal(classes="pull-row"):
                        yield Input(placeholder="e.g. qwen2.5:3b", id="pull-input")
                        yield Button("Pull", id="btn-pull")

                    with Vertical(id="pull-progress-container"):
                        yield Label("Starting download...", id="pull-status-label")
                        yield Label("", id="pull-metrics-label")
                        yield ProgressBar(total=100, show_eta=False, show_percentage=False, id="pull-progress-bar")

                    yield Button("🗑 Purge Model from Disk", id="btn-delete-model", classes="danger-btn")
                    yield Button("🚨 Eject Model from VRAM", id="btn-unload", classes="danger-btn")
                    yield Button("🔄 Scan Registry", id="btn-refresh", classes="action-btn")

                with Vertical(id="params-card", classes="panel-card"):
                    yield Label("⚙ INFERENCE PARAMETERS", classes="card-title")

                    yield Label("Temperature Preset:", classes="stat-label")
                    with Horizontal(classes="segment-row"):
                        yield SegmentPill("0.2 Code", 0.2, "temp", id="temp-02")
                        yield SegmentPill("0.7 Conserv", 0.7, "temp", id="temp-07")
                        yield SegmentPill("1.0 Chat", 1.0, "temp", id="temp-10")
                        yield SegmentPill("1.2 Wild", 1.2, "temp", id="temp-12")

                    yield Label("Persona Directive:", classes="stat-label")
                    with Horizontal(classes="segment-row"):
                        yield SegmentPill("Neutral", "Neutral", "dir", id="dir-neutral")
                        yield SegmentPill("Netrunner", "Netrunner", "dir", id="dir-netrunner")
                        yield SegmentPill("Blackwall", "Blackwall ASI", "dir", id="dir-blackwall")

                    with Horizontal(classes="control-row"):
                        yield Label("Reasoning / CoT (/think):", classes="control-label")
                        yield CustomToggle(value=True, id="toggle-thinking")

                    with Horizontal(classes="control-row"):
                        yield Label("Telemetry Diagnostics:", classes="control-label")
                        yield CustomToggle(value=True, id="toggle-verbose")

                    yield Button("💾 Export Chat Logs (Ctrl+S)", id="btn-export", classes="action-btn")
                    yield Button("Wipe Memory Buffer", id="btn-clear", classes="action-btn")

            with Vertical(id="chat-workspace"):
                with VerticalScroll(id="messages-container"):
                    yield WelcomeMessageWidget()

                with Vertical(id="queue-container"):
                    with Horizontal(id="queue-header-row"):
                        yield Label("⏳ QUEUED PROMPTS (Click to remove)", id="queue-title-lbl")
                        yield Button("Clear All [✕]", id="btn-clear-queue")
                    with Horizontal(id="queue-items-scroll"):
                        pass

                with Horizontal(id="staged-media-strip"):
                    yield Label("📸 Image Staged: Ready for next prompt (Click to clear)", id="staged-media-lbl")

                with Horizontal(id="prompt-bar"):
                    yield HistoryInput(placeholder="Type message... (Paste image with Ctrl+V or Drag & Drop)", id="user-input")
                    yield Button("📋 Paste Img", id="btn-paste-media")
                    yield Button("Abort", id="stop-button")
                    yield Button("Execute", id="send-button")

        yield Footer()

    async def on_mount(self) -> None:
        os.makedirs(CHATS_DIR, exist_ok=True)
        os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
        self.load_persisted_config()
        self._session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.fetch_ollama_models()
        self.refresh_saved_sessions_list()
        self.query_one("#user-input", HistoryInput).focus()

    def stop_active_stream_worker(self) -> None:
        if self._active_stream_task is not None:
            is_finished = getattr(self._active_stream_task, "is_finished", False)
            if not is_finished and hasattr(self._active_stream_task, "cancel"):
                try:
                    self._active_stream_task.cancel()
                except Exception:
                    pass
        self._active_stream_task = None
        self.is_generating = False

    def load_persisted_config(self) -> None:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.default_model = cfg.get("default_model", "")
                self.current_model = self.default_model or cfg.get("last_model", "")
                self.temperature = float(cfg.get("temperature", 1.0))
                self.active_directive = cfg.get("active_directive", "Neutral")
                self.thinking_enabled = bool(cfg.get("thinking_enabled", True))
                self.verbose_enabled = bool(cfg.get("verbose_enabled", True))
            except Exception:
                pass

        for p in self.query(SegmentPill):
            if p.group == "temp":
                p.selected = (abs(float(p.val) - self.temperature) < 0.01)
            elif p.group == "dir":
                p.selected = (str(p.val) == self.active_directive)

        try:
            self.query_one("#toggle-thinking", CustomToggle).value = self.thinking_enabled
            self.query_one("#toggle-verbose", CustomToggle).value = self.verbose_enabled
        except Exception:
            pass

    def save_persisted_config(self) -> None:
        cfg = {
            "default_model": self.default_model,
            "last_model": self.current_model,
            "temperature": self.temperature,
            "active_directive": self.active_directive,
            "thinking_enabled": self.thinking_enabled,
            "verbose_enabled": self.verbose_enabled,
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def update_header_pill(self) -> None:
        think_str = "THINK:ON" if self.thinking_enabled else "THINK:OFF"
        model_display = self.current_model if self.current_model else "NONE"
        if self.default_model and self.current_model == self.default_model:
            model_display += " ★"
        dir_code = self.active_directive[:4].upper()
        media_str = "📸+1" if self._staged_media_b64 else "TEXT"
        q_str = f" │ Q:{len(self.prompt_queue)}" if self.prompt_queue else ""
        self.query_one("#header-status-pill", Label).update(
            f"[ 📦 {model_display} │ T:{self.temperature} │ {dir_code} │ {media_str}{q_str} │ 🧠 {think_str} ]"
        )

    def watch_current_model(self, new_val: str) -> None:
        self.update_header_pill()
        self.save_persisted_config()

    def watch_temperature(self, new_val: float) -> None:
        self.update_header_pill()
        self.save_persisted_config()

    def watch_active_directive(self, new_val: str) -> None:
        self.update_header_pill()
        self.save_persisted_config()

    def watch_is_generating(self, generating: bool) -> None:
        stop_btn = self.query_one("#stop-button", Button)
        send_btn = self.query_one("#send-button", Button)
        if generating:
            stop_btn.display = True
            send_btn.display = False
        else:
            stop_btn.display = False
            send_btn.display = True

    def refresh_queue_hud(self) -> None:
        q_box = self.query_one("#queue-container", Vertical)
        q_scroll = self.query_one("#queue-items-scroll", Horizontal)
        q_scroll.remove_children()

        if not self.prompt_queue:
            q_box.display = False
            self.update_header_pill()
            return

        q_box.display = True
        for idx, item in enumerate(self.prompt_queue):
            short_txt = (item["prompt"][:18] + "..") if len(item["prompt"]) > 18 else item["prompt"]
            if item.get("info"):
                short_txt = f"📸 {short_txt}"
            pill_text = f"✕ #{idx+1}: {short_txt}"
            q_scroll.mount(QueuePill(queue_id=item["id"], label_text=pill_text))

        self.update_header_pill()

    def on_queue_pill_remove_requested(self, event: QueuePill.RemoveRequested) -> None:
        initial_len = len(self.prompt_queue)
        self.prompt_queue = [item for item in self.prompt_queue if item["id"] != event.queue_id]
        if len(self.prompt_queue) < initial_len:
            self.notify("Queued prompt discarded.")
            self.refresh_queue_hud()

    def clear_entire_queue(self) -> None:
        self.prompt_queue.clear()
        self.refresh_queue_hud()
        self.notify("Queue cleared.")

    def try_trigger_next_in_queue(self) -> None:
        if self.is_generating or not self.prompt_queue:
            return

        next_item = self.prompt_queue.pop(0)
        self.refresh_queue_hud()

        chat_scroll = self.query_one("#messages-container", VerticalScroll)
        chat_scroll.mount(UserMessageWidget(prompt=next_item["prompt"], media_info=next_item.get("info", "")))
        chat_scroll.scroll_end(animate=False)

        user_entry = {"role": "user", "content": next_item["prompt"]}
        if next_item.get("images"):
            user_entry["images"] = next_item["images"]

        self.conversation_history.append(user_entry)
        self._active_stream_task = self.stream_ollama_response()

    def action_paste_clipboard_image(self) -> None:
        if shutil.which("wl-paste"):
            try:
                proc = subprocess.run(
                    ["wl-paste", "--type", "image/png"],
                    capture_output=True,
                    timeout=2.0,
                )
                if proc.returncode == 0 and len(proc.stdout) > 64:
                    self.archive_and_stage_raw_bytes(proc.stdout, filename="clipboard_paste.png")
                    return
            except Exception:
                pass

        if shutil.which("xclip"):
            try:
                proc = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
                    capture_output=True,
                    timeout=2.0,
                )
                if proc.returncode == 0 and len(proc.stdout) > 64:
                    self.archive_and_stage_raw_bytes(proc.stdout, filename="x11_clipboard.png")
                    return
            except Exception:
                pass

        if HAS_PIL:
            try:
                img = ImageGrab.grabclipboard()
                if isinstance(img, Image.Image):
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    self.archive_and_stage_raw_bytes(buf.getvalue(), filename="pil_paste.png")
                    return
            except Exception:
                pass

        self.notify("No image found in clipboard.", severity="warning")

    def ingest_and_archive_media(self, file_path_or_url: str) -> bool:
        clean_path = file_path_or_url.strip().strip("'\"")
        if clean_path.startswith("file://"):
            clean_path = urllib.parse.unquote(clean_path.replace("file://", ""))

        if not os.path.isfile(clean_path):
            return False

        try:
            with open(clean_path, "rb") as f:
                raw_bytes = f.read()

            orig_name = os.path.basename(clean_path)
            return self.archive_and_stage_raw_bytes(raw_bytes, filename=orig_name)
        except Exception as e:
            self.notify(f"Image read error: {e}", severity="error")
            return False

    def archive_and_stage_raw_bytes(self, raw_bytes: bytes, filename: str = "image.png") -> bool:
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{ts}_{os.path.basename(filename)}"
            dest_path = os.path.join(ATTACHMENTS_DIR, safe_filename)

            with open(dest_path, "wb") as f:
                f.write(raw_bytes)

            b64_str = base64.b64encode(raw_bytes).decode("utf-8")
            size_kb = len(raw_bytes) / 1024.0
            info = f"{safe_filename} ({size_kb:.1f} KB)"

            self._staged_media_b64 = [b64_str]
            self._staged_media_info = info

            strip = self.query_one("#staged-media-strip", Horizontal)
            strip.display = True
            lbl = self.query_one("#staged-media-lbl", Label)
            lbl.update(f"📸 Archived in ./attachments/: {info} [Click to remove]")

            self.update_header_pill()
            self.notify(f"Image saved to ./attachments/ & staged.")
            return True
        except Exception as e:
            self.notify(f"Failed to archive media: {e}", severity="error")
            return False

    def clear_staged_media(self) -> None:
        self._staged_media_b64 = []
        self._staged_media_info = ""
        try:
            strip = self.query_one("#staged-media-strip", Horizontal)
            strip.display = False
        except Exception:
            pass
        self.update_header_pill()

    def on_click(self, event: events.Click) -> None:
        if event.widget and event.widget.id == "staged-media-lbl":
            self.clear_staged_media()
            self.notify("Staged image removed.")

    def action_new_session(self, silent: bool = False) -> None:
        self.stop_active_stream_worker()
        self.clear_entire_queue()

        self._session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._session_title = ""
        self.conversation_history = []
        self.clear_staged_media()

        if self.default_model and self.default_model in self.models_list:
            self.current_model = self.default_model

        chat_scroll = self.query_one("#messages-container", VerticalScroll)
        chat_scroll.remove_children()
        chat_scroll.mount(WelcomeMessageWidget())
        chat_scroll.scroll_end(animate=False)

        if not silent:
            self.notify(f"New session initialized: {self._session_id}")
            self.refresh_saved_sessions_list()

    def action_delete_current_session(self) -> None:
        if not self._session_id:
            self.notify("No session selected to delete.", severity="warning")
            return

        json_file = os.path.join(CHATS_DIR, f"session_{self._session_id}.json")
        md_file = os.path.join(CHATS_DIR, f"session_{self._session_id}.md")

        deleted = False
        for f in (json_file, md_file):
            if os.path.exists(f):
                try:
                    os.remove(f)
                    deleted = True
                except Exception:
                    pass

        if deleted:
            self.notify(f"Session {self._session_id} deleted.")
            self.action_new_session(silent=True)
            self.refresh_saved_sessions_list()
        else:
            self.notify("Current session has no saved disk logs.", severity="warning")

    def auto_save_conversation(self) -> None:
        if not self.conversation_history:
            return

        base_filename = os.path.join(CHATS_DIR, f"session_{self._session_id}")

        if not self._session_title and self.conversation_history:
            first_user_msg = next((m["content"] for m in self.conversation_history if m["role"] == "user"), "Session")
            self._session_title = (first_user_msg[:24] + "...") if len(first_user_msg) > 24 else first_user_msg

        json_payload = {
            "session_id": self._session_id,
            "title": self._session_title or f"Chat {self._session_id}",
            "timestamp": datetime.datetime.now().isoformat(),
            "active_model": self.current_model,
            "temperature": self.temperature,
            "directive": self.active_directive,
            "messages": self.conversation_history,
        }
        with open(f"{base_filename}.json", "w", encoding="utf-8") as f:
            json.dump(json_payload, f, indent=2)

        with open(f"{base_filename}.md", "w", encoding="utf-8") as f:
            f.write(f"# Cyberden Session: {self._session_title}\n")
            f.write(f"**Session ID:** `{self._session_id}`  \n")
            f.write(f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            f.write(f"**Model Core:** `{self.current_model}`  \n")
            f.write(f"**Temperature:** `{self.temperature}`  \n")
            f.write(f"**Directive:** `{self.active_directive}`\n\n---\n\n")
            for msg in self.conversation_history:
                role_label = "**👤 OPERATOR**" if msg["role"] == "user" else f"**✨ MODEL ({self.current_model})**"
                f.write(f"{role_label}:\n\n{msg['content']}\n\n---\n\n")

        self.refresh_saved_sessions_list()

    def refresh_saved_sessions_list(self) -> None:
        listview = self.query_one("#sessions-listview", ListView)
        listview.clear()

        if not os.path.exists(CHATS_DIR):
            return

        files = [f for f in os.listdir(CHATS_DIR) if f.startswith("session_") and f.endswith(".json")]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(CHATS_DIR, x)), reverse=True)

        if not files:
            listview.append(ListItem(Label("• No saved sessions yet")))
            return

        for fname in files:
            fpath = os.path.join(CHATS_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sid = data.get("session_id", fname.replace("session_", "").replace(".json", ""))
                    title = data.get("title", sid)
                    item = ListItem(Label(f"💬 {title}"), name=sid)
                    listview.append(item)
            except Exception:
                pass

    def load_saved_session(self, session_id: str) -> None:
        self.stop_active_stream_worker()
        self.clear_entire_queue()
        self.clear_staged_media()

        fpath = os.path.join(CHATS_DIR, f"session_{session_id}.json")
        if not os.path.exists(fpath):
            self.notify(f"Session {session_id} not found.", severity="error")
            return

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._session_id = data.get("session_id", session_id)
            self._session_title = data.get("title", "")
            self.conversation_history = data.get("messages", [])

            if "active_model" in data and data["active_model"] in self.models_list:
                self.current_model = data["active_model"]

            if "temperature" in data:
                self.temperature = float(data["temperature"])

            if "directive" in data:
                self.active_directive = data["directive"]

            chat_scroll = self.query_one("#messages-container", VerticalScroll)
            chat_scroll.remove_children()

            for msg in self.conversation_history:
                if msg["role"] == "user":
                    chat_scroll.mount(UserMessageWidget(prompt=msg["content"]))
                elif msg["role"] == "assistant":
                    asst_widget = AssistantMessageWidget(model_name=self.current_model)
                    chat_scroll.mount(asst_widget)
                    asst_widget.update_response_view(msg["content"])

            chat_scroll.scroll_end(animate=False)
            self.notify(f"Loaded: {self._session_title or session_id}")
            self.append_system_notification(f"Active Session: **`{self._session_title or session_id}`**")

        except Exception as e:
            self.notify(f"Failed to load session: {e}", severity="error")

    def on_segment_pill_selected(self, event: SegmentPill.Selected) -> None:
        pill = event.pill
        if pill.group == "temp":
            self.temperature = float(pill.val)
            for p in self.query(SegmentPill):
                if p.group == "temp":
                    p.selected = (p == pill)
            self.notify(f"Temperature locked: {self.temperature}")
        elif pill.group == "dir":
            self.active_directive = str(pill.val)
            for p in self.query(SegmentPill):
                if p.group == "dir":
                    p.selected = (p == pill)
            self.notify(f"Directive active: {self.active_directive}")
        self.save_persisted_config()

    def on_custom_toggle_changed(self, event: CustomToggle.Changed) -> None:
        if event.toggle.id == "toggle-thinking":
            self.thinking_enabled = event.value
            self.notify(f"Reasoning stream: {'ENABLED' if event.value else 'DISABLED'}")
        elif event.toggle.id == "toggle-verbose":
            self.verbose_enabled = event.value
            self.notify(f"Telemetry diagnostics: {'ENABLED' if event.value else 'DISABLED'}")
        self.save_persisted_config()

    @work(exclusive=True)
    async def fetch_ollama_models(self) -> None:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m["name"] for m in data.get("models", [])]
                    self.models_list = models

                    listview = self.query_one("#model-listview", ListView)
                    await listview.clear()

                    if models:
                        if self.default_model and self.default_model in models:
                            self.current_model = self.default_model
                        elif not self.current_model or self.current_model not in models:
                            self.current_model = models[0]

                        for m in models:
                            label_txt = f"★ {m}" if m == self.default_model else f"• {m}"
                            item = ListItem(Label(label_txt), name=m)
                            await listview.append(item)

                        if self.current_model in models:
                            listview.index = models.index(self.current_model)
                        self.notify(f"Registry: {len(models)} model(s) loaded.")
                    else:
                        await listview.append(ListItem(Label("No models found.")))
        except Exception as e:
            self.notify(f"Error connecting to registry: {e}", severity="error")

    @work(exclusive=True)
    async def pull_model_worker(self, model_name: str) -> None:
        progress_box = self.query_one("#pull-progress-container", Vertical)
        status_lbl = self.query_one("#pull-status-label", Label)
        metrics_lbl = self.query_one("#pull-metrics-label", Label)
        pbar = self.query_one("#pull-progress-bar", ProgressBar)

        progress_box.display = True
        status_lbl.update(f"Pulling {model_name}...")
        metrics_lbl.update("Connecting...")
        pbar.update(progress=0, total=100)

        self.notify(f"Initiating pull for: {model_name}...")
        self.append_system_notification(f"Pulling **`{model_name}`** from registry...")

        start_time = time.monotonic()
        last_time = start_time
        last_bytes = 0

        try:
            async with httpx.AsyncClient(timeout=1800.0) as client:
                async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/pull", json={"name": model_name}) as res:
                    if res.status_code != 200:
                        status_lbl.update(f"Error HTTP {res.status_code}")
                        self.notify(f"Pull error: HTTP {res.status_code}", severity="error")
                        return

                    async for line in res.aiter_lines():
                        if not line:
                            continue
                        data = json.loads(line)
                        status_msg = data.get("status", "Streaming...")
                        completed = data.get("completed", 0)
                        total = data.get("total", 0)

                        now = time.monotonic()
                        dt = now - last_time

                        if total > 0:
                            pct = (completed / total) * 100.0
                            pbar.update(progress=pct, total=100)
                            c_mb = completed / (1024**2)
                            t_mb = total / (1024**2)

                            if dt >= 0.5:
                                bytes_diff = completed - last_bytes
                                speed_bps = bytes_diff / dt if dt > 0 else 0
                                speed_mbps = speed_bps / (1024**2)
                                remaining_bytes = total - completed
                                if speed_bps > 0:
                                    eta_seconds = int(remaining_bytes / speed_bps)
                                    mins, secs = divmod(eta_seconds, 60)
                                    eta_str = f"{mins:02d}:{secs:02d}"
                                else:
                                    eta_str = "--:--"

                                status_lbl.update(f"{status_msg} [{pct:.1f}%]")
                                metrics_lbl.update(f"{c_mb:.1f}/{t_mb:.1f} MB │ {speed_mbps:.1f} MB/s │ ETA: {eta_str}")
                                last_time = now
                                last_bytes = completed
                        else:
                            status_lbl.update(status_msg)
                            metrics_lbl.update("Processing manifests...")

            status_lbl.update("Complete!")
            metrics_lbl.update("Verification successful.")
            pbar.update(progress=100, total=100)
            self.notify(f"Model {model_name} installed!")
            self.append_system_notification(f"Model **`{model_name}`** installed successfully.")
            self.current_model = model_name
            self.fetch_ollama_models()
        except Exception as e:
            status_lbl.update(f"Error: {str(e)[:25]}")
            metrics_lbl.update("Download aborted.")
            self.notify(f"Pull failed: {e}", severity="error")
        finally:
            await asyncio.sleep(3.0)
            progress_box.display = False

    @work(exclusive=True)
    async def preload_model_into_vram(self, model_name: str) -> None:
        self.notify(f"Preloading {model_name} into VRAM...")
        self.append_system_notification(f"⚡ Loading **`{model_name}`** into GPU memory...")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={"model": model_name, "prompt": "", "keep_alive": "10m"},
                )
                if res.status_code == 200:
                    self.notify(f"{model_name} loaded in VRAM.")
                    self.append_system_notification(f"Model **`{model_name}`** is resident in VRAM.")
                else:
                    self.notify(f"Preload error: HTTP {res.status_code}", severity="error")
        except Exception as e:
            self.notify(f"Preload failed: {e}", severity="error")

    @work(exclusive=True)
    async def delete_model_worker(self, model_name: str) -> None:
        if not model_name:
            self.notify("Select a model to purge.", severity="warning")
            return

        self.notify(f"Purging {model_name} from disk...")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.request(
                    "DELETE",
                    f"{OLLAMA_BASE_URL}/api/delete",
                    json={"name": model_name},
                )
                if res.status_code == 200:
                    self.notify(f"Purged {model_name}.")
                    self.append_system_notification(f"Model **`{model_name}`** deleted from disk.")
                    if self.default_model == model_name:
                        self.default_model = ""
                    self.current_model = ""
                    self.save_persisted_config()
                    self.fetch_ollama_models()
                else:
                    self.notify(f"Delete failed: HTTP {res.status_code}", severity="error")
        except Exception as e:
            self.notify(f"Purge failed: {e}", severity="error")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "sessions-listview":
            if event.item and event.item.name:
                self.load_saved_session(event.item.name)
            return

        if event.list_view.id == "model-listview":
            if not event.item or not event.item.name:
                return

            model_name = event.item.name
            now = time.monotonic()
            is_double_click = (
                model_name == self._last_clicked_model and (now - self._last_click_time) < 0.4
            )

            self._last_click_time = now
            self._last_clicked_model = model_name

            if is_double_click:
                self.stop_active_stream_worker()
                self.current_model = model_name
                self.preload_model_into_vram(model_name)
            else:
                if self.current_model != model_name:
                    self.stop_active_stream_worker()
                    self.current_model = model_name
                    self.notify(f"Active core: {model_name}")
                    self.append_system_notification(f"Active core switched to: **`{model_name}`**")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-new-session":
            self.action_new_session()
        elif btn_id == "btn-delete-session":
            self.action_delete_current_session()
        elif btn_id == "btn-clear-queue":
            self.clear_entire_queue()
        elif btn_id == "btn-set-default":
            if self.current_model:
                self.default_model = self.current_model
                self.save_persisted_config()
                self.notify(f"Default core locked: {self.default_model}")
                self.append_system_notification(f"Default core assigned: **`{self.default_model}`**")
                self.fetch_ollama_models()
            else:
                self.notify("Select a model first.", severity="warning")
        elif btn_id == "btn-paste-media":
            self.action_paste_clipboard_image()
        elif btn_id == "send-button":
            self.handle_submission()
        elif btn_id == "stop-button":
            self.action_stop_generation()
        elif btn_id == "btn-export":
            self.action_export_chat()
        elif btn_id == "btn-pull":
            inp = self.query_one("#pull-input", Input)
            val = inp.value.strip()
            if val:
                inp.value = ""
                self.pull_model_worker(val)
        elif btn_id == "btn-delete-model":
            if self.current_model:
                self.delete_model_worker(self.current_model)
            else:
                self.notify("Select a model to purge.", severity="warning")
        elif btn_id == "btn-refresh":
            self.fetch_ollama_models()
        elif btn_id == "btn-unload":
            self.action_unload_model()
        elif btn_id == "btn-clear":
            self.action_clear_chat()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "user-input":
            self.handle_submission()
        elif event.input.id == "pull-input":
            val = event.input.value.strip()
            if val:
                event.input.value = ""
                self.pull_model_worker(val)

    def action_stop_generation(self) -> None:
        if self.is_generating:
            self.stop_active_stream_worker()
            self.notify("Inference halted.")
            self.append_system_notification("*[Inference halted by user]*")
            self.try_trigger_next_in_queue()

    def action_export_chat(self) -> None:
        if not self.conversation_history:
            self.notify("No conversation buffer to export.", severity="warning")
            return
        self.auto_save_conversation()
        self.notify(f"Saved to ./saved_chats/session_{self._session_id}.md")
        self.append_system_notification(f"Log saved to **`./saved_chats/session_{self._session_id}.md`**")

    def action_clear_chat(self) -> None:
        self.action_new_session()

    def action_refresh_models(self) -> None:
        self.fetch_ollama_models()

    def action_unload_model(self) -> None:
        self.unload_model_worker()

    @work(exclusive=True)
    async def unload_model_worker(self) -> None:
        if not self.current_model:
            self.notify("No model selected to eject.", severity="warning")
            return

        self.notify(f"Ejecting {self.current_model} from VRAM...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={"model": self.current_model, "keep_alive": 0},
                )
                if res.status_code == 200:
                    self.notify(f"VRAM buffer purged ({self.current_model}).")
                    self.append_system_notification(
                        f"Model **`{self.current_model}`** ejected from GPU (`keep_alive: 0`)."
                    )
                else:
                    self.notify(f"Eject error: HTTP {res.status_code}", severity="error")
        except Exception as e:
            self.notify(f"Eject failed: {e}", severity="error")

    def append_system_notification(self, text: str) -> None:
        chat_scroll = self.query_one("#messages-container", VerticalScroll)
        chat_scroll.mount(SystemMessageWidget(text))
        chat_scroll.scroll_end(animate=False)

    def handle_submission(self) -> None:
        input_widget = self.query_one("#user-input", HistoryInput)
        prompt = input_widget.value.strip()

        if not prompt and not self._staged_media_b64:
            return

        if not prompt and self._staged_media_b64:
            prompt = "Analyze and describe the attached image."

        input_widget.record_prompt(prompt)
        input_widget.value = ""

        if prompt.startswith("/"):
            parts = prompt.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd in ("/paste", "/clip"):
                self.action_paste_clipboard_image()
                return
            elif cmd in ("/clearimage", "/detach"):
                self.clear_staged_media()
                self.notify("Staged image removed.")
                return
            elif cmd in ("/clearqueue", "/cq"):
                self.clear_entire_queue()
                return
            elif cmd in ("/default", "/setdefault"):
                if self.current_model:
                    self.default_model = self.current_model
                    self.save_persisted_config()
                    self.notify(f"Default model locked to: {self.default_model}")
                    self.fetch_ollama_models()
                return
            elif cmd in ("/new", "/reset"):
                self.action_new_session()
                return
            elif cmd in ("/delete", "/del"):
                self.action_delete_current_session()
                return
            elif cmd in ("/unload", "/eject"):
                self.action_unload_model()
                return
            elif cmd in ("/think", "/reason"):
                self.thinking_enabled = True
                self.save_persisted_config()
                return
            elif cmd == "/nothink":
                self.thinking_enabled = False
                self.save_persisted_config()
                return
            elif cmd == "/clear":
                self.action_clear_chat()
                return
            elif cmd == "/export":
                self.action_export_chat()
                return

        staged_imgs = list(self._staged_media_b64)
        staged_info = self._staged_media_info
        self.clear_staged_media()

        if self.is_generating:
            queue_item = {
                "id": str(time.time_ns()),
                "prompt": prompt,
                "images": staged_imgs,
                "info": staged_info,
            }
            self.prompt_queue.append(queue_item)
            self.refresh_queue_hud()
            self.notify(f"Prompt queued (#{len(self.prompt_queue)})")
            return

        chat_scroll = self.query_one("#messages-container", VerticalScroll)
        chat_scroll.mount(UserMessageWidget(prompt=prompt, media_info=staged_info))
        chat_scroll.scroll_end(animate=False)

        user_entry = {"role": "user", "content": prompt}
        if staged_imgs:
            user_entry["images"] = staged_imgs

        self.conversation_history.append(user_entry)
        self._active_stream_task = self.stream_ollama_response()

    @work(exclusive=True)
    async def stream_ollama_response(self) -> None:
        if not self.current_model:
            self.notify("Select a model before querying.", severity="error")
            return

        self.is_generating = True
        chat_scroll = self.query_one("#messages-container", VerticalScroll)
        assistant_widget = AssistantMessageWidget(model_name=self.current_model)
        await chat_scroll.mount(assistant_widget)
        chat_scroll.scroll_end(animate=False)

        active_thinking = self.thinking_enabled
        active_verbose = self.verbose_enabled

        messages = []
        directive_prompt = DIRECTIVE_PROMPTS.get(self.active_directive, "")
        if directive_prompt:
            messages.append({"role": "system", "content": directive_prompt})
        messages.extend(self.conversation_history)

        payload = {
            "model": self.current_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        if not active_thinking:
            payload["think"] = False
        else:
            payload["think"] = True

        full_response = ""
        full_thinking = ""
        inside_tag_think = False
        thinking_completed = False

        BATCH_INTERVAL = 0.035
        last_thinking_update = time.monotonic()
        last_response_update = time.monotonic()

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                async with client.stream(
                    "POST", f"{OLLAMA_BASE_URL}/api/chat", json=payload
                ) as response:
                    if response.status_code != 200:
                        if assistant_widget.is_mounted:
                            assistant_widget.update_response_view(
                                f"\n*Error: Ollama returned HTTP {response.status_code}*"
                            )
                        self.is_generating = False
                        self.try_trigger_next_in_queue()
                        return

                    async for line in response.aiter_lines():
                        if not assistant_widget.is_mounted or not self.is_generating:
                            break

                        if not line:
                            continue
                        data = json.loads(line)

                        msg = data.get("message", {})
                        raw_thinking = msg.get("thinking", "")
                        raw_content = msg.get("content", "")

                        if raw_thinking and active_thinking:
                            full_thinking += raw_thinking
                            now = time.monotonic()
                            if now - last_thinking_update >= BATCH_INTERVAL:
                                assistant_widget.update_thinking_view(full_thinking)
                                last_thinking_update = now

                        if "<think>" in raw_content:
                            inside_tag_think = True
                            raw_content = raw_content.replace("<think>", "")
                        if "</think>" in raw_content:
                            inside_tag_think = False
                            parts = raw_content.split("</think>")
                            if active_thinking:
                                full_thinking += parts[0]
                            raw_content = parts[1] if len(parts) > 1 else ""

                        if inside_tag_think:
                            if active_thinking:
                                full_thinking += raw_content
                                now = time.monotonic()
                                if now - last_thinking_update >= BATCH_INTERVAL:
                                    assistant_widget.update_thinking_view(full_thinking)
                                    last_thinking_update = now
                        else:
                            if raw_content and not thinking_completed:
                                if active_thinking and full_thinking:
                                    assistant_widget.update_thinking_view(full_thinking)
                                    assistant_widget.finish_thinking()
                                thinking_completed = True

                            if raw_content:
                                full_response += raw_content
                                now = time.monotonic()
                                if now - last_response_update >= BATCH_INTERVAL:
                                    assistant_widget.update_response_view(full_response)
                                    chat_scroll.scroll_end(animate=False)
                                    last_response_update = now

                        if data.get("done") is True:
                            if active_thinking and full_thinking and not thinking_completed:
                                assistant_widget.update_thinking_view(full_thinking)
                                assistant_widget.finish_thinking()

                            assistant_widget.update_response_view(full_response)

                            total_dur = data.get("total_duration", 0) / 1e9
                            eval_count = data.get("eval_count", 0)
                            eval_dur = data.get("eval_duration", 0) / 1e9
                            prompt_count = data.get("prompt_eval_count", 0)
                            prompt_dur = data.get("prompt_eval_duration", 0) / 1e9

                            eval_rate = (eval_count / eval_dur) if eval_dur > 0 else 0.0
                            prompt_rate = (prompt_count / prompt_dur) if prompt_dur > 0 else 0.0

                            if active_verbose:
                                assistant_widget.render_verbose_stats({
                                    "eval_rate": eval_rate,
                                    "eval_count": eval_count,
                                    "eval_sec": eval_dur,
                                    "prompt_rate": prompt_rate,
                                    "total_sec": total_dur,
                                })
                            chat_scroll.scroll_end(animate=False)

            if assistant_widget.is_mounted and self.is_generating:
                self.conversation_history.append({"role": "assistant", "content": full_response})
                self.auto_save_conversation()

        except asyncio.CancelledError:
            pass
        except httpx.ConnectError:
            if assistant_widget.is_mounted:
                assistant_widget.update_response_view("\n*Connection error: Ollama is unreachable.*")
        except Exception as e:
            if assistant_widget.is_mounted:
                assistant_widget.update_response_view(f"\n\n*Buffer error: {str(e)}*")
        finally:
            self.is_generating = False
            self.try_trigger_next_in_queue()


if __name__ == "__main__":
    app = CyberdenApp()
    app.run()
