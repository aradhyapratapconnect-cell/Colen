"""ASCII Art for Colen CLI."""

from pyfiglet import Figlet


def get_colen_banner() -> str:
    """Get the Colen banner with ASCII art."""
    figlet = Figlet(font="slant", justify="center", width=120)
    return figlet.renderText("CoLen")


def get_jarvis_banner() -> str:
    """Get a Jarvis-style banner with decorative elements."""
    figlet = Figlet(font="doom", justify="center", width=80)
    banner = figlet.renderText("Colen")
    
    # Add decorative elements using ASCII characters
    lines = [line.rstrip() for line in banner.split('\n') if line.strip() != '']
    max_len = max(len(line) for line in lines)
    
    # Create border using ASCII
    border = '+' + '=' * (max_len + 4) + '+'
    bottom_line = '+' + '=' * (max_len + 4) + '+'
    
    # Center each line
    centered_lines = []
    for line in lines:
        padding = ' ' * ((max_len - len(line)) // 2)
        centered_lines.append('| ' + padding + line + padding + ' |')
    
    banner_text = '\n'.join(centered_lines)
    
    return f"{border}\n{banner_text}\n{bottom_line}\n"


def get_centered_banner() -> str:
    """Get a beautifully centered Colen banner with enhanced styling."""
    figlet = Figlet(font="big", justify="center", width=80)
    banner = figlet.renderText("Colen")
    
    # Clean up the banner
    lines = [line.rstrip() for line in banner.split('\n') if line.strip() != '']
    banner = '\n'.join(lines)
    max_len = max(len(line) for line in lines)
    
    # Add elegant decorative elements using ASCII
    width = max_len + 8
    top = '+' + '=' * (width - 2) + '+'
    bottom = '+' + '=' * (width - 2) + '+'
    
    # Center each line with borders
    centered_lines = []
    for line in lines:
        padding = ' ' * ((max_len - len(line)) // 2)
        centered_lines.append('| ' + padding + line + padding + ' |')
    
    banner_text = '\n'.join(centered_lines)
    subtitle = '| ' + ' ' * ((width - 20) // 2) + '+ System Assistant +' + ' ' * ((width - 20) // 2) + ' |'
    
    return f"{top}\n{banner_text}\n{subtitle}\n{bottom}\n"


def get_fancy_banner() -> str:
    """Get a fancy centered banner with decorative elements."""
    figlet = Figlet(font="standard", justify="center", width=80)
    banner = figlet.renderText("Colen")
    
    # Clean up the banner
    lines = [line.rstrip() for line in banner.split('\n') if line.strip() != '']
    banner = '\n'.join(lines)
    
    # Add simple decorative elements
    width = 80
    top = '+' + '=' * (width - 2) + '+'
    bottom = '+' + '=' * (width - 2) + '+'
    
    # Center the banner
    centered_lines = []
    for line in lines:
        padding = ' ' * ((width - len(line)) // 2)
        centered_lines.append(padding + line)
    
    banner_text = '\n'.join(centered_lines)
    subtitle = ' ' * ((width - 32) // 2) + '~ AI Automation - Voice Assistant ~'
    
    return f"{top}\n{banner_text}\n{subtitle}\n{bottom}\n"


def get_minimal_banner() -> str:
    """Get a minimal but elegant banner."""
    figlet = Figlet(font="standard", justify="center", width=80)
    banner = figlet.renderText("Colen")
    
    # Clean up the banner
    lines = [line.rstrip() for line in banner.split('\n') if line.strip() != '']
    banner = '\n'.join(lines)
    max_len = max(len(line) for line in lines)
    
    # Add simple elegant border
    width = max_len + 4
    top = '+' + '-' * (width - 2) + '+'
    bottom = '+' + '-' * (width - 2) + '+'
    
    # Center each line with borders
    centered_lines = []
    for line in lines:
        padding = ' ' * ((max_len - len(line)) // 2)
        centered_lines.append('| ' + padding + line + padding + ' |')
    
    banner_text = '\n'.join(centered_lines)
    subtitle = '| ' + ' ' * ((width - 24) // 2) + 'Voice Assistant' + ' ' * ((width - 24) // 2) + ' |'
    
    return f"{top}\n{banner_text}\n{subtitle}\n{bottom}\n"


def get_cyber_banner() -> str:
    """Get a cyber/futuristic banner with tech styling."""
    figlet = Figlet(font="larry3d", justify="center", width=80)
    banner = figlet.renderText("Colen")
    
    # Clean up the banner
    lines = [line.rstrip() for line in banner.split('\n') if line.strip() != '']
    banner = '\n'.join(lines)
    
    # Add cyber-style subtitle
    subtitle = "   >>> AI Automation System <<<"
    
    return f"{banner}\n{subtitle}\n"


def get_elegant_banner() -> str:
    """Get an elegant, minimalist banner with subtle styling."""
    figlet = Figlet(font="block", justify="center", width=80)
    banner = figlet.renderText("Colen")
    
    # Clean up the banner
    lines = [line.rstrip() for line in banner.split('\n') if line.strip() != '']
    banner = '\n'.join(lines)
    max_len = max(len(line) for line in lines)
    
    # Add elegant decorative elements using ASCII
    width = max_len + 6
    top = '+' + '-' * (width - 2) + '+'
    bottom = '+' + '-' * (width - 2) + '+'
    
    # Center each line with borders
    centered_lines = []
    for line in lines:
        padding = ' ' * ((max_len - len(line)) // 2)
        centered_lines.append('|' + padding + line + padding + '|')
    
    banner_text = '\n'.join(centered_lines)
    subtitle = '|' + ' ' * ((width - 18) // 2) + 'System Assistant' + ' ' * ((width - 18) // 2) + '|'
    
    return f"{top}\n{banner_text}\n{subtitle}\n{bottom}\n"


BANNERS = {
    "default": get_centered_banner,
    "centered": get_centered_banner,
    "jarvis": get_jarvis_banner,
    "fancy": get_fancy_banner,
    "minimal": get_minimal_banner,
    "cyber": get_cyber_banner,
    "elegant": get_elegant_banner,
}