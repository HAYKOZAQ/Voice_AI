# Running The Project

## 1. Install Dependencies

```powershell
pip install -r requirements.txt
playwright install chromium
```

## 2. Environment File

`.env` in the project root (already created):
```
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
GOOGLE_API_KEY=<your Gemini key>
```

## 3. Rebuild the Knowledge Base (if needed)

```powershell
python -m scraper.compiler --strict
```

## 4. Start LiveKit (Terminal 1)

The binary is at `D:\DATA\livekit-server\livekit-server.exe`.

```powershell
.\start_livekit.ps1
# or directly:
D:\DATA\livekit-server\livekit-server.exe --dev
```

Leave this terminal open.

## 5. Start The Agent (Terminal 2)

```powershell
.\start_agent.ps1
# or directly:
python main.py dev
```

You should see `registered worker {"agent_name": "armenian-bank-agent", ...}` in the logs.

## 6. Generate a Room Token (Terminal 3)

The playground needs a JWT. Run once per session:

```powershell
python -c "
from livekit import api
token = (
    api.AccessToken('devkey', 'secret')
    .with_identity('user')
    .with_grants(api.VideoGrants(room_join=True, room='test-room'))
    .to_jwt()
)
print(token)
"
```

Copy the printed token (it starts with `eyJ...`).

## 7. Connect to the Playground

1. Open **https://agents-playground.livekit.io/**
2. Click **Manual** tab
3. **URL** → `ws://localhost:7880`
4. **Room token** → paste the `eyJ...` token from step 6
5. Click **Connect**

> **Tip:** Use Chrome or Edge. If Connect does nothing, open the browser DevTools (F12) → Console to see any WebSocket errors.

## 8. Talk to the Agent

The agent will greet you in Armenian automatically. Ask about deposits, credits, or branch locations for Mellat Bank, Ameriabank, or Ardshinbank.

## 9. Run Tests

```powershell
pytest -q
python project_evaluation.py
```

## Notes

- LiveKit binary: `D:\DATA\livekit-server\livekit-server.exe`
- Model: Gemini Live native audio (`gemini-2.5-flash-native-audio-preview-12-2025`)
- Language recognition: `hy-AM` (Eastern Armenian)
- The agent greets users in Armenian automatically when they join.
