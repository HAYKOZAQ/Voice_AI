import logging

from livekit.agents import WorkerOptions, cli

from agent import entrypoint, prewarm


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
    ))
