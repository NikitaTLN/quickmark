import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from ai_themes import generate_offline_theme, MOOD_PALETTES
from site_generator import generate_site

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def build(content_dir=None, static_dir=None, template=None, output_dir=None, mood=None, style=None, animation=None, base_path=None):
    content_dir = content_dir or os.path.join(PROJECT_ROOT, "content")
    static_dir = static_dir or os.path.join(PROJECT_ROOT, "static")
    template = template or os.path.join(PROJECT_ROOT, "template.html")
    output_dir = output_dir or os.path.join(PROJECT_ROOT, "docs")
    base_path = base_path or "/"

    available_moods = ", ".join(sorted(MOOD_PALETTES.keys()))
    mood = mood or "dark_calm"
    if mood not in MOOD_PALETTES:
        print(f"Error: mood '{mood}' not found. Available: {available_moods}")
        sys.exit(1)

    style = style or "modern"
    animation = animation or "smooth"

    print(f"Generating offline theme: mood={mood}, style={style}, animation={animation}")
    css = generate_offline_theme(mood=mood, style=style, animation=animation)

    theme_path_static = os.path.join(static_dir, "ai-theme.css")
    with open(theme_path_static, "w", encoding="utf-8") as f:
        f.write(css)
    print(f"Theme written to {theme_path_static}")

    theme_path_docs = os.path.join(output_dir, "ai-theme.css")
    os.makedirs(output_dir, exist_ok=True)
    with open(theme_path_docs, "w", encoding="utf-8") as f:
        f.write(css)
    print(f"Theme written to {theme_path_docs}")

    print(f"Generating site with base_path={base_path}")
    generate_site(content_dir, template, output_dir, static_dir, base_path)

    nojekyll_path = os.path.join(output_dir, ".nojekyll")
    with open(nojekyll_path, "w", encoding="utf-8") as f:
        f.write("")
    print(f"Created {nojekyll_path}")

    print(f"Site generated in {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Build static site with offline theme")
    parser.add_argument("--content", help="Content directory (default: ./content)")
    parser.add_argument("--static", help="Static assets directory (default: ./static)")
    parser.add_argument("--template", help="HTML template file (default: ./template.html)")
    parser.add_argument("--output", help="Output directory (default: ./docs)")
    parser.add_argument("--base-path", help="Base path for links (default: /)")
    parser.add_argument("--mood", help=f"Theme mood (default: dark_calm)")
    parser.add_argument("--style", help="Theme style: modern, minimal, bold (default: modern)")
    parser.add_argument("--animation", help="Animation speed: smooth, fast, dramatic (default: smooth)")
    args = parser.parse_args()

    build(
        content_dir=args.content,
        static_dir=args.static,
        template=args.template,
        output_dir=args.output,
        mood=args.mood,
        style=args.style,
        animation=args.animation,
        base_path=args.base_path,
    )


if __name__ == "__main__":
    main()
