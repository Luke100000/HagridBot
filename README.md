# HagridBot

HagridBot is a Discord bot with trigger-based moderation/help replies and optional LLM-backed chat responses in a
Hagrid-like persona.

## Features

- Rule-based trigger responses from `data/settings.json`
- Cross-channel anti-crosspost guard
- LLM chat fallback via `hey hagrid`
- MCA config Q&A (`hagrid config ...`)
- AI Horde image generation (`hagrid paint|draw ...`)
- XP/rank progression with slash commands (`/rank`, `/ranks`, `/rankadd`, `/rankremove`, `/rankchannel`)
- Usage stats (`/stats`)

## Runtime requirements

Set these in `.env`:

- `DISCORD_TOKEN`
- `LLM_API_URL`, `LLM_API_KEY`, `LLM_MODEL`
- `HORDE_API_KEY`

## Run locally

```bash
uv sync
python app/main.py
```

## Run with Docker Compose

```bash
docker compose up --build
```

`./data` is mounted to `/data` in the container so bot state survives restarts.

