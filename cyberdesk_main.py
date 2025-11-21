#!/usr/bin/env python3
"""
CyberDesk - Real Graphics Version
Usa il widget Image nativo per mostrare PNG/JPG reali nel terminale.
"""
import os
import sys
import json
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from configparser import ConfigParser

try:
    from textual.app import App, ComposeResult
    from textual.containers import Grid, ScrollableContainer, Container, Vertical
    from textual.widgets import Label, Header, Footer, Static
    from textual.screen import ModalScreen
    from textual.events import Key
    
    # Importiamo il widget Image nativo (richiede 'pip install textual-image')
    try:
        from textual_image.widget import Image
        HAS_IMAGE = True
    except ImportError:
        # Fallback se manca la libreria specifica, usiamo quello built-in se disponibile in futuro
        # o gestiamo l'errore gentilmente
        HAS_IMAGE = False
        print("⚠️  Manca 'textual-image'. Le icone reali non si vedranno.")
        print("   Esegui: pip install textual-image")

except ModuleNotFoundError:
    print("Manca una libreria base. Esegui: pip install textual textual-image")
    sys.exit(1)

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "cyberdesk"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

DESKTOP_PATHS = [Path("/usr/share/applications"), Path.home() / ".local/share/applications"]

# Fallback Map (usata solo se non troviamo il file immagine)
ICON_MAP = {
    "firefox": "", "chrome": "", "brave": "", "code": "", "neovim": "", "vim": "",
    "terminal": "", "kitty": "🐱", "alacritty": "", "urxvt": "",
    "files": "", "folder": "", "nautilus": "", "thunar": "", "dolphin": "",
    "settings": "", "control": "🎚️", "qt": "", "rofi": "", "run": "",
    "vlc": "", "mpv": "", "obs": "", "monitor": "", "btop": "",
    "discord": "ﭮ", "spotify": "", "steam": "",
    "waypaper": "", "wallpaper": "", "nitrogen": "",
    "xournal": "", "draw": "", "paint": "", "gimp": "",
    "uuctl": "", "usb": "",
}

def load_icon_overrides(path: Path) -> Dict[str, str]:
    if not path.exists(): return {}
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def find_real_icon_path(icon_name: str) -> Optional[str]:
    """Cerca il percorso reale del file immagine (PNG/JPG/SVG)."""
    if not icon_name: return None
    
    path_obj = Path(icon_name)
    if path_obj.is_absolute() and path_obj.exists():
        return str(path_obj)
    
    clean_name = path_obj.stem
    search_roots = [
        Path("/usr/share/pixmaps"),
        Path("/usr/share/icons/hicolor"),
        Path("/usr/share/icons/Adwaita"),
        Path("/usr/share/icons/breeze"),
        Path("/usr/share/icons/Papirus"),
        Path.home() / ".local/share/icons"
    ]
    # Preferiamo risoluzioni alte per la grafica reale
    resolutions = ["256x256", "128x128", "64x64", "48x48", "scalable"]
    subdirs = ["apps", "categories", "places", "devices"]
    # SVG supportato da textual-image in molti casi, ma PNG è più sicuro
    extensions = [".png", ".svg", ".jpg", ".ico"] 

    # 1. Cerca nella root diretta (es. /usr/share/pixmaps/firefox.png)
    for root in search_roots:
        if not root.exists(): continue
        for ext in extensions:
            direct = root / (clean_name + ext)
            if direct.exists(): return str(direct)

    # 2. Cerca nelle sottocartelle
    for root in search_roots:
        if not root.exists(): continue
        for res in resolutions:
            for sub in subdirs:
                for ext in extensions:
                    candidate = root / res / sub / (clean_name + ext)
                    if candidate.exists(): return str(candidate)
                    candidate_lower = root / res / sub / (clean_name.lower() + ext)
                    if candidate_lower.exists(): return str(candidate_lower)
    return None

