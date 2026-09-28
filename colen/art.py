"""ASCII Art for Colen CLI."""

from pyfiglet import Figlet


def get_colen_banner() -> str:
    """Get the Colen banner with ASCII art."""
    figlet = Figlet(font="slant", justify="center", width=120)
    return figlet.renderText("CoLen")


def get_jarvis_banner() -> str:
    """Get a Jarvis-style banner."""
    figlet = Figlet(font="doom", justify="center", width=78)
    return figlet.renderText("Colen")


def get_centered_banner() -> str:
    """Get a beautifully centered Colen banner."""
    figlet = Figlet(font="big", justify="center", width=78)
    banner = figlet.renderText("Colen")
    # Add a subtle underline
    lines = [line.rstrip() for line in banner.split('\n') if line.strip() != '']
    banner = '\n'.join(lines)
    max_len = max(len(line) for line in lines)
    underline = ' ' * ((max_len - 20) // 2) + '=' * 20
    return banner + '\n' + underline + '\n'


def get_fancy_banner() -> str:
    """Get a fancy centered banner with decorative elements."""
    figlet = Figlet(font="standard", justify="center", width=78)
    banner = figlet.renderText("Colen")
    
    # Clean up the banner - remove trailing spaces and extra newlines
    lines = [line.rstrip() for line in banner.split('\n') if line.strip() != '']
    banner = '\n'.join(lines)
    
    # Add decorative top and bottom
    width = 78
    top = '=' * width
    bottom = '=' * width
    subtitle = ' ' * ((width - 22) // 2) + '* Your AI Assistant *'
    
    return f"{top}\n{banner}\n{subtitle}\n{bottom}\n"


def get_minimal_banner() -> str:
    """Get a minimal banner."""
    return """
    
    CoLen - Your AI Assistant
    ==========================
    
"""


BANNERS = {
    "default": get_centered_banner,
    "jarvis": get_jarvis_banner,
    "fancy": get_fancy_banner,
    "minimal": get_minimal_banner,
}