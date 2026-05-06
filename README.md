# Static Site Generator

A fast, Python-based static site generator that converts Markdown into beautiful HTML — powered by **Flet** and managed with **uv**.

## Features

- **Markdown to HTML** — full inline support for `**bold**`, `_italic_`, `` `code` ``, [links](url), and ![images](url)
- **Block-level parsing** — headings (h1–h6), paragraphs, code blocks, blockquotes, ordered and unordered lists
- **HTML templating** — shared template with `{{ Title }}` and `{{ Content }}` placeholders
- **Recursive content** — nested directories generate nested pages automatically
- **Static assets** — CSS, images copied seamlessly
- **GitHub Pages ready** — configurable base path for subdirectory hosting
- **Web GUI** — beautiful dark-themed Flet interface
- **Zero dependencies** — Python standard library only for the core engine

## Quick Start

### Prerequisites

- [uv](https://github.com/astral-sh/uv) package manager
- Python 3.13+

### Install

```bash
uv sync
```

### Generate the Site

```bash
./main.sh
# or
uv run src/main.py
```

### Preview Locally

```bash
./main.sh
# Site serves at http://localhost:8888
```

### Launch the GUI

```bash
./gui.sh
# or
uv run gui.py
```

### Production Build (GitHub Pages)

```bash
./build.sh
# Outputs to public/ with base path /static-site-generator/
```

### Run Tests

```bash
./test.sh
# or
uv run python -m unittest discover -s src
```

## Project Structure

```
├── content/              # Markdown source files
│   ├── index.md          # Home page
│   ├── blog/             # Blog section
│   └── contact/          # Contact page
├── static/               # CSS, images, and other assets
│   └── styles.css
├── public/               # Generated site output (do not edit)
├── template.html         # HTML page template
├── src/                  # Core engine
│   ├── main.py           # Entry point and orchestrator
│   ├── generate_page.py  # Page generation and Markdown conversion
│   ├── markdown_blocks.py # Block-level Markdown parsing
│   ├── inline_markdown.py # Inline Markdown parsing
│   ├── htmlnode.py       # HTML node classes
│   └── textnode.py       # Text node classes
├── gui.py                # Flet web GUI
├── pyproject.toml        # uv project configuration
├── main.sh               # Build and serve locally
├── build.sh              # Production build script
├── test.sh               # Test runner
└── gui.sh                # Launch GUI
```

## Customizing Your Site

### Edit Content

All pages are Markdown files in `content/`. The directory structure mirrors the URL structure:

| File | URL |
|------|-----|
| `content/index.md` | `/` |
| `content/blog/index.md` | `/blog/` |
| `content/blog/post1.md` | `/blog/post1` |

Create new pages by adding `.md` files — they auto-generate on build.

### Add Images

1. Place files in `static/images/`
2. Reference in any Markdown file: `![alt text](/images/photo.png)`

### Change Styling

Edit `static/styles.css` — changes apply to all pages instantly.

### Change Page Layout

Edit `template.html` to modify the HTML wrapper. Placeholders are replaced automatically:

```html
{{ Title }}   → Extracted from the first H1 heading
{{ Content }} → Converted Markdown content
```

## Markdown Support

| Syntax | Example | Output |
|--------|---------|--------|
| Heading | `## Title` | `<h2>Title</h2>` |
| Bold | `**text**` | `<b>text</b>` |
| Italic | `_text_` | `<i>text</i>` |
| Code | `` `code` `` | `<code>code</code>` |
| Code block | `` ```...``` `` | `<pre><code>...</code></pre>` |
| Link | `[text](url)` | `<a href="url">text</a>` |
| Image | `![alt](url)` | `<img src="url" alt="alt">` |
| Quote | `> quote` | `<blockquote>quote</blockquote>` |
| Ordered list | `1. item` | `<ol><li>item</li></ol>` |
| Unordered list | `- item` | `<ul><li>item</li></ul>` |

## Deployment

Push to GitHub and enable GitHub Pages on the `public/` directory. For subdirectory hosting, run:

```bash
uv run src/main.py "/your-repo-name/"
```

## GUI

The web GUI runs in your browser and provides:

- Pre-filled field defaults for quick generation
- Live output log
- One-click preview server launch
- Dark, minimal design

Run `uv run gui.py` and access the URL printed in the terminal.
