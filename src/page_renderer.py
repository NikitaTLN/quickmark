import re
import os
from htmlnode import ParentNode
from markdown_blocks import markdown_to_blocks, block_to_block_type_html


def extract_title(markdown):
    match = re.match(r'^#\s+(.*)', markdown.strip())
    if match:
        return match.group(1)
    return None


def markdown_to_html(markdown):
    blocks = markdown_to_blocks(markdown)
    html_blocks = []
    for block in blocks:
        if block.startswith("```") and block.endswith("```"):
            lines = block.split("\n")
            code_content = "\n".join(lines[1:-1])
            html_blocks.append(f"<pre><code>{code_content}</code></pre>")
        else:
            html_node = block_to_block_type_html(block)
            html_blocks.append(html_node.to_html())
    return "\n".join(html_blocks)


def generate_page(markdown, template, base_path="/", relative_prefix=""):
    title = extract_title(markdown)
    if title is None:
        title = "No Title"

    html_content = markdown_to_html(markdown)

    page = template.replace("{{ Title }}", title)
    page = page.replace("{{ Content }}", html_content)

    if relative_prefix:
        page = re.sub(
            r'href="([^"]*\.html)"',
            lambda m: f'href="{relative_prefix}{m.group(1)}"',
            page,
        )
        page = page.replace('href="styles.css"', f'href="{relative_prefix}styles.css"')
        page = page.replace('href="ai-theme.css"', f'href="{relative_prefix}ai-theme.css"')
    else:
        page = page.replace('href="/', f'href="{base_path}')
        page = page.replace('src="/', f'src="{base_path}')

    return page


def get_dir_files(directory):
    files = []
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        if os.path.isfile(full_path):
            files.append(full_path)
        else:
            files.extend(get_dir_files(full_path))
    return files
