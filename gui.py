import os
import sys
import tempfile
import threading
import http.server
import socketserver
import webbrowser
from pathlib import Path

import flet as ft

Icons = ft.icons.Icons

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from main import generate_site
from ai_themes import generate_theme, apply_theme, PRELOADED_THEMES, test_api_key, detect_provider, generate_offline_theme, MOOD_PALETTES

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULTS = {
    "content": os.path.join(PROJECT_ROOT, "content"),
    "static": os.path.join(PROJECT_ROOT, "static"),
    "template": os.path.join(PROJECT_ROOT, "template.html"),
    "output": os.path.join(PROJECT_ROOT, "docs"),
    "base_path": "/",
    "repo_name": "quickmark",
}

ACCENT = "#6568ff"
SURFACE = "#0f1117"
SIDEBAR = "#161b22"
CARD = "#1a1f2e"
INPUT_BG = "#21262d"
INPUT_HOVER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
DIM = "#484f58"
BORDER = "#30363d"
RED = "#f85149"
GREEN = "#3fb950"
YELLOW = "#d29922"
BLUE = "#58a6ff"

FONT_MONO = "Cascadia Code, Fira Code, Consolas, monospace"

SIDEBAR_W = 260

SAMPLE_CONTENT = """
<h1>Welcome to My Blog</h1>
<p>This is a sample paragraph to preview your theme. The text should be readable and well-styled.</p>
<h2>Features</h2>
<p>Here are some things this site supports:</p>
<ul>
<li>Markdown to HTML conversion</li>
<li>Custom CSS themes</li>
<li>Responsive design</li>
</ul>
<h2>Code Example</h2>
<p>Here's how a code block looks:</p>
<pre><code>def hello():
    print("Hello, World!")
</code></pre>
<blockquote>This is a blockquote. It should have a distinct left border and subtle background.</blockquote>
<p>Visit our <a href="/blog/">blog page</a> for more articles.</p>
<hr>
<p>Final paragraph with some closing text.</p>
"""


def make_input(**kwargs):
    defaults = {
        "border_radius": 8,
        "filled": True,
        "bgcolor": INPUT_BG,
        "color": TEXT,
        "border_color": "transparent",
        "focused_border_color": ACCENT,
        "cursor_color": ACCENT,
        "text_size": 13,
    }
    defaults.update(kwargs)
    return ft.TextField(**defaults)


