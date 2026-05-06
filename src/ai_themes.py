import os
import re
import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are a world-class CSS designer. Your job is to create stunning, modern, fully-animated CSS themes for static blog-style websites.

CRITICAL RULES:
- Return ONLY the raw CSS code. No markdown backticks, no ```css, no explanations.
- Use CSS custom properties (variables) in :root for all colors.
- Style every element: body, h1-h6, p, a, code, pre, blockquote, ul, ol, li, img, hr.
- Always include a .page-container class (centered content with max-width).
- Always include a .top-nav class and .nav-link class for the navigation bar.
- The CSS must be responsive and look great on all screen sizes.

ANIMATION REQUIREMENTS:
- Page load animation on .page-container (fade-in, slide-up, or zoom-in, 0.6-1s duration).
- Smooth hover transitions on ALL interactive elements (links, headings, buttons).
- Subtle glow effects on links and headings using box-shadow or text-shadow.
- Animated underline or color shift on link hover (not just plain color change).
- Staggered entrance animations for paragraphs (each p element fades in slightly delayed).
- Hover effects on headings: scale, glow, or animated underline.
- Code blocks should have a subtle border animation or gradient shift on hover.
- Blockquotes should have a sliding or glowing left border on hover.
- Smooth background gradients with optional slow animated gradient shift.
- Use cubic-bezier easing for all transitions (e.g., cubic-bezier(0.4, 0, 0.2, 1)) for professional feel.

DESIGN REQUIREMENTS:
- Use glassmorphism (backdrop-filter: blur, semi-transparent backgrounds) for at least one element.
- Modern color palette with high contrast and good readability.
- Custom scrollbar styling for webkit browsers.
- Selection color should match the theme.
- Use ::before or ::after pseudo-elements on headings for decorative accents.
- Smooth scroll behavior: scroll-behavior: smooth.
- Custom focus-visible styles for accessibility.

RESPONSIVENESS:
- Use clamp() for font sizes on headings and paragraphs.
- @media queries for screens under 768px and 480px.
- Navigation bar should wrap gracefully on small screens."""


def detect_provider(api_key):
    key = api_key.strip()
    if key.startswith("gsk_"):
        return "groq"
    if key.startswith("sk-or-"):
        return "openrouter"
    return None


def get_provider_url(provider):
    if provider == "groq":
        return GROQ_URL
    if provider == "openrouter":
        return OPENROUTER_URL
    return GROQ_URL


def get_provider_model(provider):
    if provider == "groq":
        return "llama-3.1-8b-instant"
    if provider == "openrouter":
        return "meta-llama/llama-3.1-8b-instruct"
    return "llama-3.1-8b-instant"


def get_content_context(content_dir):
    sample = ""
    for root, _, files in os.walk(content_dir):
        for f in files:
            if f.endswith(".md"):
                with open(os.path.join(root, f), "r", encoding="utf-8") as fh:
                    sample += fh.read(300) + "\n---\n"
    return sample[:2000]

import os
import re
import json

def validate_api_key(api_key):
    api_key = api_key.strip().replace('"', '').replace("'", "")
    provider = detect_provider(api_key)
    if provider == "groq":
        return True, "Valid Groq key"
    if provider == "openrouter":
        return True, "Valid OpenRouter key"
    return False, "Key should start with 'gsk_' (Groq) or 'sk-or-' (OpenRouter)."


def test_api_key(api_key):
    import httpx
    api_key = api_key.strip().replace('"', '').replace("'", '')

    provider = detect_provider(api_key)
    if not provider:
        return False, "Unrecognized key format. Should start with 'gsk_' or 'sk-or-'."

    debug_info = []
    debug_info.append(f"Provider: {provider}")
    debug_info.append(f"Key starts with: {api_key[:10]}...")
    debug_info.append(f"Key length: {len(api_key)}")

    url = get_provider_url(provider)
    model = get_provider_model(provider)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if provider == "openrouter":
        headers["HTTP-Referer"] = "http://localhost"
        headers["X-Title"] = "Quickmark SSG"

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                url,
                headers=headers,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 1,
                },
            )
            debug_info.append(f"HTTP status: {resp.status_code}")
            debug_info.append(f"Response: {resp.text[:300]}")

            if resp.status_code == 200:
                return True, f"Key is valid! (via {provider})"
            else:
                return False, f"Error {resp.status_code}:\n" + "\n".join(debug_info)
    except Exception as e:
        return False, f"Connection failed: {str(e)}\n" + "\n".join(debug_info)

def generate_theme(prompt, content_dir, api_key):
    api_key = api_key.strip().replace('"', '').replace("'", "")
    context = get_content_context(content_dir)
    user_prompt = f"Project context:\n{context}\n\nUser request: {prompt}\n\nMake it stunning."

    provider = detect_provider(api_key)
    if not provider:
        raise ValueError("Unrecognized API key format. Use 'gsk_' (Groq) or 'sk-or-' (OpenRouter).")

    url = get_provider_url(provider)
    model = get_provider_model(provider)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if provider == "openrouter":
        headers["HTTP-Referer"] = "http://localhost"
        headers["X-Title"] = "Quickmark SSG"

    import httpx
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            url,
            headers=headers,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.8,
            },
        )
        if resp.status_code == 401:
            raise Exception(f"Invalid API key for {provider}. Check the key has no extra spaces.")
        resp.raise_for_status()
        css = resp.json()["choices"][0]["message"]["content"]
        return re.sub(r'^```css\s*|\s*```$', '', css).strip()

PRELOADED_THEMES = {
    "Default": "",
    "NvChad OneDark": """
:root { --bg: #1e222a; --surface: #282c34; --text: #abb2bf; --primary: #61afef; --accent: #98c379; --muted: #565c64; --red: #e06c75; --purple: #c678dd; --cyan: #56b6c2; --yellow: #e5c07b; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 6px; transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1); }
.nav-link:hover { color: var(--primary); background: rgba(97,175,239,0.08); text-decoration: none; transform: translateY(-1px); }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease, text-shadow 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--primary); text-shadow: 0 0 20px rgba(97,175,239,0.2); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h2 { font-size: clamp(1.3rem, 3vw, 1.8rem); }
h1::after, h2::after { content: ''; display: block; width: 40px; height: 3px; background: var(--primary); margin-top: 10px; border-radius: 3px; transition: width 0.4s cubic-bezier(0.22, 1, 0.36, 1); }
h1:hover::after, h2:hover::after { width: 80px; }
a { color: var(--primary); text-decoration: none; position: relative; transition: color 0.3s ease; }
a::after { content: ''; position: absolute; bottom: -2px; left: 0; width: 0; height: 1px; background: var(--primary); transition: width 0.3s cubic-bezier(0.22, 1, 0.36, 1); }
a:hover::after { width: 100%; }
pre { background: var(--surface); border-radius: 8px; padding: 1.2em; border: 1px solid rgba(97,175,239,0.1); transition: border-color 0.3s ease; }
pre:hover { border-color: rgba(97,175,239,0.3); }
code { background: rgba(97,175,239,0.1); color: var(--primary); padding: 2px 6px; border-radius: 4px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--accent); background: var(--surface); padding: 1em 1.5em; border-radius: 0 8px 8px 0; color: var(--muted); transition: border-left-width 0.3s ease; }
blockquote:hover { border-left-width: 5px; }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--primary); }
img { border-radius: 8px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(97,175,239,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(97,175,239,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(97,175,239,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad Catppuccin": """
:root { --bg: #1E1D2D; --surface: #2d2c3c; --text: #D9E0EE; --primary: #89B4FA; --accent: #ABE9B3; --muted: #585B70; --red: #F38BA8; --purple: #CBA6F7; --cyan: #89DCEB; --yellow: #FAE3B0; --orange: #F8BD96; --lavender: #c7d1ff; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 12px 16px; margin-bottom: 32px; background: var(--surface); border-radius: 10px; flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 8px; transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1); }
.nav-link:hover { color: var(--lavender); background: rgba(137,180,250,0.08); text-decoration: none; }
h1, h2, h3 { color: var(--text); }
h1:hover, h2:hover, h3:hover { color: var(--purple); text-shadow: 0 0 20px rgba(203,166,247,0.2); transition: all 0.3s ease; }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); color: var(--primary); }
h2 { font-size: clamp(1.3rem, 3vw, 1.8rem); color: var(--accent); }
h1::after { content: ''; display: block; width: 40px; height: 3px; background: var(--primary); margin-top: 10px; border-radius: 3px; transition: width 0.4s cubic-bezier(0.22, 1, 0.36, 1); }
h1:hover::after { width: 80px; }
a { color: var(--primary); text-decoration: none; position: relative; }
a::after { content: ''; position: absolute; bottom: -2px; left: 0; width: 100%; height: 1px; background: var(--primary); transform: scaleX(0); transform-origin: right; transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1); }
a:hover::after { transform: scaleX(1); transform-origin: left; }
pre { background: var(--surface); border-radius: 8px; padding: 1.2em; border: 1px solid rgba(203,166,247,0.1); transition: border-color 0.3s ease; }
pre:hover { border-color: rgba(203,166,247,0.3); }
code { background: rgba(203,166,247,0.1); color: var(--purple); padding: 2px 6px; border-radius: 4px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--accent); background: var(--surface); padding: 1em 1.5em; border-radius: 0 8px 8px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--primary); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--accent); }
img { border-radius: 8px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(203,166,247,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(137,180,250,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(137,180,250,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad Tokyonight": """
:root { --bg: #1a1b26; --surface: #24283b; --text: #c0caf5; --primary: #7aa2f7; --accent: #9ece6a; --muted: #565f89; --red: #f7768e; --purple: #bb9af7; --cyan: #7dcfff; --orange: #ff9e64; --yellow: #e0af68; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 6px; transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1); }
.nav-link:hover { color: var(--primary); background: rgba(122,162,247,0.08); text-decoration: none; }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease, text-shadow 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--primary); text-shadow: 0 0 15px rgba(122,162,247,0.25); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h1::after { content: ''; display: block; width: 40px; height: 3px; background: linear-gradient(90deg, var(--primary), var(--cyan)); margin-top: 10px; border-radius: 3px; transition: width 0.4s cubic-bezier(0.22, 1, 0.36, 1); }
h1:hover::after { width: 80px; }
a { color: var(--cyan); text-decoration: none; position: relative; transition: color 0.3s ease; }
a:hover { color: var(--primary); }
a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 100%; height: 1px; background: var(--primary); transform: scaleX(0); transform-origin: right; transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1); }
a:hover::after { transform: scaleX(1); transform-origin: left; }
pre { background: var(--surface); border-radius: 8px; padding: 1.2em; border-left: 3px solid var(--cyan); transition: all 0.3s ease; }
pre:hover { box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
code { background: rgba(122,162,247,0.1); color: var(--primary); padding: 2px 6px; border-radius: 4px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--primary); background: var(--surface); padding: 1em 1.5em; border-radius: 0 8px 8px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--accent); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--accent); }
img { border-radius: 8px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(122,162,247,0.2), transparent); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(122,162,247,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(122,162,247,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(122,162,247,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad Gruvbox": """
:root { --bg: #282828; --surface: #353535; --text: #ebdbb2; --primary: #83a598; --accent: #b8bb26; --muted: #7c6f64; --red: #fb4934; --purple: #d3869b; --cyan: #8ec07c; --yellow: #fabd2f; --orange: #e78a4e; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 4px; transition: all 0.25s ease; }
.nav-link:hover { color: var(--primary); background: rgba(131,165,152,0.1); text-decoration: none; }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--primary); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h1::after { content: ''; display: block; width: 50px; height: 3px; background: var(--yellow); margin-top: 10px; border-radius: 3px; transition: width 0.4s ease; }
h1:hover::after { width: 100px; }
a { color: var(--primary); text-decoration: none; position: relative; }
a:hover { color: var(--yellow); }
a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 2px; background: var(--yellow); transition: width 0.3s ease; }
a:hover::after { width: 100%; }
pre { background: var(--surface); border-radius: 6px; padding: 1.2em; border: 1px solid rgba(131,165,152,0.15); transition: border-color 0.3s ease; }
pre:hover { border-color: rgba(131,165,152,0.4); }
code { background: rgba(184,187,38,0.1); color: var(--accent); padding: 2px 6px; border-radius: 3px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--yellow); background: var(--surface); padding: 1em 1.5em; border-radius: 0 6px 6px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--accent); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--accent); }
img { border-radius: 6px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(250,189,47,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(131,165,152,0.3); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(131,165,152,0.5); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad Nord": """
:root { --bg: #2E3440; --surface: #373d49; --text: #D8DEE9; --primary: #81A1C1; --accent: #A3BE8C; --muted: #4C566A; --red: #BF616A; --purple: #B48EAD; --cyan: #88C0D0; --yellow: #EBCB8B; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 4px; transition: all 0.25s ease; }
.nav-link:hover { color: var(--primary); background: rgba(129,161,193,0.1); text-decoration: none; }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--primary); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h1::after { content: ''; display: block; width: 50px; height: 3px; background: var(--cyan); margin-top: 10px; border-radius: 3px; transition: width 0.4s ease; }
h1:hover::after { width: 80px; }
a { color: var(--primary); text-decoration: none; position: relative; }
a:hover { color: var(--cyan); }
a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 1px; background: var(--cyan); transition: width 0.3s ease; }
a:hover::after { width: 100%; }
pre { background: var(--surface); border-radius: 6px; padding: 1.2em; border-left: 3px solid var(--cyan); transition: border-left-color 0.3s ease; }
pre:hover { border-left-color: var(--primary); }
code { background: rgba(129,161,193,0.1); color: var(--primary); padding: 2px 6px; border-radius: 3px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--accent); background: var(--surface); padding: 1em 1.5em; border-radius: 0 6px 6px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--primary); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--accent); }
img { border-radius: 6px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(129,161,193,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(129,161,193,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(129,161,193,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad Dracula": """
:root { --bg: #282A36; --surface: #373844; --text: #F8F8F2; --primary: #BD93F9; --accent: #50fa7b; --muted: #626483; --red: #ff7070; --pink: #FF79C6; --cyan: #8BE9FD; --yellow: #F1FA8C; --orange: #FFB86C; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 6px; transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1); }
.nav-link:hover { color: var(--primary); background: rgba(189,147,249,0.08); text-decoration: none; transform: translateY(-1px); }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease, text-shadow 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--pink); text-shadow: 0 0 15px rgba(255,121,198,0.25); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h1::after { content: ''; display: block; width: 40px; height: 3px; background: linear-gradient(90deg, var(--primary), var(--pink)); margin-top: 10px; border-radius: 3px; transition: width 0.4s ease; }
h1:hover::after { width: 80px; }
a { color: var(--cyan); text-decoration: none; position: relative; transition: color 0.3s ease; }
a:hover { color: var(--accent); }
a::after { content: ''; position: absolute; bottom: -2px; left: 0; width: 0; height: 1px; background: var(--primary); transition: width 0.3s cubic-bezier(0.22, 1, 0.36, 1); }
a:hover::after { width: 100%; }
pre { background: var(--surface); border-radius: 8px; padding: 1.2em; border: 1px solid rgba(189,147,249,0.1); transition: border-color 0.3s ease; }
pre:hover { border-color: rgba(189,147,249,0.3); }
code { background: rgba(189,147,249,0.1); color: var(--primary); padding: 2px 6px; border-radius: 4px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--pink); background: var(--surface); padding: 1em 1.5em; border-radius: 0 8px 8px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--primary); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--primary); }
img { border-radius: 8px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(189,147,249,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(189,147,249,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(189,147,249,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad Kanagawa": """
:root { --bg: #1F1F28; --surface: #272730; --text: #DCD7BA; --primary: #7E9CD8; --accent: #98BB6C; --muted: #54546D; --red: #d8616b; --pink: #D27E99; --purple: #9c86bf; --yellow: #FF9E3B; --cyan: #A3D4D5; --orange: #fa9b61; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 4px; transition: all 0.25s ease; }
.nav-link:hover { color: var(--primary); background: rgba(126,156,216,0.08); text-decoration: none; }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--pink); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h1::after { content: ''; display: block; width: 40px; height: 3px; background: linear-gradient(90deg, var(--primary), var(--pink)); margin-top: 10px; border-radius: 3px; transition: width 0.4s ease; }
h1:hover::after { width: 80px; }
a { color: var(--primary); text-decoration: none; position: relative; }
a:hover { color: var(--pink); }
a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 1px; background: var(--primary); transition: width 0.3s ease; }
a:hover::after { width: 100%; }
pre { background: var(--surface); border-radius: 6px; padding: 1.2em; border-left: 3px solid var(--primary); transition: border-left-color 0.3s ease; }
pre:hover { border-left-color: var(--accent); }
code { background: rgba(126,156,216,0.1); color: var(--primary); padding: 2px 6px; border-radius: 3px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--accent); background: var(--surface); padding: 1em 1.5em; border-radius: 0 6px 6px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--primary); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--accent); }
img { border-radius: 6px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(210,126,153,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(126,156,216,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(126,156,216,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad Doom": """
:root { --bg: #282c34; --surface: #32363e; --text: #bbc2cf; --primary: #51afef; --accent: #98be65; --muted: #53575f; --red: #ff6b5a; --purple: #dc8ef3; --cyan: #46D9FF; --yellow: #ECBE7B; --orange: #ea9558; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 4px; transition: all 0.25s ease; }
.nav-link:hover { color: var(--primary); background: rgba(81,175,239,0.08); text-decoration: none; }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--primary); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h1::after { content: ''; display: block; width: 50px; height: 3px; background: var(--orange); margin-top: 10px; border-radius: 3px; transition: width 0.4s ease; }
h1:hover::after { width: 80px; }
a { color: var(--primary); text-decoration: none; position: relative; }
a:hover { color: var(--orange); }
a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 1px; background: var(--primary); transition: width 0.3s ease; }
a:hover::after { width: 100%; }
pre { background: var(--surface); border-radius: 6px; padding: 1.2em; border-left: 3px solid var(--orange); transition: border-left-color 0.3s ease; }
pre:hover { border-left-color: var(--primary); }
code { background: rgba(81,175,239,0.1); color: var(--primary); padding: 2px 6px; border-radius: 3px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--accent); background: var(--surface); padding: 1em 1.5em; border-radius: 0 6px 6px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--primary); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--accent); }
img { border-radius: 6px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(81,175,239,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(81,175,239,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(81,175,239,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad Everforest": """
:root { --bg: #2b3339; --surface: #363e44; --text: #D3C6AA; --primary: #7393b3; --accent: #83c092; --muted: #626a70; --red: #e67e80; --purple: #d699b6; --cyan: #95d1c9; --yellow: #dbbc7f; --orange: #e69875; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 4px; transition: all 0.25s ease; }
.nav-link:hover { color: var(--accent); background: rgba(131,192,146,0.08); text-decoration: none; }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--accent); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h1::after { content: ''; display: block; width: 40px; height: 3px; background: var(--yellow); margin-top: 10px; border-radius: 3px; transition: width 0.4s ease; }
h1:hover::after { width: 80px; }
a { color: var(--accent); text-decoration: none; position: relative; }
a:hover { color: var(--yellow); }
a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 1px; background: var(--accent); transition: width 0.3s ease; }
a:hover::after { width: 100%; }
pre { background: var(--surface); border-radius: 6px; padding: 1.2em; border-left: 3px solid var(--accent); transition: border-left-color 0.3s ease; }
pre:hover { border-left-color: var(--yellow); }
code { background: rgba(131,192,146,0.1); color: var(--accent); padding: 2px 6px; border-radius: 3px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--yellow); background: var(--surface); padding: 1em 1.5em; border-radius: 0 6px 6px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--accent); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--accent); }
img { border-radius: 6px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(131,192,146,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(131,192,146,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(131,192,146,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad Decay": """
:root { --bg: #171B20; --surface: #262a2f; --text: #dee1e6; --primary: #86aaec; --accent: #78DBA9; --muted: #494d52; --red: #e26c7c; --purple: #c68aee; --cyan: #98d3ee; --yellow: #ecd3a0; --orange: #e9a180; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 6px; transition: all 0.25s ease; }
.nav-link:hover { color: var(--accent); background: rgba(120,219,169,0.08); text-decoration: none; }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease, text-shadow 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--accent); text-shadow: 0 0 15px rgba(120,219,169,0.2); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h1::after { content: ''; display: block; width: 40px; height: 3px; background: var(--purple); margin-top: 10px; border-radius: 3px; transition: width 0.4s ease; }
h1:hover::after { width: 80px; }
a { color: var(--primary); text-decoration: none; position: relative; }
a:hover { color: var(--cyan); }
a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 1px; background: var(--primary); transition: width 0.3s ease; }
a:hover::after { width: 100%; }
pre { background: var(--surface); border-radius: 8px; padding: 1.2em; border: 1px solid rgba(134,170,236,0.1); transition: border-color 0.3s ease; }
pre:hover { border-color: rgba(134,170,236,0.3); }
code { background: rgba(134,170,236,0.1); color: var(--primary); padding: 2px 6px; border-radius: 4px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--accent); background: var(--surface); padding: 1em 1.5em; border-radius: 0 8px 8px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--primary); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--accent); }
img { border-radius: 8px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(198,138,238,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(134,170,236,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(134,170,236,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad Oxocarbon": """
:root { --bg: #161616; --surface: #262626; --text: #f2f4f8; --primary: #78a9ff; --accent: #42be65; --muted: #525252; --red: #ee5396; --purple: #be95ff; --cyan: #33b1ff; --yellow: #fdd06c; --orange: #ff7eb6; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 4px; transition: all 0.25s ease; }
.nav-link:hover { color: var(--primary); background: rgba(120,169,255,0.08); text-decoration: none; }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease, text-shadow 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--primary); text-shadow: 0 0 15px rgba(120,169,255,0.2); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h1::after { content: ''; display: block; width: 40px; height: 3px; background: var(--cyan); margin-top: 10px; border-radius: 3px; transition: width 0.4s ease; }
h1:hover::after { width: 80px; }
a { color: var(--cyan); text-decoration: none; position: relative; }
a:hover { color: var(--primary); }
a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 1px; background: var(--cyan); transition: width 0.3s ease; }
a:hover::after { width: 100%; }
pre { background: var(--surface); border-radius: 6px; padding: 1.2em; border-left: 3px solid var(--cyan); transition: border-left-color 0.3s ease; }
pre:hover { border-left-color: var(--primary); }
code { background: rgba(120,169,255,0.1); color: var(--primary); padding: 2px 6px; border-radius: 3px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--accent); background: var(--surface); padding: 1em 1.5em; border-radius: 0 6px 6px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--primary); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--accent); }
img { border-radius: 6px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(120,169,255,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(120,169,255,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(120,169,255,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad NightOwl": """
:root { --bg: #011627; --surface: #0b253a; --text: #d6deeb; --primary: #82aaff; --accent: #22da6e; --muted: #403f53; --red: #ef5350; --purple: #c792ea; --cyan: #7fdbca; --yellow: #c792ea; --orange: #f78c6c; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 4px; transition: all 0.25s ease; }
.nav-link:hover { color: var(--primary); background: rgba(130,170,255,0.08); text-decoration: none; }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease, text-shadow 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--primary); text-shadow: 0 0 15px rgba(130,170,255,0.2); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h1::after { content: ''; display: block; width: 40px; height: 3px; background: var(--cyan); margin-top: 10px; border-radius: 3px; transition: width 0.4s ease; }
h1:hover::after { width: 80px; }
a { color: var(--cyan); text-decoration: none; position: relative; }
a:hover { color: var(--primary); }
a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 1px; background: var(--cyan); transition: width 0.3s ease; }
a:hover::after { width: 100%; }
pre { background: var(--surface); border-radius: 6px; padding: 1.2em; border-left: 3px solid var(--primary); transition: border-left-color 0.3s ease; }
pre:hover { border-left-color: var(--cyan); }
code { background: rgba(130,170,255,0.1); color: var(--primary); padding: 2px 6px; border-radius: 3px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--primary); background: var(--surface); padding: 1em 1.5em; border-radius: 0 6px 6px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--cyan); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--primary); }
img { border-radius: 6px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(130,170,255,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(130,170,255,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(130,170,255,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad NightFox": """
:root { --bg: #192330; --surface: #232e40; --text: #cdcecf; --primary: #719cd6; --accent: #81b29a; --muted: #444b5a; --red: #c94f4d; --purple: #9d79d6; --cyan: #63cdcf; --yellow: #dbc074; --orange: #f4a261; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 4px; transition: all 0.25s ease; }
.nav-link:hover { color: var(--accent); background: rgba(129,178,154,0.08); text-decoration: none; }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--accent); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h1::after { content: ''; display: block; width: 40px; height: 3px; background: var(--orange); margin-top: 10px; border-radius: 3px; transition: width 0.4s ease; }
h1:hover::after { width: 80px; }
a { color: var(--primary); text-decoration: none; position: relative; }
a:hover { color: var(--cyan); }
a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 1px; background: var(--primary); transition: width 0.3s ease; }
a:hover::after { width: 100%; }
pre { background: var(--surface); border-radius: 6px; padding: 1.2em; border-left: 3px solid var(--accent); transition: border-left-color 0.3s ease; }
pre:hover { border-left-color: var(--primary); }
code { background: rgba(113,156,214,0.1); color: var(--primary); padding: 2px 6px; border-radius: 3px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--accent); background: var(--surface); padding: 1em 1.5em; border-radius: 0 6px 6px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--primary); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--accent); }
img { border-radius: 6px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(113,156,214,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(113,156,214,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(113,156,214,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
    "NvChad Palenight": """
:root { --bg: #292D3E; --surface: #333747; --text: #babed8; --primary: #82aaff; --accent: #c3e88d; --muted: #546e7a; --red: #f07178; --purple: #c792ea; --cyan: #89ddff; --yellow: #ffcb6b; --orange: #f78c6c; }
html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.7; }
.page-container { max-width: 900px; margin: 0 auto; padding: 48px 24px; animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
.top-nav { display: flex; gap: 4px; padding: 10px 0; margin-bottom: 32px; border-bottom: 1px solid var(--surface); flex-wrap: wrap; animation: slideDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both; }
.nav-link { color: var(--muted); text-decoration: none; font-size: 0.9rem; font-weight: 500; padding: 8px 16px; border-radius: 4px; transition: all 0.25s ease; }
.nav-link:hover { color: var(--primary); background: rgba(130,170,255,0.08); text-decoration: none; }
h1, h2, h3 { color: var(--text); transition: color 0.3s ease, text-shadow 0.3s ease; }
h1:hover, h2:hover, h3:hover { color: var(--primary); text-shadow: 0 0 15px rgba(130,170,255,0.2); }
h1 { font-size: clamp(1.8rem, 4vw, 2.6rem); }
h1::after { content: ''; display: block; width: 40px; height: 3px; background: var(--purple); margin-top: 10px; border-radius: 3px; transition: width 0.4s ease; }
h1:hover::after { width: 80px; }
a { color: var(--primary); text-decoration: none; position: relative; }
a:hover { color: var(--cyan); }
a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 1px; background: var(--primary); transition: width 0.3s ease; }
a:hover::after { width: 100%; }
pre { background: var(--surface); border-radius: 6px; padding: 1.2em; border-left: 3px solid var(--primary); transition: border-left-color 0.3s ease; }
pre:hover { border-left-color: var(--purple); }
code { background: rgba(130,170,255,0.1); color: var(--primary); padding: 2px 6px; border-radius: 3px; font-size: 0.88em; }
pre code { background: none; color: var(--text); }
blockquote { border-left: 3px solid var(--accent); background: var(--surface); padding: 1em 1.5em; border-radius: 0 6px 6px 0; color: var(--muted); }
blockquote:hover { border-left-color: var(--primary); }
li { margin-bottom: 6px; transition: transform 0.2s ease; }
li:hover { transform: translateX(3px); }
li::marker { color: var(--accent); }
img { border-radius: 6px; transition: transform 0.3s ease; }
img:hover { transform: scale(1.01); }
hr { border: none; height: 1px; background: var(--surface); margin: 2em 0; }
p { animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
p:nth-child(2) { animation-delay: 0.08s; }
p:nth-child(3) { animation-delay: 0.14s; }
p:nth-child(4) { animation-delay: 0.2s; }
::selection { background: rgba(130,170,255,0.3); color: #fff; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(130,170,255,0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(130,170,255,0.4); }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(25px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideDown { from { opacity: 0; transform: translateY(-12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
""",
}

def apply_theme(name, css_content, static_dir):
    path = os.path.join(static_dir, "ai-theme.css")
    with open(path, "w", encoding="utf-8") as f:
        f.write(css_content)
    return path
