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

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULTS = {
    "content": os.path.join(PROJECT_ROOT, "content"),
    "static": os.path.join(PROJECT_ROOT, "static"),
    "template": os.path.join(PROJECT_ROOT, "template.html"),
    "output": os.path.join(PROJECT_ROOT, "docs"),
    "base_path": "/quickmark/",
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

FONT_MONO = "Cascadia Code, Fira Code, Consolas, monospace"


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
            with open(path, "r") as f:
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
            with open(self.current_file, "w") as f:
                f.write(self.field.value)
            self.original = self.field.value
            return True
        return False

    def is_dirty(self):
        return self.field.value != self.original if self.current_file else False


def main(page: ft.Page):
    page.title = "Quickmark — Static Site Generator"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = SURFACE
    page.padding = 0
    page.window_width = 1200
    page.window_height = 750
    page.window_min_width = 900
    page.window_min_height = 600

    editor = Editor()
    file_tree = FileTree(on_select=None)

    status_text = ft.Text("Select a file to edit", size=12, color=MUTED)

    fields = {
        "base_path": ft.TextField(
            label="Base Path",
            value=DEFAULTS["base_path"],
            border_radius=8,
            filled=True,
            bgcolor=INPUT_BG,
            color=TEXT,
            border_color="transparent",
            focused_border_color=ACCENT,
            cursor_color=ACCENT,
            height=44,
            text_size=13,
        )
    }

    output_log = ft.TextField(
        label="Build Output",
        read_only=True,
        multiline=True,
        border_radius=8,
        filled=True,
        bgcolor=INPUT_BG,
        color=MUTED,
        border_color="transparent",
        height=100,
        text_size=12,
    )

    def do_select_file(path):
        editor.open_file(path)
        status_text.value = f"Editing: {Path(path).name}"
        status_text.color = TEXT
        status_text.update()

    file_tree.on_select = do_select_file

    def log(msg):
        output_log.value += msg + "\n"
        output_log.update()

    def on_save(e):
        if editor.save():
            status_text.value = f"Saved: {Path(editor.current_file).name}"
            status_text.color = GREEN
            status_text.update()
            page.show_snack_bar(ft.SnackBar(ft.Text("File saved!"), bgcolor=GREEN, duration=1500))
        else:
            page.show_snack_bar(ft.SnackBar(ft.Text("No file open"), bgcolor=YELLOW, duration=1500))

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
                page.show_snack_bar(ft.SnackBar(ft.Text("Site generated!"), bgcolor=GREEN, duration=2000))
            except Exception as exc:
                log(f"Error: {str(exc)}")
                page.show_snack_bar(ft.SnackBar(ft.Text(f"Failed: {str(exc)}"), bgcolor=RED, duration=3000))

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
                page.show_snack_bar(ft.SnackBar(ft.Text("File already exists"), bgcolor=RED, duration=2000))
                return
            with open(path, "w") as f:
                f.write(f"# {name.replace('.md', '')}\n\n")
            file_tree.reload(DEFAULTS["content"])
            editor.open_file(path)
            do_select_file(path)
            sidebar.update()
            page.close_dialog()

        new_name_field = ft.TextField(
            label="File name",
            value="untitled.md",
            border_radius=8,
            filled=True,
            bgcolor=INPUT_BG,
            color=TEXT,
            border_color="transparent",
            focused_border_color=ACCENT,
            cursor_color=ACCENT,
        )

        page.dialog = ft.AlertDialog(
            title=ft.Text("New File"),
            content=ft.Column([new_name_field], tight=True, spacing=12),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: page.close_dialog()),
                ft.FilledButton("Create", on_click=do_create),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(page.dialog)

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
                ft.Container(height=4),
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
        width=260,
        bgcolor=SIDEBAR,
        border=ft.border.all(1, BORDER),
    )

    # -- Editor area --
    editor_area = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
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
    settings_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Settings", size=13, color=MUTED, weight="bold"),
                fields["base_path"],
                ft.Container(height=8),
                ft.Row(
                    [
                        ft.FilledButton(
                            "Generate",
                            icon=Icons.PLAY_ARROW,
                            on_click=on_generate,
                            height=40,
                        ),
                        ft.OutlinedButton(
                            "Preview",
                            icon=Icons.LANGUAGE,
                            on_click=on_preview,
                            height=40,
                        ),
                    ],
                    spacing=8,
                ),
                ft.Container(height=8),
                output_log,
            ],
            spacing=6,
        ),
        padding=16,
        border_radius=8,
        bgcolor=CARD,
    )

    right_panel = ft.Container(
        content=ft.Column(
            [
                settings_card,
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
        width=280,
        bgcolor=SIDEBAR,
        border=ft.border.all(1, BORDER),
        padding=12,
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