class HelpScreen(ModalScreen):
    CSS = """
    HelpScreen { align: center middle; background: rgba(30, 30, 46, 0.8); }
    #help-container { width: 50; height: auto; background: #313244; border: heavy #89b4fa; padding: 2; }
    .help-title { text-align: center; color: #f9e2af; text-style: bold; margin-bottom: 1; }
    .help-row { color: #cdd6f4; margin: 1 0; }
    """
    def compose(self) -> ComposeResult:
        with Vertical(id="help-container"):
            yield Label("⌨️  COMANDI", classes="help-title")
            yield Label("[N] / [DX]  : Pagina Successiva", classes="help-row")
            yield Label("[P] / [SX]  : Pagina Precedente", classes="help-row")
            yield Label("[K]         : Chiudi menu", classes="help-row")
            yield Label("[R]         : Ricarica tutto", classes="help-row")
            yield Label("[ESC]       : Esci", classes="help-row")
    def on_key(self, event: Key) -> None:
        if event.key == "escape" or event.key.lower() == "k": self.dismiss()

class AppIcon(Static):
    DEFAULT_CSS = """
    AppIcon {
        width: 28;
        min-width: 20;  /* Impedisce che l'icona venga schiacciata troppo */
        max-width: 32;
        height: 28;
        margin: 1 1;
        padding: 1;
        background: #313244;
        border: heavy #45475a;
        color: #cdd6f4;
        align: center middle;
    }
    AppIcon:hover {
        background: #45475a;
        border: heavy #89b4fa;
    }
    
    /* Stile specifico per il widget Image */
    Image {
        width: 100%;
        height: 6; /* Altezza riservata all'immagine */
        content-align: center middle;
        margin-bottom: 1;
    }
    
    .icon-label {
        width: 100%; text-align: center; color: #bac2de; height: 3;
        text-style: bold;
    }
    
    .fallback-glyph {
        width: 100%; text-align: center; color: #f9e2af;
        text-style: bold; height: 4; padding-bottom: 1;
        content-align: center middle;
    }
    """

    def __init__(self, app_id: str, label: str, icon: str, command: str, icon_path: Optional[str], terminal: bool = False) -> None:
        super().__init__()
        self.app_id = app_id
        self.app_name = label or "Unknown"
        self.icon_char = icon or "?"
        self.command = command
        self.icon_file_path = icon_path
        self.is_terminal = terminal

    def compose(self) -> ComposeResult:
        img_widget = None
        
        if HAS_IMAGE and self.icon_file_path:
            try:
                # Textual Image gestisce automaticamente il rendering migliore
                img_widget = Image(self.icon_file_path)
                # Impostiamo una dimensione in celle fissa per il layout
                img_widget.styles.width = "100%"
                img_widget.styles.height = 6
            except Exception:
                # Se fallisce (es. SVG complesso o formato strano), fallback
                img_widget = None

        if img_widget:
            yield img_widget
        else:
            yield Label(self.icon_char, classes="fallback-glyph")
            
        yield Label(self.app_name, classes="icon-label")

    def on_click(self) -> None:
        self.launch_app()

    def launch_app(self):
        # --- DEBUG SETUP ---
        log_path = Path.home() / "debug_cyberdesk.txt"
        def log(msg):
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[App: {self.app_name}] {msg}\n")
        # -------------------

        log(f"Click rilevato. Comando originale: {self.command}")
        log(f"Richiede terminale? {self.is_terminal}")

        if not self.command: 
            log("Nessun comando trovato. Esco.")
            return
        
        cmd_parts = []
        try: cmd_parts = shlex.split(self.command)
        except ValueError: cmd_parts = self.command.split()
        
        if not cmd_parts: return

        # Gestione App CLI
        if self.is_terminal:
            log("Cerco un emulatore di terminale...")
            # Aggiunto x-terminal-emulator che è standard su molti linux
            terminals = [
                ("x-terminal-emulator", "-e"),
                ("gnome-terminal", "--"), 
                ("kitty", "-e"), 
                ("alacritty", "-e"),
                ("xfce4-terminal", "-x"), 
                ("konsole", "-e"), 
                ("terminator", "-x"),
                ("xterm", "-e")
            ]
            
            found_term = None
            for term, flag in terminals:
                if shutil.which(term):
                    found_term = (term, flag)
                    log(f"Trovato terminale: {term}")
                    break
            
            if found_term:
                term_exe, term_flag = found_term
                # Costruiamo il comando finale
                prefix = [term_exe, term_flag] if term_flag else [term_exe]
                cmd_parts = prefix + cmd_parts
                log(f"Comando finale costruito: {cmd_parts}")
            else:
                log("ERRORE: Nessun terminale trovato nella lista.")
                self.app.notify("❌ Nessun terminale trovato!", severity="error")
                return

        executable = cmd_parts[0]
        # Nota: se usiamo un terminale, l'eseguibile è il terminale stesso, quindi shutil.which funzionerà
        if not shutil.which(executable):
            log(f"ERRORE: Eseguibile {executable} non trovato nel PATH.")
            self.app.notify(f"❌ Non trovato: {executable}", severity="error")
            return
            
        self.app.notify(f"🚀 {self.app_name}", timeout=2)
        try:
            log("Tentativo di avvio subprocess...")
            subprocess.Popen(
                cmd_parts, 
                start_new_session=True,
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL, 
                stdin=subprocess.DEVNULL,
                close_fds=True, 
                cwd=str(Path.home())
            )
            log("Subprocess lanciato con successo (teorico).")
        except Exception as e:
            log(f"EXCEPTION durante Popen: {e}")
            self.app.notify(f"❌ {e}", severity="error")

