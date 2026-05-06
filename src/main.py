from textnode import TextNode, TextType


def main():
    node = TextNode("This is some anchor text", TextType.BOLD, "https://www.boot.dev")
    print(node)


main()
