import re
from htmlnode import LeafNode, ParentNode
from inline_markdown import text_to_textnodes
from textnode import text_node_to_html_node, TextNode, TextType


def markdown_to_blocks(markdown):
    blocks = []
    lines = markdown.split("\n")
    current_block = []
    in_code_block = False

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            current_block.append(line)
        elif in_code_block:
            current_block.append(line)
        elif line.strip() == "":
            if current_block:
                blocks.append("\n".join(current_block).strip())
                current_block = []
        else:
            current_block.append(line)

    if current_block:
        blocks.append("\n".join(current_block).strip())

    return blocks


def block_to_block_type(block):
    lines = block.split("\n")
    first_line = lines[0].strip()

    if first_line.startswith("#"):
        heading_match = re.match(r'^(#{1,6})\s', first_line)
        if heading_match:
            return "heading"

    if first_line.startswith("```") and lines[-1].strip().startswith("```"):
        return "code"

    if first_line.startswith(">"):
        return "quote"

    if re.match(r'^\d+\.\s', first_line):
        return "ordered_list"

    if first_line.startswith("- ") or first_line.startswith("* "):
        return "unordered_list"

    return "paragraph"


def block_to_block_type_html(block):
    block_type = block_to_block_type(block)

    if block_type == "heading":
        return text_to_heading(block)
    elif block_type == "code":
        return text_to_code_block(block)
    elif block_type == "quote":
        return text_to_quote(block)
    elif block_type == "ordered_list":
        return text_to_ordered_list(block)
    elif block_type == "unordered_list":
        return text_to_unordered_list(block)
    elif block_type == "paragraph":
        return text_to_paragraph(block)
    else:
        raise ValueError(f"Unknown block type: {block_type}")


def text_to_heading(block):
    lines = block.split("\n")
    match = re.match(r'^(#{1,6})\s(.*)', lines[0])
    if not match:
        raise ValueError("Invalid heading")

    level = len(match.group(1))
    heading_content = match.group(2)
    tag = f"h{level}"

    text_nodes = text_to_textnodes(heading_content)
    children = [text_node_to_html_node(node) for node in text_nodes]

    heading_node = ParentNode(tag, children)

    if len(lines) > 1:
        remaining = "\n".join(lines[1:])
        if remaining.strip():
            p_nodes = text_to_textnodes(remaining)
            p_children = [text_node_to_html_node(node) for node in p_nodes]
            return ParentNode("div", [heading_node, ParentNode("p", p_children)])

    return heading_node


def text_to_paragraph(block):
    text_nodes = text_to_textnodes(block)
    children = [text_node_to_html_node(node) for node in text_nodes]
    return ParentNode("p", children)


def text_to_code_block(block):
    lines = block.split("\n")
    code_content = "\n".join(lines[1:-1])
    return ParentNode("pre", [LeafNode("code", code_content)])


def text_to_quote(block):
    lines = block.split("\n")
    quote_lines = [line.lstrip("> ").strip() for line in lines]
    quote_content = " ".join(quote_lines)
    text_nodes = text_to_textnodes(quote_content)
    children = [text_node_to_html_node(node) for node in text_nodes]
    return ParentNode("blockquote", children)


def text_to_ordered_list(block):
    lines = block.split("\n")
    children = []
    for line in lines:
        content = re.sub(r'^\d+\.\s', '', line).strip()
        try:
            text_nodes = text_to_textnodes(content)
        except ValueError:
            text_nodes = [TextNode(content, TextType.TEXT)]
        item_children = [text_node_to_html_node(node) for node in text_nodes]
        children.append(ParentNode("li", item_children))
    return ParentNode("ol", children)


def text_to_unordered_list(block):
    lines = block.split("\n")
    children = []
    for line in lines:
        if line.startswith("- "):
            content = line[2:].strip()
        elif line.startswith("* "):
            content = line[2:].strip()
        else:
            content = line.strip()
        try:
            text_nodes = text_to_textnodes(content)
        except ValueError:
            text_nodes = [TextNode(content, TextType.TEXT)]
        item_children = [text_node_to_html_node(node) for node in text_nodes]
        children.append(ParentNode("li", item_children))
    return ParentNode("ul", children)