class ColorPicker:
    def __init__(self, label, initial="#61afef", on_change=None):
        self.on_change = on_change
        self._value = initial
        r, g, b = self._hex_to_rgb(initial)
        self.r_slider = ft.Slider(min=0, max=255, value=r, label="{value}", on_change=self._on_slider)
        self.g_slider = ft.Slider(min=0, max=255, value=g, label="{value}", on_change=self._on_slider)
        self.b_slider = ft.Slider(min=0, max=255, value=b, label="{value}", on_change=self._on_slider)
        self.hex_field = make_input(value=initial, width=90, text_size=12, on_submit=self._on_hex_submit)
        self.swatch = ft.Container(
            width=32, height=32, border_radius=8, bgcolor=initial,
            border=ft.border.all(1, BORDER),
        )
        self.label = ft.Text(label, size=11, color=MUTED, width=60)

        self.r_slider.width = 140
        self.g_slider.width = 140
        self.b_slider.width = 140

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return 100, 100, 100
        return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    def _on_slider(self, e):
        r, g, b = int(self.r_slider.value), int(self.g_slider.value), int(self.b_slider.value)
        self._value = f"#{r:02x}{g:02x}{b:02x}"
        self.hex_field.value = self._value
        self.swatch.bgcolor = self._value
        if self.on_change:
            self.on_change(self._value)
        self.container.update()

    def _on_hex_submit(self, e):
        val = self.hex_field.value.strip()
        if val.startswith("#") and len(val) == 7:
            try:
                self._value = val
                r, g, b = self._hex_to_rgb(val)
                self.r_slider.value = r
                self.g_slider.value = g
                self.b_slider.value = b
                self.swatch.bgcolor = val
                if self.on_change:
                    self.on_change(self._value)
                self.container.update()
            except ValueError:
                pass

    def build(self):
        self.container = ft.Container(
            content=ft.Row(
                [
                    self.label,
                    self.r_slider,
                    ft.Container(width=4),
                    self.g_slider,
                    ft.Container(width=4),
                    self.b_slider,
                    self.swatch,
                    self.hex_field,
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(vertical=4),
        )
        return self.container

    @property
    def value(self):
        return self._value


class FileTree:
    def __init__(self, on_select):
        self.on_select = on_select
        self.controls = []
        self.container = None

    def build(self, directory, label="Files"):
        self.controls = []
        self._add_dir(directory, indent=0)
        self.container = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(label, size=12, color=MUTED, weight="bold"),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=Icons.REFRESH,
                                icon_size=16,
                                icon_color=MUTED,
                                on_click=lambda e: self.reload(directory),
                                tooltip="Refresh",
                            ),
                        ],
                        spacing=4,
                    ),
                    ft.Divider(color=BORDER, height=8),
                    ft.ListView(
                        controls=self.controls,
                        expand=True,
                        spacing=0,
                        padding=0,
                    ),
                ],
                spacing=0,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )
        return self.container

    def reload(self, directory):
        self.controls.clear()
        self._add_dir(directory, indent=0)
        if self.container:
            self.container.content.controls[-1].controls = self.controls
            self.container.update()

    def _add_dir(self, directory, indent):
        try:
            items = sorted(Path(directory).iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except Exception:
            return

        for item in items:
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            if item.is_dir():
                self._add_dir(item, indent)
            elif item.suffix in (".md", ".html", ".css", ".js", ".json", ".toml", ".txt", ".yml", ".yaml", ".sh"):
                self.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(width=indent * 16),
                                ft.Icon(Icons.DESCRIPTION, size=14, color=DIM),
                                ft.Text(item.name, size=13, color=TEXT, no_wrap=True),
                            ],
                            spacing=6,
                        ),
                        padding=ft.padding.symmetric(horizontal=8, vertical=6),
                        border_radius=6,
                        on_hover=self._hover,
                        on_click=lambda e, p=str(item): self.on_select(p),
                    )
                )

    def _hover(self, e):
        e.control.bgcolor = INPUT_HOVER if e.data == "true" else None
        e.control.update()


class Editor:
    def __init__(self):
        self.current_file = None
        self.original = ""
        self.field = ft.TextField(
            multiline=True,
            border_radius=0,
            filled=True,
            bgcolor=INPUT_BG,
            color=TEXT,
            border_color="transparent",
            focused_border_color=ACCENT,
            cursor_color=ACCENT,
            text_style=ft.TextStyle(font_family=FONT_MONO, size=14, color=TEXT),
            content_padding=20,
            expand=True,
        )

    def open_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.current_file = path
            self.original = content
            self.field.value = content
            self.field.label = Path(path).name
            self.field.update()
            return True
        except Exception:
            return False

    def save(self):
        if self.current_file:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.field.value)
            self.original = self.field.value
            return True
        return False

    def is_dirty(self):
        return self.field.value != self.original if self.current_file else False