class CyberDesk(App):
    ENABLE_COMMAND_PALETTE = True 
    
    CSS = """
    Screen { background: #1e1e2e; align: center middle; }
    Header { background: #11111b; color: #cdd6f4; dock: top; height: 1; }
    Footer { background: #11111b; color: #6c7086; dock: bottom; }
    .grid-container { align: center middle; height: 100%; padding: 2; }
    Grid { grid-size: 4; grid-gutter: 1; align: center middle; }
    .status-bar { width: 100%; text-align: center; color: #6c7086; background: #1e1e2e; padding-bottom: 1; }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apps: List[Dict] = []
        self.icons_override = load_icon_overrides(CONFIG_DIR / "icons.json")
        self.page_offset = 0
        self.CARD_WIDTH = 32 

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="grid-container"):
            yield Label("", classes="status-bar", id="status")
            with ScrollableContainer():
                self.grid = Grid()
                yield self.grid
        yield Footer()

    async def on_mount(self) -> None:
        self.title = "CyberDesk"
        self.load_apps()
        await self.render_icons()
        self.call_after_refresh(self.refresh_grid_columns)

    async def on_resize(self, event) -> None:
        """
        Gestisce il ridimensionamento con un debounce.
        Evita di ridisegnare 100 volte mentre trascini la finestra.
        """
        # Se c'è già un timer attivo (stiamo ancora ridimensionando), lo annulliamo
        if hasattr(self, "_resize_timer") and self._resize_timer:
            self._resize_timer.stop()
            
        # Impostiamo un nuovo timer: ridisegna solo se ci fermiamo per 0.3 secondi
        self._resize_timer = self.set_timer(0.3, self.redraw_after_resize)

    async def redraw_after_resize(self) -> None:
        """
        Chiamato quando il ridimensionamento è 'stabilizzato'.
        """
        # 1. Ricalcola le colonne della griglia basandosi sulla nuova larghezza
        self.refresh_grid_columns()
        
        # 2. IMPORTANTE: Ricarica le icone!
        # Se la finestra è più grande, magari ora ci stanno più app per pagina.
        # Senza questo, la griglia cambia forma ma le icone restano vecchie/spostate male.
        await self.render_icons()

    def refresh_grid_columns(self) -> None:
        try:
            width = self.size.width
            cols = max(1, (width - 4) // self.CARD_WIDTH)
            self.grid.styles.grid_size_columns = cols
        except Exception: pass

    async def on_key(self, event: Key) -> None:
        if event.key.lower() == "k":
            self.push_screen(HelpScreen())
        elif event.key.lower() == "n" or event.key == "right":
            self.change_page(1)
        elif event.key.lower() == "p" or event.key == "left":
            self.change_page(-1)
        elif event.key.lower() == "r":
            self.load_apps()
            await self.render_icons()
            self.notify("App ricaricate")
        elif event.key == "escape":
            self.exit()

    def change_page(self, direction: int):
        try:
            cols = self.grid.styles.grid_size_columns or 3
            rows = max(1, (self.size.height - 6) // 14) # Altezza card leggermente diversa
            per_page = cols * rows
        except: per_page = 12
        
        if direction > 0:
            self.page_offset = min(len(self.apps) - per_page, self.page_offset + per_page)
        else:
            self.page_offset = max(0, self.page_offset - per_page)
        self.run_worker(self.render_icons())

    async def render_icons(self):
        await self.grid.remove_children()
        try:
            cols = self.grid.styles.grid_size_columns or 3
            rows = max(1, (self.size.height - 6) // 14) 
            per_page = max(1, cols * rows)
        except: per_page = 15

        start = max(0, self.page_offset)
        end = min(len(self.apps), start + per_page)
        page_apps = self.apps[start:end]
        
        status = self.query_one("#status", Label)
        current = (start // per_page) + 1
        status.update(f"  Apps: {len(self.apps)}  |  📄 Pagina {current}  |  [K] Comandi")

        for app in page_apps:
            btn = AppIcon(
                app.get("id"), 
                app.get("Name"), 
                app.get("icon"), 
                app.get("Exec"),
                app.get("icon_path"),
                app.get("terminal", False)
            )
            await self.grid.mount(btn)

    def load_apps(self):
        apps = []
        for d in DESKTOP_PATHS:
            if not d.exists(): continue
            for p in d.glob("*.desktop"):
                data = self.parse_desktop(p)
                if data: apps.append(data)
            seen = set()
            filtered = []
        for a in apps:
            key = (a.get("Name"), a.get("Exec"))
            if key not in seen:
                filtered.append(a)
                seen.add(key)
        self.apps = sorted(filtered, key=lambda x: x["Name"].lower())
        if not self.apps: self.apps = [{"id": "1", "Name": "Term", "Exec": "bash", "icon": "", "icon_path": None, "terminal": True}]

    def parse_desktop(self, path: Path) -> Optional[Dict]:
        cfg = ConfigParser(interpolation=None)
        try: cfg.read(path, encoding="utf-8")
        except: return None
        if "Desktop Entry" not in cfg: return None
        entry = cfg["Desktop Entry"]
        if entry.get("NoDisplay", "false").lower() == "true": return None
        
        name = entry.get("Name", path.stem)
        raw_exec = entry.get("Exec", "")
        icon_name = entry.get("Icon", "")
        # --- NUOVO: Leggiamo se serve il terminale ---
        term_val = entry.get("Terminal", "false").lower()
        is_terminal = term_val in ("true", "1")
        
        exec_clean = ""
        if raw_exec:
            try:
                parts = [p for p in shlex.split(raw_exec) if not p.startswith("%")]
                exec_clean = " ".join(parts)
            except ValueError:
                exec_clean = raw_exec.split("%")[0].strip()

        real_icon_path = find_real_icon_path(icon_name)

        # Fallback Glifo solo se manca l'immagine
        icon_char = "?"
        if not real_icon_path:
            lower_name = (exec_clean + " " + icon_name).lower()
            for k, v in ICON_MAP.items():
                if k in lower_name: 
                    icon_char = v
                    break
            if icon_char == "?": icon_char = name[:1].upper()

        return {
            "id": path.stem, 
            "Name": name, 
            "Exec": exec_clean, 
            "icon": icon_char, 
            "icon_path": real_icon_path
            ,
            "terminal": is_terminal,
        }

if __name__ == "__main__":
    app = CyberDesk()
    app.run()