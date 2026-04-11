#!/usr/bin/env python3

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

console = Console()

banner_text = """
🚀 Welcome to Phase 0!
Get ready to build something amazing.
"""

console.print(
    Panel(
        banner_text,
        title="Phase 0",
        subtitle="Milrem Robotics",
        style="bold magenta",
        border_style="green",
    )
)