def main(page: ft.Page):
    page.title = "Quickmark - Static Site Generator"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = SURFACE
    page.padding = 0
    page.window_width = 1400
    page.window_height = 800
    page.window_min_width = 1100
    page.window_min_height = 650

    editor = Editor()
    file_tree = FileTree(on_select=None)

    status_text = ft.Text("Select a file to edit", size=12, color=MUTED)
    dirty_badge = ft.Container(
        content=ft.Text("", size=11, color=YELLOW),
        visible=False,
        padding=ft.padding.only(right=8),
    )

    fields = {
        "base_path": make_input(label="Base Path", value=DEFAULTS["base_path"])
    }

    def _on_mode_change(e):
        if "github" in e.control.selected:
            fields["base_path"].value = f"/{DEFAULTS['repo_name']}/"
        else:
            fields["base_path"].value = "/"
        fields["base_path"].update()

    mode_toggle = ft.SegmentedButton(
        selected=["local"],
        on_change=_on_mode_change,
        segments=[
            ft.Segment(
                value="local",
                label=ft.Text("Local"),
                icon=ft.Icon(Icons.LOCAL_BAR, size=16),
            ),
            ft.Segment(
                value="github",
                label=ft.Text("GitHub Pages"),
                icon=ft.Icon(Icons.CLOUD, size=16),
            ),
        ],
        selected_icon=None,
    )

    output_log = ft.TextField(
        label="Build Output",
        read_only=True,
        multiline=True,
        border_radius=8,
        filled=True,
        bgcolor=INPUT_BG,
        color=MUTED,
        border_color="transparent",
        expand=True,
        text_size=12,
    )

    def do_select_file(path):
        editor.open_file(path)
        status_text.value = f"Editing: {Path(path).name}"
        status_text.color = TEXT
        dirty_badge.visible = False
        dirty_badge.update()
        status_text.update()

    file_tree.on_select = do_select_file

    def log(msg):
        output_log.value += msg + "\n"
        output_log.update()

    def toast(msg, color=GREEN):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=color, duration=2000)
        page.snack_bar.open = True
        page.update()

    def on_save(e):
        if editor.save():
            status_text.value = f"Saved: {Path(editor.current_file).name}"
            status_text.color = GREEN
            dirty_badge.visible = False
            status_text.update()
            dirty_badge.update()
            toast("File saved!")
        else:
            toast("No file open", YELLOW)

    def on_generate(e):
        output_log.value = ""
        output_log.update()

        base_path = fields["base_path"].value
        if not base_path.startswith("/"):
            base_path = "/" + base_path
        if not base_path.endswith("/"):
            base_path = base_path + "/"

        if editor.is_dirty():
            editor.save()
            status_text.value = "Saved before build"
            status_text.color = YELLOW
            dirty_badge.visible = False
            dirty_badge.update()
            status_text.update()

        def run():
            try:
                log(f"Generating with base path: {base_path}")
                generate_site(
                    DEFAULTS["content"],
                    DEFAULTS["template"],
                    DEFAULTS["output"],
                    DEFAULTS["static"],
                    base_path,
                )
                log("Done!")
                toast("Site generated!")
            except Exception as exc:
                log(f"Error: {str(exc)}")
                toast(f"Failed: {str(exc)}", RED)

        threading.Thread(target=run, daemon=True).start()

    def on_preview(e):
        output = DEFAULTS["output"]
        if not output or not os.path.exists(output):
            log("Error: output directory does not exist. Build first.")
            return

        log("Preview on http://localhost:8888")

        def serve():
            os.chdir(output)
            with socketserver.TCPServer(("", 8888), http.server.SimpleHTTPRequestHandler) as httpd:
                log("Serving at http://localhost:8888")
                httpd.serve_forever()

        threading.Thread(target=serve, daemon=True).start()

    def on_new_file(e):
        def do_create(_):
            name = new_name_field.value.strip()
            if not name:
                return
            if not name.endswith(".md"):
                name += ".md"
            path = os.path.join(DEFAULTS["content"], name)
            if os.path.exists(path):
                toast("File already exists", RED)
                return
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# {name.replace('.md', '')}\n\n")
            file_tree.reload(DEFAULTS["content"])
            editor.open_file(path)
            do_select_file(path)
            sidebar.update()
            close_dialog()

        new_name_field = make_input(label="File name", value="untitled.md")

        page.dialog = ft.AlertDialog(
            title=ft.Text("New File"),
            content=ft.Column([new_name_field], tight=True, spacing=12),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
                ft.FilledButton("Create", on_click=do_create),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog.open = True
        page.update()

    def close_dialog():
        if page.dialog:
            page.dialog.open = False
            page.update()

    def open_folder(_):
        if sys.platform == "win32":
            os.startfile(DEFAULTS["content"])
        elif sys.platform == "darwin":
            os.system(f'open "{DEFAULTS["content"]}"')
        else:
            os.system(f'xdg-open "{DEFAULTS["content"]}"')

    # -- Sidebar --
    sidebar = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(Icons.BOLT, size=18, color=ACCENT),
                            ft.Text("Quickmark", size=16, color=TEXT, weight="bold"),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                ),
                ft.Divider(color=BORDER, height=1),
                ft.Container(height=4),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("EXPLORER", size=11, color=MUTED, weight="bold"),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=Icons.ADD,
                                icon_size=16,
                                icon_color=MUTED,
                                on_click=on_new_file,
                                tooltip="New file",
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                ),
                file_tree.build(DEFAULTS["content"]),
                ft.Container(expand=True),
                ft.Divider(color=BORDER, height=1),
                ft.Container(height=4),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(Icons.FOLDER, size=14, color=DIM),
                            ft.Text("content/", size=12, color=MUTED),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=Icons.OPEN_IN_NEW,
                                icon_size=14,
                                icon_color=DIM,
                                on_click=open_folder,
                                tooltip="Open folder",
                            ),
                        ],
                        spacing=6,
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                ),
            ],
            spacing=0,
        ),
        width=SIDEBAR_W,
        bgcolor=SIDEBAR,
        border=ft.border.only(right=ft.border.BorderSide(1, BORDER)),
    )

    # -- Main tab bar --
    tab_line = ft.Container(height=3, bgcolor=ACCENT, border_radius=1)

    def make_tab_btn(label, idx):
        return ft.Container(
            content=ft.Text(label, size=14, color=ACCENT if idx == 0 else MUTED, weight="bold"),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            on_click=lambda e: switch_main_tab(idx),
            data=idx,
            bgcolor=ACCENT if idx == 0 else None,
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
        )

    editor_tab_btn = make_tab_btn("Editor", 0)
    themes_tab_btn = make_tab_btn("Themes", 1)
    settings_tab_btn = make_tab_btn("Settings", 2)

    main_tab_bar = ft.Container(
        content=ft.Row(
            [
                editor_tab_btn,
                themes_tab_btn,
                settings_tab_btn,
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Row(
                        [
                            dirty_badge,
                            status_text,
                            ft.IconButton(
                                icon=Icons.SAVE,
                                icon_size=18,
                                icon_color=MUTED,
                                on_click=on_save,
                                tooltip="Save",
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.only(right=16),
                ),
            ],
            spacing=0,
        ),
        bgcolor=CARD,
        border=ft.border.only(bottom=ft.border.BorderSide(1, BORDER)),
        padding=ft.padding.only(left=8),
    )

    # -- Editor tab content --
    editor_tab_content = ft.Container(
        content=editor.field,
        expand=True,
        visible=True,
    )

    # -- Themes tab content --
    provider_label = ft.Text("", size=11, color=ACCENT)

    api_key_field = make_input(
        label="AI API Key (Groq or OpenRouter)",
        password=True,
        can_reveal_password=True,
        on_change=lambda e: _update_provider(),
    )

    def _update_provider():
        key = api_key_field.value.strip()
        provider = detect_provider(key)
        if provider == "groq":
            provider_label.value = "Groq (llama-3.1-8b-instant)"
            provider_label.color = GREEN
        elif provider == "openrouter":
            provider_label.value = "OpenRouter (llama-3.1-8b-instruct)"
            provider_label.color = BLUE
        else:
            provider_label.value = "Unrecognized key format" if key else ""
            provider_label.color = RED if key else MUTED
        themes_tab_content.update()

    ai_prompt = ft.TextField(
        label="Describe the vibe",
        multiline=True,
        min_lines=2,
        max_lines=3,
        border_radius=8,
        filled=True,
        bgcolor=INPUT_BG,
        color=TEXT,
        border_color="transparent",
        focused_border_color=ACCENT,
        cursor_color=ACCENT,
        text_size=13,
    )

    ai_status = ft.Text("", size=12, color=MUTED)

    def on_test_key(e):
        key = api_key_field.value.strip()
        if not key:
            ai_status.value = "Enter a key first"
            ai_status.color = RED
            themes_tab_content.update()
            return

        ai_status.value = "Testing..."
        ai_status.color = BLUE
        themes_tab_content.update()

        def run_test():
            success, msg = test_api_key(key)
            ai_status.value = msg
            ai_status.color = GREEN if success else RED
            themes_tab_content.update()

        threading.Thread(target=run_test, daemon=True).start()

    def on_generate_theme(e):
        key = api_key_field.value.strip().replace('"', '').replace("'", "")
        if not key:
            ai_status.value = "Please enter your API key"
            ai_status.color = RED
            themes_tab_content.update()
            return

        ai_status.value = "Generating... (may take 10-20s)"
        ai_status.color = BLUE
        themes_tab_content.update()

        def run_gen_sync():
            try:
                css = generate_theme(ai_prompt.value or "Modern, beautiful, animated dark theme", DEFAULTS["content"], key)
                apply_theme("ai-theme", css, DEFAULTS["static"])
                ai_status.value = "Theme applied!"
                ai_status.color = GREEN
                update_preview(css)
            except Exception as exc:
                ai_status.value = f"Error: {str(exc)}"
                ai_status.color = RED
            themes_tab_content.update()

        threading.Thread(target=run_gen_sync, daemon=True).start()

    offline_status = ft.Text("", size=12, color=MUTED)

    mood_dropdown = ft.Dropdown(
        label="Mood",
        options=[ft.dropdown.Option(m) for m in MOOD_PALETTES.keys()],
        value="dark_calm",
        border_radius=8,
        filled=True,
        bgcolor=INPUT_BG,
        color=TEXT,
        border_color="transparent",
        focused_border_color=ACCENT,
        content_padding=12,
        text_size=13,
    )

    style_dropdown = ft.Dropdown(
        label="Style",
        options=[ft.dropdown.Option(s) for s in ["modern", "minimal", "bold"]],
        value="modern",
        border_radius=8,
        filled=True,
        bgcolor=INPUT_BG,
        color=TEXT,
        border_color="transparent",
        focused_border_color=ACCENT,
        content_padding=12,
        text_size=13,
    )

    def on_generate_offline(e):
        mood = mood_dropdown.value or "dark_calm"
        style = style_dropdown.value or "modern"
        css = generate_offline_theme(mood=mood, style=style, animation="smooth")
        name = f"Offline ({mood.replace('_', ' ').title()})"
        apply_theme(name, css, DEFAULTS["static"])
        offline_status.value = f"Applied: {name}"
        offline_status.color = GREEN
        update_preview(css)
        themes_tab_content.update()

    preview_container = ft.Container(
        content=ft.Column([
            ft.Icon(Icons.PREVIEW, size=48, color=DIM),
            ft.Text("No theme loaded yet", size=14, color=MUTED),
            ft.Text("Generate or select a theme to preview", size=12, color=DIM),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=INPUT_BG,
        border_radius=8,
        border=ft.border.all(1, BORDER),
        padding=24,
        expand=True,
    )

    preview_btn = ft.OutlinedButton(
        "Open in Browser",
        icon=Icons.OPEN_IN_BROWSER,
        visible=False,
        on_click=lambda e: open_preview_browser(),
    )

    preview_info = ft.Text("", size=11, color=DIM)

    def open_preview_browser():
        if os.path.exists(temp_preview_path):
            webbrowser.open(f"file://{temp_preview_path}")

    def update_preview(css):
        base_css = open(os.path.join(DEFAULTS["static"], "styles.css"), "r", encoding="utf-8").read()
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
{base_css}
{css}
</style>
</head>
<body>
<div class="page-container">
<nav class="top-nav">
<a class="nav-link" href="/">Главная</a>
<a class="nav-link" href="/blog/">Блог</a>
<a class="nav-link" href="/contact/">Контакты</a>
</nav>
{SAMPLE_CONTENT}
</div>
</body>
</html>"""
        global temp_preview_path
        temp_preview_path = os.path.join(tempfile.gettempdir(), "quickmark_preview.html")
        with open(temp_preview_path, "w", encoding="utf-8") as f:
            f.write(html)
        preview_container.content = ft.Column([
            ft.Row([
                ft.Icon(Icons.CHECK_CIRCLE, size=20, color=GREEN),
                ft.Text("Preview ready", size=13, color=TEXT, weight="bold"),
            ]),
            preview_btn,
            preview_info,
        ], spacing=8)
        preview_btn.visible = True
        preview_info.value = f"File: {temp_preview_path}"
        preview_container.update()

    theme_dropdown = ft.Dropdown(
        label="Quick Themes",
        options=[ft.dropdown.Option(name) for name in PRELOADED_THEMES.keys()],
        border_radius=8,
        filled=True,
        bgcolor=INPUT_BG,
        color=TEXT,
        border_color="transparent",
        focused_border_color=ACCENT,
        content_padding=12,
        text_size=13,
    )

    def on_preloaded_theme(e):
        name = theme_dropdown.value
        css = PRELOADED_THEMES.get(name, "")
        apply_theme(name, css, DEFAULTS["static"])
        ai_status.value = f"Applied: {name}"
        ai_status.color = GREEN
        update_preview(css)
        themes_tab_content.update()

    cp_bg = ColorPicker("Background", "#1a1b26")
    cp_surface = ColorPicker("Surface", "#24283b")
    cp_text = ColorPicker("Text", "#c0caf5")
    cp_primary = ColorPicker("Primary", "#7aa2f7")
    cp_accent = ColorPicker("Accent", "#9ece6a")
    cp_muted = ColorPicker("Muted", "#565f89")

    custom_status = ft.Text("", size=12, color=MUTED)

    custom_name_field = make_input(label="Theme Name", value="My Custom Theme", width=250)

    def _hex_to_rgba(hex_color, alpha):
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgba({r},{g},{b},{alpha})"
        return f"rgba(100,100,100,{alpha})"

    def on_apply_custom(e):
        p = cp_primary.value
        bg_rgba = _hex_to_rgba(p, 0.1)
        css = f""":root {{ --bg: {cp_bg.value}; --surface: {cp_surface.value}; --text: {cp_text.value}; --primary: {cp_primary.value}; --accent: {cp_accent.value}; --muted: {cp_muted.value}; }}
html {{ scroll-behavior: smooth; }}
body {{ background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }}
.page-container {{ max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }}
.top-nav {{ display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }}
.nav-link {{ color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 6px; transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1); }}
.nav-link:hover {{ color: var(--text); background: {bg_rgba}; text-decoration: none; transform: translateY(-1px); }}
h1, h2, h3 {{ color: var(--text); transition: color 0.3s ease, text-shadow 0.3s ease; }}
h1:hover, h2:hover, h3:hover {{ color: var(--primary); text-shadow: 0 0 15px {bg_rgba.replace("0.1", "0.25")}; }}
h1 {{ font-size: clamp(1.8rem, 4vw, 2.6rem); }}
h2 {{ font-size: clamp(1.3rem, 3vw, 1.8rem); }}
h1::after, h2::after {{ content: ''; display: block; width: 40px; height: 3px; background: var(--primary); margin-top: 10px; border-radius: 3px; transition: width 0.4s cubic-bezier(0.22, 1, 0.36, 1); }}
h1:hover::after, h2:hover::after {{ width: 80px; }}
a {{ color: var(--primary); text-decoration: none; position: relative; transition: color 0.3s ease; }}
a::after {{ content: ''; position: absolute; bottom: -2px; left: 0; width: 0; height: 1px; background: var(--primary); transition: width 0.3s cubic-bezier(0.22, 1, 0.36, 1); }}
a:hover::after {{ width: 100%; }}
pre {{ background: var(--surface); border-radius: 8px; padding: 1.2em; border-left: 3px solid var(--primary); transition: all 0.3s ease; }}
pre:hover {{ box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
code {{ background: {bg_rgba}; color: var(--primary); padding: 2px 6px; border-radius: 4px; font-size: 0.88em; }}
pre code {{ background: none; color: var(--text); }}
blockquote {{ border-left: 3px solid var(--accent); background: var(--surface); padding: 1em 1.5em; border-radius: 0 8px 8px 0; color: var(--muted); }}
blockquote:hover {{ border-left-color: var(--primary); }}
li {{ margin-bottom: 6px; transition: transform 0.2s ease; }}
li:hover {{ transform: translateX(3px); }}
li::marker {{ color: var(--accent); }}
img {{ border-radius: 8px; transition: transform 0.3s ease; }}
img:hover {{ transform: scale(1.01); }}
hr {{ border: none; height: 1px; background: var(--surface); margin: 2em 0; }}
p {{ animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }}
p:nth-child(2) {{ animation-delay: 0.08s; }}
p:nth-child(3) {{ animation-delay: 0.14s; }}
p:nth-child(4) {{ animation-delay: 0.2s; }}
::selection {{ background: {bg_rgba.replace("0.1", "0.3")}; color: #fff; }}
::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: {bg_rgba.replace("0.1", "0.2")}; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {bg_rgba.replace("0.1", "0.4")}; }}
@keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(25px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes slideDown {{ from {{ opacity: 0; transform: translateY(-12px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
"""
        name = custom_name_field.value or "Custom Theme"
        apply_theme(name, css, DEFAULTS["static"])
        custom_status.value = f"Applied: {name}"
        custom_status.color = GREEN
        update_preview(css)
        themes_tab_content.update()

    def on_custom_change(_):
        p = cp_primary.value
        bg_rgba = _hex_to_rgba(p, 0.1)
        css = f""":root {{ --bg: {cp_bg.value}; --surface: {cp_surface.value}; --text: {cp_text.value}; --primary: {cp_primary.value}; --accent: {cp_accent.value}; --muted: {cp_muted.value}; }}
body {{ background: var(--bg); color: var(--text); }}
h1, h2, h3 {{ color: var(--text); }}
h1:hover, h2:hover, h3:hover {{ color: var(--primary); text-shadow: 0 0 15px {bg_rgba.replace("0.1", "0.25")}; transition: all 0.3s ease; }}
a {{ color: var(--primary); }}
.nav-link {{ color: var(--muted); }}
.nav-link:hover {{ color: var(--text); background: {bg_rgba}; text-decoration: none; }}
"""
        update_preview(css)

    for cp in [cp_bg, cp_surface, cp_text, cp_primary, cp_accent, cp_muted]:
        cp.on_change = on_custom_change

    themes_left = ft.Container(
        content=ft.Column([
            ft.Text("AI Theme Studio", size=14, color=MUTED, weight="bold"),
            ft.Container(height=8),
            api_key_field,
            ft.Container(height=4),
            provider_label,
            ft.Container(height=8),
            ai_prompt,
            ft.Container(height=10),
            ft.Row([
                ft.FilledButton("Generate", icon=Icons.AUTO_AWESOME, on_click=on_generate_theme, expand=True),
                ft.Container(width=6),
                ft.OutlinedButton("Test Key", icon=Icons.CHECK, on_click=on_test_key, expand=True),
            ]),
            ft.Container(height=8),
            ai_status,
            ft.Container(height=16),
            ft.Divider(color=BORDER, height=1),
            ft.Container(height=12),
            ft.Text("Offline Generator", size=14, color=MUTED, weight="bold"),
            ft.Container(height=8),
            mood_dropdown,
            ft.Container(height=6),
            style_dropdown,
            ft.Container(height=10),
            ft.FilledButton("Generate Offline", icon=Icons.PALETTE, on_click=on_generate_offline, expand=True),
            ft.Container(height=6),
            offline_status,
            ft.Container(height=16),
            ft.Divider(color=BORDER, height=1),
            ft.Container(height=12),
            ft.Text("Quick Themes", size=14, color=MUTED, weight="bold"),
            ft.Container(height=8),
            theme_dropdown,
            ft.Container(height=16),
            ft.Divider(color=BORDER, height=1),
            ft.Container(height=12),
            ft.Text("Custom Theme Builder", size=14, color=MUTED, weight="bold"),
            ft.Container(height=8),
            custom_name_field,
            ft.Container(height=6),
            cp_bg.build(),
            cp_surface.build(),
            cp_text.build(),
            cp_primary.build(),
            cp_accent.build(),
            cp_muted.build(),
            ft.Container(height=8),
            ft.Row([
                ft.FilledButton("Preview", icon=Icons.VISIBILITY, on_click=lambda e: on_custom_change(None), expand=True),
                ft.Container(width=6),
                ft.FilledButton("Apply & Build", icon=Icons.CHECK, on_click=on_apply_custom, expand=True),
            ]),
            ft.Container(height=6),
            custom_status,
        ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
        expand=True,
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
    )

    themes_right = ft.Container(
        content=ft.Column([
            ft.Text("Live Preview", size=14, color=MUTED, weight="bold"),
            ft.Container(height=8),
            preview_container,
        ], expand=True),
        width=500,
        bgcolor=CARD,
        border=ft.border.only(left=ft.border.BorderSide(1, BORDER)),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
    )

    themes_tab_content = ft.Container(
        content=ft.Row(
            [themes_left, themes_right],
            expand=True,
            spacing=0,
        ),
        expand=True,
        visible=False,
    )

    # -- Settings tab content --
    settings_tab_content = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text("Deployment Settings", size=16, color=TEXT, weight="bold"),
                    padding=ft.padding.only(bottom=12),
                ),
                ft.Text("Choose your deployment target and configure base paths.", size=13, color=MUTED),
                ft.Container(height=16),
                ft.Row([
                    ft.Text("Target:", size=13, color=TEXT, weight="bold"),
                    mode_toggle,
                ], spacing=12),
                ft.Container(height=12),
                fields["base_path"],
                ft.Container(height=24),
                ft.Divider(color=BORDER, height=1),
                ft.Container(height=16),
                ft.Row([
                    ft.Text("Content Directory:", size=13, color=TEXT, weight="bold"),
                    ft.Text(DEFAULTS["content"], size=12, color=MUTED),
                    ft.Container(expand=True),
                    ft.IconButton(icon=Icons.OPEN_IN_NEW, icon_size=16, icon_color=MUTED, on_click=open_folder),
                ]),
                ft.Container(height=8),
                ft.Row([
                    ft.Text("Template:", size=13, color=TEXT, weight="bold"),
                    ft.Text(DEFAULTS["template"], size=12, color=MUTED),
                ]),
                ft.Container(height=8),
                ft.Row([
                    ft.Text("Static:", size=13, color=TEXT, weight="bold"),
                    ft.Text(DEFAULTS["static"], size=12, color=MUTED),
                ]),
                ft.Container(height=8),
                ft.Row([
                    ft.Text("Output:", size=13, color=TEXT, weight="bold"),
                    ft.Text(DEFAULTS["output"], size=12, color=MUTED),
                ]),
                ft.Container(height=24),
                ft.Divider(color=BORDER, height=1),
                ft.Container(height=16),
                ft.Row([
                    ft.FilledButton("Generate Site", icon=Icons.PLAY_ARROW, on_click=on_generate, expand=True),
                    ft.Container(width=8),
                    ft.OutlinedButton("Preview Server", icon=Icons.LANGUAGE, on_click=on_preview, expand=True),
                ]),
                ft.Container(height=16),
                output_log,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        expand=True,
        visible=False,
        padding=ft.padding.all(24),
    )

    def switch_main_tab(idx):
        editor_tab_content.visible = idx == 0
        themes_tab_content.visible = idx == 1
        settings_tab_content.visible = idx == 2

        for btn, i in [(editor_tab_btn, 0), (themes_tab_btn, 1), (settings_tab_btn, 2)]:
            btn.content.color = ACCENT if i == idx else MUTED
            btn.bgcolor = ACCENT if i == idx else None

        center_area.update()

    # -- Editor header bar --
    editor_header = ft.Container(
        content=ft.Row(
            [
                ft.Icon(Icons.DESCRIPTION, size=16, color=MUTED),
                ft.Text("Editor", size=14, color=TEXT, weight="bold"),
                ft.Container(expand=True),
                ft.Text("Ctrl+S to save", size=11, color=DIM),
            ],
            spacing=8,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
    )

    # -- Center area --
    center_area = ft.Container(
        content=ft.Column(
            [
                main_tab_bar,
                ft.Container(height=32),
                editor_header,
                ft.Container(height=4),
                ft.Divider(color=BORDER, height=1),
                ft.Stack(
                    [
                        editor_tab_content,
                        themes_tab_content,
                        settings_tab_content,
                    ],
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        ),
        expand=True,
    )

    # -- Main layout --
    page.add(
        ft.Row(
            [
                sidebar,
                center_area,
            ],
            expand=True,
            spacing=0,
        )
    )


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER)
