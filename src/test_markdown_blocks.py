import unittest
from markdown_blocks import (
    markdown_to_blocks,
    block_to_block_type,
    block_to_block_type_html,
    text_to_heading,
    text_to_paragraph,
    text_to_code_block,
    text_to_quote,
    text_to_ordered_list,
    text_to_unordered_list,
)
from htmlnode import ParentNode, LeafNode


class TestMarkdownToBlocks(unittest.TestCase):
    def test_single_block(self):
        markdown = "Hello, world!"
        self.assertEqual(markdown_to_blocks(markdown), ["Hello, world!"])

    def test_multiple_blocks(self):
        markdown = "Hello, world!\n\nThis is a new paragraph."
        self.assertEqual(
            markdown_to_blocks(markdown),
            ["Hello, world!", "This is a new paragraph."],
        )

    def test_blocks_with_empty_lines(self):
        markdown = "Line 1\n\n\nLine 2"
        self.assertEqual(markdown_to_blocks(markdown), ["Line 1", "Line 2"])


class TestBlockToBlockType(unittest.TestCase):
    def test_paragraph(self):
        self.assertEqual(block_to_block_type("Just a paragraph"), "paragraph")

    def test_heading_1(self):
        self.assertEqual(block_to_block_type("# Heading 1"), "heading")

    def test_heading_2(self):
        self.assertEqual(block_to_block_type("## Heading 2"), "heading")

    def test_heading_6(self):
        self.assertEqual(block_to_block_type("###### Heading 6"), "heading")

    def test_code_block(self):
        block = "```\ncode here\n```"
        self.assertEqual(block_to_block_type(block), "code")

    def test_quote(self):
        self.assertEqual(block_to_block_type("> This is a quote"), "quote")

    def test_ordered_list(self):
        self.assertEqual(block_to_block_type("1. First item"), "ordered_list")

    def test_unordered_list_dash(self):
        self.assertEqual(block_to_block_type("- Item"), "unordered_list")

    def test_unordered_list_asterisk(self):
        self.assertEqual(block_to_block_type("* Item"), "unordered_list")


class TestBlockToHTML(unittest.TestCase):
    def test_heading_to_html(self):
        node = text_to_heading("# Hello")
        self.assertEqual(node.tag, "h1")
        self.assertEqual(node.to_html(), "<h1>Hello</h1>")

    def test_heading_2_to_html(self):
        node = text_to_heading("## Hello")
        self.assertEqual(node.tag, "h2")
        self.assertEqual(node.to_html(), "<h2>Hello</h2>")

    def test_paragraph_to_html(self):
        node = text_to_paragraph("This is a paragraph")
        self.assertEqual(node.tag, "p")
        self.assertEqual(node.to_html(), "<p>This is a paragraph</p>")

    def test_paragraph_with_bold(self):
        node = text_to_paragraph("This is **bold** text")
        self.assertEqual(node.to_html(), "<p>This is <b>bold</b> text</p>")

    def test_code_block_to_html(self):
        block = "```\ndef hello():\n    pass\n```"
        node = text_to_code_block(block)
        self.assertEqual(node.tag, "pre")
        self.assertEqual(node.to_html(), "<pre><code>def hello():\n    pass</code></pre>")

    def test_quote_to_html(self):
        node = text_to_quote("> This is a quote")
        self.assertEqual(node.tag, "blockquote")
        self.assertEqual(node.to_html(), "<blockquote>This is a quote</blockquote>")

    def test_ordered_list_to_html(self):
        block = "1. First\n2. Second\n3. Third"
        node = text_to_ordered_list(block)
        self.assertEqual(node.tag, "ol")
        self.assertEqual(
            node.to_html(),
            "<ol><li>First</li><li>Second</li><li>Third</li></ol>",
        )

    def test_unordered_list_to_html(self):
        block = "- Item 1\n- Item 2\n- Item 3"
        node = text_to_unordered_list(block)
        self.assertEqual(node.tag, "ul")
        self.assertEqual(
            node.to_html(),
            "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>",
        )


class TestMarkdownToHTML(unittest.TestCase):
    def test_full_markdown_to_html(self):
        from generate_page import markdown_to_html

        markdown = """# Hello World

This is a **bold** statement.

> A famous quote

1. Step one
2. Step two
"""
        html = markdown_to_html(markdown)
        self.assertIn("<h1>Hello World</h1>", html)
        self.assertIn("<p>This is a <b>bold</b> statement.</p>", html)
        self.assertIn("<blockquote>A famous quote</blockquote>", html)
        self.assertIn("<ol><li>Step one</li><li>Step two</li></ol>", html)


if __name__ == "__main__":
    unittest.main()
