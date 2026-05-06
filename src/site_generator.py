import os
import re
import sys
import shutil
from page_renderer import generate_page, get_dir_files, extract_title


NAV_CONFIG = [
    {"slug": "index", "label": "Главная", "path": "index.html"},
    {"slug": "blog", "label": "Блог", "path": "blog/index.html"},
    {"slug": "contact", "label": "Контакты", "path": "contact/index.html"},
]


def scan_pages(content_dir):
    pages = []
    for root, dirs, files in os.walk(content_dir):
        dirs.sort()
        for item in sorted(files):
            if not item.endswith(".md"):
                continue
            full_path = os.path.join(root, item)
            with open(full_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
            match = re.match(r"^#\s+(.*)", first_line)
            title = match.group(1) if match else item.replace(".md", "")
            rel_path = os.path.relpath(full_path, content_dir)
            slug = rel_path.replace(".md", "")
            if slug.endswith("/index"):
                output_path = f"{slug.replace('/index', '')}/index.html"
            elif "/" in slug:
                output_path = f"{slug}/index.html"
            else:
                output_path = f"{slug}.html"
            pages.append({"title": title, "slug": slug, "path": full_path, "output": output_path})
    return pages


def build_nav_html(pages, base_prefix=""):
    nav_items = []
    for page in pages:
        output = page["output"]
        href = f'{base_prefix}{output}'
        label = page["title"]
        nav_items.append(f'<a class="nav-link" href="{href}">{label}</a>')
    return "\n        ".join(nav_items)


def inject_nav(template, nav_html):
    return template.replace("{{ Nav }}", nav_html)


def generate_site(content_dir, template_path, output_dir, static_dir, base_path="/"):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    with open(template_path, "r", encoding="utf-8") as f:
        original_template = f.read()

    pages = scan_pages(content_dir)

    if "{{ Nav }}" in template:
        nav_html = build_nav_html(pages)
        template = inject_nav(template, nav_html)
    else:
        nav_links = []
        for page in pages:
            if "/" in page["slug"]:
                href = f'{page["slug"]}/index.html'
            else:
                href = f'{page["slug"]}.html'
            nav_links.append(f'<a class="nav-link" href="{href}">{page["title"]}</a>')
        nav_html = "\n        ".join(nav_links)
        template = template.replace(
            "<nav class=\"top-nav\">",
            f'<nav class="top-nav">\n        {nav_html}\n        <!-- DYNAMIC_NAV -->',
        )

    for page in pages:
        with open(page["path"], "r", encoding="utf-8") as f:
            markdown = f.read()

        rel_path = os.path.relpath(page["path"], content_dir)
        output_path = os.path.join(output_dir, page["output"])

        output_file_dir = os.path.dirname(output_path)
        if not os.path.exists(output_file_dir):
            os.makedirs(output_file_dir)

        depth = page["output"].count("/")
        relative_prefix = "../" * depth if depth > 0 else ""

        html = generate_page(markdown, template, base_path, relative_prefix)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Generated: {output_path}")

    shutil.copytree(static_dir, output_dir, dirs_exist_ok=True)
    print(f"Copied static assets from {static_dir} to {output_dir}")


def create_page(content_dir, name, title=None, in_folder=None):
    name = name.strip()
    if not name.endswith(".md"):
        name += ".md"
    if in_folder:
        folder_path = os.path.join(content_dir, in_folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        path = os.path.join(folder_path, name)
    else:
        path = os.path.join(content_dir, name)
    if os.path.exists(path):
        return None, "File already exists"
    page_title = title or name.replace(".md", "").replace("-", " ").title()
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {page_title}\n\n")
    return path, None


def delete_page(path):
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def get_page_list(content_dir):
    return scan_pages(content_dir)


def main():
    base_path = "/"
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
        if not base_path.startswith("/"):
            base_path = "/" + base_path
        if not base_path.endswith("/"):
            base_path = base_path + "/"

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    content_dir = os.path.join(project_root, "content")
    template_path = os.path.join(project_root, "template.html")
    output_dir = os.path.join(project_root, "docs")
    static_dir = os.path.join(project_root, "static")

    print(f"Generating site with base path: {base_path}")
    generate_site(content_dir, template_path, output_dir, static_dir, base_path)
    print("Site generation complete!")


if __name__ == "__main__":
    main()
