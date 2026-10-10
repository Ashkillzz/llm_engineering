"""
Terminal and HTML logging formatting utilities for Online Deal Scouter.
"""

# Foreground ANSI colors
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'

# Background ANSI colors
BG_BLACK = '\033[40m'
BG_BLUE = '\033[44m'

# ANSI Reset
RESET = '\033[0m'

COLOR_MAP = {
    BG_BLACK + RED: "#ff5555",
    BG_BLACK + GREEN: "#50fa7b",
    BG_BLACK + YELLOW: "#f1fa8c",
    BG_BLACK + BLUE: "#8be9fd",
    BG_BLACK + MAGENTA: "#bd93f9",
    BG_BLACK + CYAN: "#8be9fd",
    BG_BLACK + WHITE: "#f8f8f2",
    BG_BLUE + WHITE: "#ffb86c",
}


def reformat(message: str) -> str:
    """Converts terminal ANSI color codes into colored HTML spans for dashboard rendering."""
    for ansi_code, hex_color in COLOR_MAP.items():
        message = message.replace(ansi_code, f'<span style="color: {hex_color}; font-weight: bold;">')
    message = message.replace(RESET, '</span>')
    return message
