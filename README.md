# Quickmark — Static Site Generator

A fast, cross-platform static site generator with a built-in editor. Write Markdown, generate beautiful HTML — all from one app.

<p align="center">
  <strong>Linux</strong> · <strong>Windows</strong> · <strong>macOS</strong>
</p>

## Features

- **Built-in editor** — create, edit, and save Markdown files without leaving the app
- **File explorer** — browse your project files in a sidebar
- **Markdown to HTML** — full inline support for `**bold**`, `_italic_`, `` `code` ``, [links](url), and ![images](url)
- **Block-level parsing** — headings (h1–h6), paragraphs, code blocks, blockquotes, ordered and unordered lists
- **HTML templating** — shared template with `{{ Title }}` and `{{ Content }}` placeholders
- **Recursive content** — nested directories generate nested pages automatically
- **Static assets** — CSS, images copied seamlessly
- **GitHub Pages ready** — configurable base path for subdirectory hosting
- **Cross-platform** — runs on Linux, Windows, and macOS
- **Zero dependencies** — Python standard library only for the core engine

## Quick Start

### Prerequisites

- [uv](https://github.com/astral-sh/uv) package manager
- Python 3.13+

### Install

```bash
uv sync
```

### Launch the App

```bash
uv run gui.py
```

Opens a web browser with the full editor, file explorer, and build tools.

### Generate the Site (CLI)

```bash
uv run src/main.py
```

### Production Build (GitHub Pages)

```bash
./build.sh
```

### Run Tests

```bash
./test.sh
```

## Project Structure

```
├── content/              # Markdown source files (edit these)
│   ├── index.md          # Home page
│   ├── blog/             # Blog section
│   └── contact/          # Contact page
├── static/               # CSS, images, and other assets
│   └── styles.css
├── docs/                 # Generated site (deploy this on GitHub Pages)
├── template.html         # HTML page template
├── src/                  # Core engine
│   ├── main.py           # Entry point and orchestrator
│   ├── generate_page.py  # Page generation and Markdown conversion
│   ├── markdown_blocks.py # Block-level Markdown parsing
│   ├── inline_markdown.py # Inline Markdown parsing
│   ├── htmlnode.py       # HTML node classes
│   └── textnode.py       # Text node classes
├── gui.py                # Cross-platform GUI with built-in editor
├── pyproject.toml        # uv project configuration
├── build.sh              # Production build script
├── main.sh               # Build and serve locally
├── test.sh               # Test runner
└── gui.sh                # Launch GUI
```

## Using the App

The GUI has three panels:

**Left sidebar** — file explorer showing all editable files (`.md`, `.css`, `.html`, etc.)
- Click any file to open it in the editor
- Click **+** to create a new Markdown file
- Click **⟳** to refresh the file list
- Click the folder icon to open the content directory

**Center** — text editor with monospace font
- Edit any opened file
- Click **Save** (or just hit Generate — it auto-saves dirty files first)

**Right panel** — settings and build controls
- **Base Path** — URL prefix for GitHub Pages (default: `/quickmark/`)
- **Generate** — build the entire site to `docs/`
- **Preview** — start a local server at `http://localhost:8888`

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

## Customizing Your Site

### Edit Content

All pages are Markdown files in `content/`. The directory structure mirrors the URL structure:

| File | URL |
|------|-----|
| `content/index.md` | `/` |
| `content/blog/index.md` | `/blog/` |
| `content/blog/post1.md` | `/blog/post1` |

### Add Images

1. Place files in `static/images/`
2. Reference in any Markdown file: `![alt text](/images/photo.png)`

### Change Styling

Edit `static/styles.css` — open it from the file explorer and save.

### Change Page Layout

Edit `template.html` to modify the HTML wrapper.

## Deployment

### GitHub Pages

1. Push to GitHub
2. **Settings → Pages → Source → Deploy from a branch**
3. Select branch: `main`, folder: `/docs`
4. Click **Save**

For subdirectory hosting, set the **Base Path** in the GUI to `/your-repo-name/` before generating.

Your site will be live at `https://YOUR_USERNAME.github.io/YOUR_REPO/`

### Local Preview

Click **Preview** in the GUI, then open `http://localhost:8888` in your browser.

## Building a Standalone Release

To create a standalone executable (no Python required):

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "content:content" --add-data "static:static" --add-data "template.html:." --add-data "src:src" gui.py
```

The executable will be in `dist/` and works on the same OS it was built on. Build on each platform (Linux, Windows, macOS) for full cross-platform releases.
