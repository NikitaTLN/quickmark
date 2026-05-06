import os
import sys
import threading
import http.server
import socketserver
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
RIGHT_PANEL_W = 360


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
    page.window_width = 1280
    page.window_height = 750
    page.window_min_width = 980
    page.window_min_height = 600

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

    # -- Editor area --
    editor_area = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            dirty_badge,
                            status_text,
                            ft.Container(expand=True),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=Icons.SAVE,
                                        icon_size=18,
                                        icon_color=MUTED,
                                        on_click=on_save,
                                        tooltip="Save",
                                    ),
                                ],
                                spacing=4,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                ),
                ft.Divider(color=BORDER, height=1),
                editor.field,
            ],
            spacing=0,
            expand=True,
        ),
        expand=True,
    )

    # -- Right panel --
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
        right_panel.update()

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
            right_panel.update()
            return

        ai_status.value = "Testing..."
        ai_status.color = BLUE
        right_panel.update()

        def run_test():
            success, msg = test_api_key(key)
            ai_status.value = msg
            ai_status.color = GREEN if success else RED
            right_panel.update()

        threading.Thread(target=run_test, daemon=True).start()

    def on_generate_theme(e):
        key = api_key_field.value.strip().replace('"', '').replace("'", "")
        if not key:
            ai_status.value = "Please enter your API key"
            ai_status.color = RED
            right_panel.update()
            return

        ai_status.value = "Generating... (may take 10-20s)"
        ai_status.color = BLUE
        right_panel.update()

        def run_gen_sync():
            try:
                css = generate_theme(ai_prompt.value or "Modern, beautiful, animated dark theme", DEFAULTS["content"], key)
                apply_theme("ai-theme", css, DEFAULTS["static"])
                ai_status.value = "Theme applied! Rebuild to preview."
                ai_status.color = GREEN
                update_preview(css)
                on_generate(e)
            except Exception as exc:
                ai_status.value = f"Error: {str(exc)}"
                ai_status.color = RED
            right_panel.update()

        threading.Thread(target=run_gen_sync, daemon=True).start()

    def on_preloaded_theme(e):
        name = theme_dropdown.value
        css = PRELOADED_THEMES.get(name, "")
        apply_theme(name, css, DEFAULTS["static"])
        ai_status.value = f"Applied: {name}"
        ai_status.color = GREEN
        update_preview(css)
        on_generate(e)
        right_panel.update()

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
        on_select=on_preloaded_theme,
    )

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
        on_generate(e)
        right_panel.update()

    preview_container = ft.Container(
        content=ft.Text("Select or generate a theme to see preview", size=12, color=MUTED, text_align=ft.TextAlign.CENTER),
        bgcolor=INPUT_BG,
        border_radius=8,
        border=ft.border.all(1, BORDER),
        padding=0,
        height=300,
    )

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
        preview_container.content = ft.Html(html, expand=True)
        preview_container.update()

    tab_line = ft.Container(height=2, bgcolor=ACCENT, border_radius=1)
    settings_tab_btn = ft.Container(
        content=ft.Text("Settings", size=13, color=ACCENT, weight="bold"),
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        on_click=lambda e: switch_tab(0),
        data=0,
    )
    themes_tab_btn = ft.Container(
        content=ft.Text("Themes", size=13, color=MUTED, weight="bold"),
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        on_click=lambda e: switch_tab(1),
        data=1,
    )

    tab_bar = ft.Container(
        content=ft.Column([
            ft.Row(
                [
                    settings_tab_btn,
                    themes_tab_btn,
                    ft.Container(expand=True),
                ],
                spacing=0,
            ),
            tab_line,
        ],
        spacing=0,
        ),
        margin=ft.margin.only(left=-16, right=-16, top=-16, bottom=8),
    )

    def switch_tab(idx):
        settings_card.visible = idx == 0
        themes_card.visible = idx == 1
        if idx == 0:
            settings_tab_btn.content.color = ACCENT
            themes_tab_btn.content.color = MUTED
            tab_line.parent.controls[0].controls[0] = settings_tab_btn
        else:
            themes_tab_btn.content.color = ACCENT
            settings_tab_btn.content.color = MUTED
        right_panel.update()

    themes_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("AI Theme Studio", size=13, color=MUTED, weight="bold"),
                        ft.Container(expand=True),
                        ft.TextButton(
                            "Groq",
                            url="https://console.groq.com/keys",
                            style=ft.ButtonStyle(color=ACCENT, padding=0),
                            icon=ft.Icon(Icons.OPEN_IN_NEW, size=12, color=ACCENT),
                        ),
                        ft.Container(width=4),
                        ft.TextButton(
                            "OpenRouter",
                            url="https://openrouter.ai/settings/keys",
                            style=ft.ButtonStyle(color=ACCENT, padding=0),
                            icon=ft.Icon(Icons.OPEN_IN_NEW, size=12, color=ACCENT),
                        ),
                    ],
                    spacing=0,
                ),
                ft.Container(height=8),
                api_key_field,
                ft.Container(height=4),
                provider_label,
                ft.Container(height=8),
                ai_prompt,
                ft.Container(height=10),
                ft.Row(
                    [
                        ft.FilledButton(
                            "Generate Theme",
                            icon=Icons.AUTO_AWESOME,
                            on_click=on_generate_theme,
                            expand=True,
                        ),
                        ft.Container(width=6),
                        ft.OutlinedButton(
                            "Test Key",
                            icon=Icons.CHECK,
                            on_click=on_test_key,
                            expand=True,
                        ),
                    ],
                    spacing=0,
                ),
                ft.Container(height=8),
                ai_status,
                ft.Container(height=16),
                ft.Divider(color=BORDER, height=1),
                ft.Container(height=12),
                ft.Text("Offline Theme Generator", size=13, color=MUTED, weight="bold"),
                ft.Container(height=8),
                mood_dropdown,
                ft.Container(height=6),
                style_dropdown,
                ft.Container(height=10),
                ft.FilledButton(
                    "Generate Offline",
                    icon=Icons.PALETTE,
                    on_click=on_generate_offline,
                    expand=True,
                ),
                ft.Container(height=6),
                offline_status,
                ft.Container(height=16),
                ft.Divider(color=BORDER, height=1),
                ft.Container(height=12),
                ft.Text("Live Preview", size=13, color=MUTED, weight="bold"),
                ft.Container(height=8),
                preview_container,
                ft.Container(height=12),
                ft.Divider(color=BORDER, height=1),
                ft.Container(height=12),
                theme_dropdown,
            ],
            spacing=0,
        ),
        expand=True,
    )

    settings_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Deployment", size=13, color=MUTED, weight="bold"),
                ft.Container(height=8),
                mode_toggle,
                ft.Container(height=10),
                fields["base_path"],
                ft.Container(height=12),
                ft.Row(
                    [
                        ft.FilledButton(
                            "Generate",
                            icon=Icons.PLAY_ARROW,
                            on_click=on_generate,
                            expand=True,
                        ),
                        ft.Container(width=6),
                        ft.OutlinedButton(
                            "Preview",
                            icon=Icons.LANGUAGE,
                            on_click=on_preview,
                            expand=True,
                        ),
                    ],
                    spacing=0,
                ),
                ft.Container(height=12),
                output_log,
            ],
            spacing=0,
        ),
        expand=True,
    )

    settings_card.visible = True
    themes_card.visible = False

    right_panel = ft.Container(
        content=ft.Column(
            [
                tab_bar,
                ft.Container(
                    content=ft.Column(
                        [
                            settings_card,
                            themes_card,
                        ],
                        spacing=0,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=4),
                    expand=True,
                ),
            ],
            spacing=0,
        ),
        width=RIGHT_PANEL_W,
        bgcolor=SIDEBAR,
        border=ft.border.only(left=ft.border.BorderSide(1, BORDER)),
    )

    # -- Main layout --
    page.add(
        ft.Row(
            [
                sidebar,
                editor_area,
                right_panel,
            ],
            expand=True,
            spacing=0,
        )
    )


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER)
