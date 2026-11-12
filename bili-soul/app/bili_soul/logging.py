from rich.console import Console
from datetime import datetime
import logging
import sys
from pathlib import Path

console = Console() if sys.stdout is not None else None
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(filename="logs/bilisoul.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")

def say(stage, message, style="cyan"):
    stamp = datetime.now().strftime("%H:%M:%S")
    if console is not None:
        console.print(f"[dim]{stamp}[/dim] [{style}][{stage}][/{style}] {message}")
    logging.info("[%s] %s", stage, message)
