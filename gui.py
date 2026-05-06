import os
import sys
import threading
import http.server
import socketserver

import flet as ft

Icons = ft.icons.Icons

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from main import generate_site

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULTS = {
    "content": os.path.join(PROJECT_ROOT, "content"),
    "static": os.path.join(PROJECT_ROOT, "static"),
    "template": os.path.join(PROJECT_ROOT, "template.html"),
    "output": os.path.join(PROJECT_ROOT, "public"),
    "base_path": "/",
}

ACCENT = "#6568ff"
SURFACE = "#111827"
CARD = "#1f2937"
INPUT_BG = "#374151"
TEXT = "#f9fafb"
MUTED = "#9ca3af"


def field(label, default):
    return ft.TextField(
        label=label,
        value=default,
        border_radius=8,
        filled=True,
        bgcolor=INPUT_BG,
        color=TEXT,
        border_color="transparent",
        focused_border_color=ACCENT,
        cursor_color=ACCENT,
        text_size=14,
        height=50,
    )


def section(title, children):
    return ft.Container(
        content=ft.Column(
            [ft.Text(title, size=13, color=MUTED, weight="w600"), *children],
            spacing=12,
        ),
        padding=20,
        border_radius=12,
        bgcolor=CARD,
    )


def main(page: ft.Page):
    page.title = "Static Site Generator"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = SURFACE
    page.padding = 32

    content_field = field("Content Directory", DEFAULTS["content"])
    static_field = field("Static Directory", DEFAULTS["static"])
    template_field = field("Template File", DEFAULTS["template"])
    output_field = field("Output Directory", DEFAULTS["output"])
    base_path_field = field("Base Path", DEFAULTS["base_path"])

    output_log = ft.TextField(
        label="Output",
        read_only=True,
        multiline=True,
        border_radius=8,
        filled=True,
        bgcolor=INPUT_BG,
        color=MUTED,
        border_color="transparent",
        height=120,
        text_size=13,
    )

    def log(msg):
        output_log.value += msg + "\n"
        output_log.update()

    def on_generate(e):
        output_log.value = ""
        output_log.update()

        base_path = base_path_field.value
        if not base_path.startswith("/"):
            base_path = "/" + base_path
        if not base_path.endswith("/"):
            base_path = base_path + "/"

        fields = [
            ("Content Directory", content_field),
            ("Static Directory", static_field),
            ("Template File", template_field),
            ("Output Directory", output_field),
        ]
        for name, f in fields:
            if not f.value:
                log(f"Error: {name} is empty")
                return

        def run():
            try:
                log(f"Generating with base path: {base_path}")
                generate_site(
                    content_field.value,
                    template_field.value,
                    output_field.value,
                    static_field.value,
                    base_path,
                )
                log("Done!")
                page.show_snack_bar(ft.SnackBar(ft.Text("Site generated!"), bgcolor="#16a34a", duration=2000))
            except Exception as e:
                log(f"Error: {str(e)}")
                page.show_snack_bar(ft.SnackBar(ft.Text(f"Failed: {str(e)}"), bgcolor="#dc2626", duration=3000))

        threading.Thread(target=run, daemon=True).start()

    def on_preview(e):
        output = output_field.value
        if not output or not os.path.exists(output):
            log("Error: output directory does not exist")
            return
        log("Preview on http://localhost:8888")

        def serve():
            os.chdir(output)
            with socketserver.TCPServer(("", 8888), http.server.SimpleHTTPRequestHandler) as httpd:
                log("Serving at http://localhost:8888")
                httpd.serve_forever()

        threading.Thread(target=serve, daemon=True).start()

    settings_card = section("Settings", [
        ft.Row([ft.Column([content_field], expand=True)], spacing=12),
        ft.Row([ft.Column([static_field], expand=True)], spacing=12),
        ft.Row([ft.Column([template_field], expand=True)], spacing=12),
        ft.Row([ft.Column([output_field], expand=True)], spacing=12),
        ft.Row([
            ft.Column([base_path_field], expand=2),
            ft.Container(width=12),
            ft.Column([
                ft.Row([
                    ft.Button(
                        "Generate",
                        icon=Icons.PLAY_ARROW,
                        bgcolor=ACCENT,
                        color="#ffffff",
                        style=ft.ButtonStyle(
                            padding=ft.Padding.symmetric(horizontal=24, vertical=8),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=on_generate,
                        height=50,
                    ),
                    ft.Button(
                        "Preview",
                        icon=Icons.LANGUAGE,
                        bgcolor=INPUT_BG,
                        color=TEXT,
                        style=ft.ButtonStyle(
                            padding=ft.Padding.symmetric(horizontal=24, vertical=8),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=on_preview,
                        height=50,
                    ),
                ], spacing=8),
            ], expand=1),
        ], spacing=12),
    ])

    page.add(
        ft.Column([
            ft.Text("Static Site Generator", size=20, color=TEXT, weight="bold"),
            ft.Text("Build beautiful static sites from Markdown", size=13, color=MUTED),
            ft.Divider(color=CARD, height=16),
            settings_card,
            ft.Container(height=10),
            output_log,
        ], spacing=8, scroll=ft.ScrollMode.AUTO),
    )


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER)
