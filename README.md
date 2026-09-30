# Colen

A beautiful Jarvis-like CLI assistant built with Python.

## Features

- 🎨 Beautiful ASCII art banners (multiple styles)
- 🖥️ System information display
- ⏰ Current date and time
- 🧹 Terminal clearing
- 💬 Interactive shell with rich formatting
- 🎯 Single command execution mode
- 🧠 Conversational voice AI (Groq `llama-3.1-8b-instant` + PocketTTS) directly in the shell!

## Installation

```bash
pip install -e .
```

Or install with development dependencies:

```bash
pip install -e ".[dev]"
```

For voice replies, also install the audio extras and run a local PocketTTS
server (see the [Pocket TTS repo](https://github.com/kyutai-labs/pocket-tts)):

```bash
pip install -e ".[speech]"
pocket-tts serve          # serves http://localhost:8000
```

## Configuration

All secrets and settings live in a `.env` file (git-ignored). Copy the
template and fill in your own values:

```bash
cp .env.example .env        # macOS / Linux
copy .env.example .env      # Windows
```

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | yes | Groq API key ([console.groq.com/keys](https://console.groq.com/keys)) |
| `COLEN_LLM_MODEL` | no | Groq chat model (default `llama-3.1-8b-instant`; falls back automatically if unavailable on your key) |
| `COLEN_GROQ_URL` | no | Groq chat-completions endpoint |
| `COLEN_TTS_URL` | no | Local PocketTTS endpoint (default `http://localhost:8000/tts`) |
| `COLEN_VOICE_NAME` | no | Built-in PocketTTS voice preset (default `mary`; `""`/`file` clones from `voices/`) |
| `COLEN_VOICES_DIR` | no | Directory holding the voice-clone reference audio |
| `COLEN_CACHE_DIR` | no | Directory used to cache generated speech clips |

Values already exported in your shell take precedence over `.env`, so you can
always override per-session (e.g. `COLEN_LLM_MODEL=... colen`).

## Usage

### Interactive Mode (default)

```bash
colen
```

Or explicitly:

```bash
colen --interactive
```

### Single Command Mode

```bash
colen --command "help"
colen --command "info"
colen --command "time"
colen --command "banner minimal"
```

### Banner Styles

```bash
colen --banner jarvis      # Doom font (default)
colen --banner default     # Slant font
colen --banner minimal     # Minimal ASCII art
```

## Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `help` | `h`, `?` | Show available commands |
| `info` | `i`, `sysinfo` | Show system information |
| `time` | `t`, `date` | Show current date and time |
| `banner` | `b` | Show Colen banner |
| `banner <style>` | | Show banner with specific style |
| `clear` | `c`, `cls`, `reset` | Clear terminal and conversation context |
| `exit` | `q`, `quit`, `bye` | Exit Colen |
| `<any question>` | | Speak directly with Colen (streamed Groq AI + PocketTTS voice reply) |

## Screenshots

### Main Interface
![Main Interface](screenshots/main-interface.png)

### Tool Executing
![Banner Styles](screenshots/tool-working.png)

## Requirements

- Python 3.8+
- rich >= 13.0.0
- click >= 8.0.0
- pyfiglet >= 0.8

## License

MIT