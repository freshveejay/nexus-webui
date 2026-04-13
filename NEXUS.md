# NEXUS Platform v3 - Open WebUI Fork

Local-first AI inference platform for Hollywood post-production teams.
Fork of [Open WebUI](https://github.com/open-webui/open-webui) with NEXUS intelligence baked in.

## Quick Start

```bash
# Copy env
cp .env.nexus .env

# Start with Docker Compose
docker compose -f docker-compose.nexus.yaml up -d

# After first startup, seed the database with NEXUS personas
docker exec nexus-webui python /app/nexus/seed.py
```

## What's Pre-Configured

### 5 AI Personas (Model Configs)
All powered by Nemotron 3 Super 120B on DGX Spark (192.168.1.113:8000)

| Persona | Temp | Purpose |
|---------|------|---------|
| NEXUS Base | 0.7 | General post-production assistant |
| Counsel | 0.3 | Legal, compliance, delivery specs |
| Muse | 0.9 | Creative ideation, trailer concepts |
| Quant | 0.4 | Data analysis, production metrics |
| Dispatch | 0.5 | Operations, scheduling, coordination |

### 5 User Groups (Role-Based Access)
| Group | Model Access |
|-------|-------------|
| Admin | All 5 personas + all tools |
| Creative | NEXUS Base, Muse |
| Analyst | NEXUS Base, Quant |
| Operator | NEXUS Base, Dispatch |
| Manager | NEXUS Base, Quant, Dispatch |

### Infrastructure
- LLM: Nemotron 3 Super 120B @ 192.168.1.113:8000
- TTS: Kokoro @ 192.168.1.145:5010
- Embeddings: NVIDIA NIM @ 192.168.1.109:8006
- Reranker: NVIDIA NIM @ 192.168.1.109:8005
- Vector DB: Milvus @ 192.168.1.109:19530

## Development

```bash
# Backend (Python/FastAPI)
cd backend && pip install -r requirements.txt
uvicorn open_webui.main:app --reload --port 8080

# Frontend (SvelteKit)
npm install && npm run dev
```

## License
Open WebUI license applies. Under 50 users: full rebranding allowed.
Over 50 users: enterprise license or merged contribution required.
