import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import Agent, AgentSession, AutoSubscribe, JobContext, JobProcess
from livekit.plugins import google

ROOT_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = ROOT_DIR / "system_prompt.md"
KNOWLEDGE_BASE_PATH = ROOT_DIR / "knowledge_base.md"
KNOWLEDGE_BASE_JSON_PATH = ROOT_DIR / "knowledge_base.json"

load_dotenv(ROOT_DIR / ".env")

logger = logging.getLogger("voice-agent")

REQUIRED_ENV_VARS = (
    "LIVEKIT_URL",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
    "GOOGLE_API_KEY",
)
GEMINI_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
GEMINI_VOICE = "Puck"
ARMENIAN_LANGUAGE_CODE = "hy-AM"   # BCP-47 for Eastern Armenian

MAX_PAGES_PER_CATEGORY = 2
MAX_TEXT_CHUNKS_PER_PAGE = 1
MAX_TABLES_PER_PAGE = 1
MAX_ROWS_PER_TABLE = 3
MAX_PDFS_PER_PAGE = 1
MAX_PDF_CHUNKS_PER_DOC = 1

# Armenian greeting spoken by the agent when a user joins.
GREETING_INSTRUCTIONS = (
    "Greet the user warmly in Armenian. "
    "Introduce yourself as the Armenian bank support assistant for Mellat Bank, "
    "Ameriabank, and Ardshinbank. "
    "Say that you can answer questions about deposits, credits, and branch locations. "
    "Ask how you can help them today. "
    "Keep it brief — two or three sentences."
)


def _read_text_file(path: Path, label: str) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required {label}: {path}")

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"Required {label} is empty: {path}")

    return content


def build_agent_instructions() -> str:
    system_prompt_template = _read_text_file(SYSTEM_PROMPT_PATH, "system prompt")
    knowledge_markdown = build_compact_knowledge_base()

    if "{{BANK_KNOWLEDGE_BASE}}" not in system_prompt_template:
        raise ValueError("system_prompt.md is missing the {{BANK_KNOWLEDGE_BASE}} placeholder")

    instructions = system_prompt_template.replace("{{BANK_KNOWLEDGE_BASE}}", knowledge_markdown)
    if "{{BANK_KNOWLEDGE_BASE}}" in instructions:
        raise ValueError("Knowledge base placeholder was not replaced")

    return instructions


def build_compact_knowledge_base() -> str:
    if KNOWLEDGE_BASE_JSON_PATH.exists():
        knowledge_base = json.loads(KNOWLEDGE_BASE_JSON_PATH.read_text(encoding="utf-8"))
        return render_compact_knowledge_base(knowledge_base)

    return _read_text_file(KNOWLEDGE_BASE_PATH, "knowledge base")


def render_compact_knowledge_base(knowledge_base: dict) -> str:
    lines = [
        "# Armenian Bank Knowledge Base",
        "",
        f"Generated at: {knowledge_base['generated_at']}",
        "",
    ]

    for bank in knowledge_base["banks"]:
        lines.append(f"## {bank['bank_name']}")
        lines.append("")
        for category in bank["categories"].values():
            lines.append(f"### {category['label']}")
            lines.append("")

            for page in category.get("pages", [])[:MAX_PAGES_PER_CATEGORY]:
                lines.append(f"- Page: {page.get('title') or page.get('url')}")
                lines.append(f"  URL: {page.get('url', '')}")

                headings = page.get("headings", [])
                if headings:
                    lines.append(f"  Headings: {', '.join(headings[:8])}")

                for chunk in page.get("text_chunks", [])[:MAX_TEXT_CHUNKS_PER_PAGE]:
                    lines.append(f"  Text: {chunk}")

                for table in page.get("data_tables", [])[:MAX_TABLES_PER_PAGE]:
                    sample_rows = table[:MAX_ROWS_PER_TABLE] if isinstance(table, list) else table
                    lines.append("  Table:")
                    lines.append("  ```json")
                    lines.append("  " + json.dumps(sample_rows, ensure_ascii=False))
                    lines.append("  ```")

                for pdf_doc in page.get("pdf_documents", [])[:MAX_PDFS_PER_PAGE]:
                    lines.append(f"  PDF: {pdf_doc.get('title', '')} | {pdf_doc.get('url', '')}")
                    for chunk in pdf_doc.get("content_chunks", [])[:MAX_PDF_CHUNKS_PER_DOC]:
                        lines.append(f"  PDF Text: {chunk}")

                lines.append("")

    return "\n".join(lines).strip()


def validate_environment() -> None:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def build_gemini_realtime_model() -> google.realtime.RealtimeModel:
    """Build the Gemini realtime model.

    - instructions are NOT set here; Agent.instructions is the single
      authoritative source in livekit-agents >= 1.0 and is synced
      automatically via update_instructions() when the session starts.
    - language="hy-AM" tells the Gemini Live API to recognise Armenian
      speech input even when the user speaks quietly or with an accent.
    - input/output transcription use defaults (AudioTranscriptionConfig)
      so the playground displays conversation text in real time.
    """
    return google.realtime.RealtimeModel(
        model=GEMINI_MODEL,
        api_key=os.getenv("GOOGLE_API_KEY"),
        voice=GEMINI_VOICE,
    )


def build_agent(instructions: str) -> Agent:
    return Agent(instructions=instructions)


def prewarm(proc: JobProcess) -> None:
    # Nothing heavy to prewarm for a realtime model; placeholder kept for
    # potential future use (e.g. loading the knowledge base once into shared memory).
    pass


async def entrypoint(ctx: JobContext) -> None:
    logger.info("starting entrypoint for room: %s", ctx.room.name)

    validate_environment()
    instructions = build_agent_instructions()

    realtime_model = build_gemini_realtime_model()

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    agent = build_agent(instructions)
    session = AgentSession(llm=realtime_model)

    await session.start(agent, room=ctx.room)
    logger.info("Agent started with Gemini Live native audio model %s", GEMINI_MODEL)
