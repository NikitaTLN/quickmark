import os
import re
import httpx

SYSTEM_PROMPT = """You are a master CSS designer. You generate beautiful, modern, animated CSS.
Return ONLY the CSS code. No markdown backticks, no explanations.
- Use CSS variables in `:root` for colors.
- Add smooth transitions, hover effects, and subtle animations.
- Use glassmorphism, gradients, or modern styling techniques.
- Style: body, h1-h6, p, a, code, pre, blockquote, ul, ol, li, img, hr.
- Add a .page-container class to center content and add padding.
- Keep it responsive and readable."""

def get_content_context(content_dir):
    sample = ""
    for root, _, files in os.walk(content_dir):
        for f in files:
            if f.endswith(".md"):
                with open(os.path.join(root, f), "r", encoding="utf-8") as fh:
                    sample += fh.read(300) + "\n---\n"
    return sample[:2000]

async def generate_theme(prompt, content_dir, api_key):
    context = get_content_context(content_dir)
    user_prompt = f"Project context:\n{context}\n\nUser request: {prompt}\n\nMake it stunning."

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.8,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        css = resp.json()["choices"][0]["message"]["content"]
        return re.sub(r'^```css\s*|\s*```$', '', css).strip()

PRELOADED_THEMES = {
    "Default": "",
    "Neon Cyberpunk": """
:root { --bg: #05050a; --surface: #0f0f1a; --text: #e0e0ff; --primary: #00ff88; --accent: #ff0055; }
body { background: radial-gradient(circle at 50% 50%, #1a1a2e 0%, #05050a 100%); color: var(--text); font-family: 'Inter', sans-serif; transition: all 0.3s ease; }
h1, h2, h3 { background: linear-gradient(90deg, var(--primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 20px rgba(0, 255, 136, 0.3); }
a { color: var(--primary); transition: 0.2s; }
a:hover { text-shadow: 0 0 10px var(--primary); }
pre, blockquote { background: rgba(255,255,255,0.03); border: 1px solid rgba(0,255,136,0.2); border-radius: 8px; backdrop-filter: blur(10px); }
code { background: rgba(255,0,85,0.2); color: #ff0077; padding: 2px 6px; border-radius: 4px; }
.page-container { max-width: 800px; margin: 0 auto; padding: 40px 20px; animation: fadeIn 1s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
""",
    "Minimalist Light": """
:root { --bg: #f8f9fa; --text: #343a40; --primary: #495057; }
body { background: var(--bg); color: var(--text); font-family: 'Helvetica Neue', sans-serif; line-height: 1.8; }
h1, h2, h3 { letter-spacing: -0.02em; font-weight: 700; color: #212529; border-bottom: 2px solid #e9ecef; padding-bottom: 0.3em; }
a { color: var(--primary); text-decoration: underline; }
blockquote { border-left: 3px solid #6c757d; background: #e9ecef; padding: 1em; font-style: italic; }
pre { background: #e9ecef; border-radius: 4px; padding: 1.5em; }
.page-container { max-width: 700px; margin: 0 auto; padding: 40px 20px; }
""",
}

def apply_theme(name, css_content, static_dir):
    path = os.path.join(static_dir, "ai-theme.css")
    with open(path, "w", encoding="utf-8") as f:
        f.write(css_content)
    return path
