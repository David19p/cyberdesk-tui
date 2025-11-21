# CyberDesk — Terminal Cyber-Desk (TUI)

<!-- Screenshot: relative path to workspace root image 'foto.png' -->
![CyberDesk TUI screenshot](../../photo.png)

A cyberdeck-style TUI desktop for Linux, displaying application icons in an interactive grid. Click to launch apps, navigate with keyboard, and enjoy a retro-futuristic terminal experience.

## Overview
CyberDesk scans Linux `.desktop` files and presents them in an interactive TUI grid. Each app is represented by a real icon image (PNG/JPG), unicode glyph (Nerd Font), or fallback emoji, with a label. Designed for fast prototyping and aesthetic terminal UX.

- Language: Python
- UI: Textual (TUI)
- Primary platform: Linux (X11 / Wayland). Tested on Arch with Hyprland; usable in WSL for development.

---

## Key Features
- Discovers `.desktop` entries in `/usr/share/applications` and `~/.local/share/applications`
- Grid layout with clickable App icons (AppIcon widget) showing real images, glyphs, or emojis
- Pick & Place: basic move/position of icons with persistence
- Launching: uses `gtk-launch` when available; if not available, uses `systemd-run --user --scope`, else `setsid` for a safe detach
- Icon overrides: `icons.json` (user can map an app name to a Nerd font glyph or emoji)
- Real image support: displays actual PNG/JPG icons from system icon themes (requires `textual-image`)
- Persistence through `~/.config/cyberdesk/layout.json`
- Debug flags `--list` and `--debug` for diagnosing discovery and mounting
- Grid is wrapped in a `ScrollableContainer` for smaller terminals (arrow keys / PageUp / PageDown available)

---

## Quick Start (Linux / Arch / WSL)
Prereqs:
- Python 3.11+ (3.12+ recommended)
- Textual and textual-image libraries (pip)
- Terminal emulator with Nerd Font (Hack Nerd Font / Fira Code Nerd Font) and image support (Kitty, WezTerm, etc. for real icons)

Simple install and run (Linux/WSL):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# or use the helper script
bash setup.sh
```

Run the app:

```bash
python cyberdesk_main.py
# Debug or list options
python cyberdesk_main.py --debug
# If glyphs appear as boxes, run with ASCII fallback to force the fallback icon
python cyberdesk_main.py --debug --ascii
# or with helper
bash run.sh --debug --ascii
python cyberdesk_main.py --list
```

Alternatively, you can use the provided helper script to create/activate a virtualenv, install requirements, and run the app:

```bash
# creates/activates venv, installs requirements and launches the app
bash run.sh
# with debug
bash run.sh --debug
```

Troubleshooting: 'externally-managed-environment'

If you run a pip command and see this error message:

```
error: externally-managed-environment
```

It means you're trying to install Python packages into a system-managed Python installation (for example, installed via your distro's package manager). The recommended options are:

- Use a virtual env:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

- Use pipx for a user-scoped install of tools:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install textual
```

- Or install with your package manager if the package is directly available in your distro:

```bash
# On Arch/Manjaro (if available)
sudo pacman -S python-textual
```

---

## Arch + Hyprland / Wayland notes
- Terminal choice: use a Wayland-friendly terminal (Alacritty, foot, Kitty). Windows Terminal / WSL also works for development.
- Install a Nerd Font from AUR: e.g., `nerd-fonts-hack` or `nerd-fonts-fira-code`.
- Launching on Wayland: `gtk-launch` respects `.desktop` metadata. CyberDesk prefers `gtk-launch` if the desktop id is available. On systemd systems, `systemd-run --user --scope` is used for safe detaching.
- You can add a Hyprland binding to open CyberDesk quickly from your Hyprland config.

Example Hyprland config keybinding:

```
bind=super,space,exec,alacritty -e python /path/to/repo/cyberdesk_main.py
```

---

## Debugging
- `--list` shows parsed `.desktop` files and their `Exec` lines (useful to confirm discovery)
- `--debug` prints parsing, rendering, and mounted children details
- If icons don't appear: ensure you're running a Nerd Font and adjust `AppIcon.DEFAULT_CSS` or grid columns
	- If icons show as boxes, try ASCII fallback with `--ascii` and hide labels with `--compact`.
		```bash
		# debug + ascii
		bash run.sh --debug --ascii
		# debug + compact (hide labels)
		bash run.sh --debug --compact
		```
	- While running, press `L` to toggle compact mode (hide labels) interactively.

---

## Development
- Main entry: `cyberdesk_main.py` — prototyping code should be easy to iterate on
- Suggestion: use `python-desktop-file` or `pyxdg` for more robust `.desktop` parsing in later commits

Dev workflow:

```bash
git clone <repo>
cd repo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python cyberdesk_main.py --debug
```

---

## Contributing
- Open issues for feature requests or bugs
- Use a dedicated branch for PRs, include tests or small scripts that reproduce issues when necessary
- Keep changes small and focused for faster reviews

---

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Roadmap
- Add UI to edit `icons.json` in-app
- Provide paginated or grouped views for many apps
- Windows Start Menu `.lnk` discovery for a cross-platform experience
- Add screenshot badges and CI (GitHub Actions) for linting and tests


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
