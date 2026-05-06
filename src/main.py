import os
import sys
import shutil
from generate_page import generate_page, get_dir_files


def generate_site(content_dir, template_path, output_dir, static_dir, base_path="/"):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    with open(template_path, "r") as f:
        template = f.read()

    md_files = get_dir_files(content_dir)

    for md_file in md_files:
        with open(md_file, "r") as f:
            markdown = f.read()

        relative_path = os.path.relpath(md_file, content_dir)
        output_path = os.path.join(output_dir, relative_path.replace(".md", ".html"))

        output_file_dir = os.path.dirname(output_path)
        if not os.path.exists(output_file_dir):
            os.makedirs(output_file_dir)

        html = generate_page(markdown, template, base_path)

        with open(output_path, "w") as f:
            f.write(html)

        print(f"Generated: {output_path}")

    shutil.copytree(static_dir, output_dir, dirs_exist_ok=True)
    print(f"Copied static assets from {static_dir} to {output_dir}")


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
    output_dir = os.path.join(project_root, "public")
    static_dir = os.path.join(project_root, "static")

    print(f"Generating site with base path: {base_path}")
    generate_site(content_dir, template_path, output_dir, static_dir, base_path)
    print("Site generation complete!")


if __name__ == "__main__":
    main()
