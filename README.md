# Armenian Voice AI Support Agent

An Armenian-speaking LiveKit voice agent that provides customer support for exactly three banks:

- **Mellat Bank**
- **Ameriabank**
- **Ardshinbank**

This agent satisfies all core project criteria:
- **Scope-bound:** It only handles **deposits**, **credits and loans**, and **branch locations**. Guardrails explicitly prevent it from discussing other banks or off-topic subjects.
- **Data-Grounded:** All answers are grounded entirely in data scraped directly from the official bank websites using a Playwright pipeline.
- **RAG via Prompt Injection:** Extracts are compiled into `knowledge_base.json`, rendered compactly into `knowledge_base.md`, and injected directly into the Gemini Live system prompt. No vector database is used.
- **Native Audio:** Powered by `gemini-2.5-flash-native-audio-preview-12-2025` via LiveKit Agents `v1.5.0` to process and speak Armenian naturally.

## Project Structure

- `main.py`: LiveKit worker entrypoint
- `agent.py`: Gemini runtime configuration, prompt assembly, and environment validation
- `RUNNING.md`: Quick-start technical reference
- `system_prompt.md`: Agent identity, guardrails, and rules
- `knowledge_base.json` / `.md`: Structured compiled bank data
- `project_evaluation.py`: Automated static validation report generator
- `scraper/`: Playwright spiders, PDF processors, and data chunk compilers
- `tests/`: Project validation unit tests (`pytest`)

## Requirements

- Python 3.10+
- The local **LiveKit Server** binary
- A Google **Gemini API key**

```powershell
# Install dependencies
pip install -r requirements.txt
playwright install chromium
```

## Setup & Environment

Create a `.env` file in the project root:

```text
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
```
*(Do not commit your `.env` file!)*

If you modify the scraper, recompile the knowledge base data:
```powershell
python -m scraper.compiler --strict
```

## Running the Agent Locally

You need two terminals.

**Terminal 1: Start LiveKit Server**
```powershell
.\start_livekit.ps1
# or: D:\DATA\livekit-server\livekit-server.exe --dev
```

**Terminal 2: Start the Agent**
```powershell
.\start_agent.ps1
# or: python main.py dev
```

## Connecting & Testing

To talk to the agent in the browser, you need a room token.

**1. Generate a Connection Token**
Run this script snippet in PowerShell to generate a JWT token:
```powershell
python -c "from livekit import api; print(api.AccessToken('devkey', 'secret').with_identity('user').with_grants(api.VideoGrants(room_join=True, room='test-room')).to_jwt())"
```

**2. Connect in the Playground**
- Open [LiveKit Agents Playground](https://agents-playground.livekit.io/)
- Click the **Manual** tab
- **LiveKit URL**: `ws://localhost:7880`
- **Room Token**: Paste the generated token
- Click **Connect** and introduce yourself in Armenian!

## Evaluation & Testing

Run the automated test suite to verify module behavior:
```powershell
pytest -q
```

Run the static project validation checks (guardrails, bank coverage, content limits):
```powershell
python project_evaluation.py
```
This generates `evaluation_report.json` to prove the knowledge base meets minimum coverage thresholds.
