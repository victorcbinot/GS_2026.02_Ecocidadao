from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.agent import EcoCidadaoAgent
from ecocidadao.config import get_settings
from ecocidadao.ui import STARTUP_ERROR_MESSAGE, build_demo


def main() -> None:
    settings = get_settings()
    agent: EcoCidadaoAgent | None = None
    startup_error: str | None = None
    try:
        agent = EcoCidadaoAgent(settings=settings)
    except Exception:
        startup_error = STARTUP_ERROR_MESSAGE

    demo = build_demo(
        agent=agent,
        settings=settings,
        startup_error=startup_error,
    )
    demo.launch(
        server_name=settings.gradio_server_name,
        server_port=settings.gradio_server_port,
        show_error=False,
    )


if __name__ == "__main__":
    main()
