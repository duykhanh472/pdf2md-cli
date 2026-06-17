from pdf2md.models import Document, HeadingNode, ParagraphNode, ListItemNode, TableNode
from pdf2md.render.markdown_renderer import render_markdown
from pdf2md.cleanup.markdown_cleanup import cleanup_markdown

def test_renderer_and_cleanup():
    # 1. Test AST rendering
    doc = Document()
    doc.nodes.extend([
        HeadingNode(text="Heading 1", level=1),
        ParagraphNode(text="This is a simple paragraph."),
        ListItemNode(text="Item 1", level=0, ordered=False, marker="-"),
        ListItemNode(text="Item 1.1", level=1, ordered=False, marker="-"),
        TableNode(
            headers=["Name", "Age"],
            rows=[["Alice", "30"], ["Bob\nJ.", "25"]]  # newline in cell should be escaped
        )
    ])
    
    rendered = render_markdown(doc)
    
    assert "# Heading 1" in rendered
    assert "This is a simple paragraph." in rendered
    assert "- Item 1" in rendered
    assert "  - Item 1.1" in rendered
    assert "| Name | Age |" in rendered
    assert "| --- | --- |" in rendered
    assert "| Alice | 30 |" in rendered
    assert "| Bob J. | 25 |" in rendered  # newline replaced with space

    # 2. Test Cleanup Pass normalization
    dirty_md = """
#Heading 1


This is a paragraph with too many blank lines.



- Item 1
    """
    
    cleaned = cleanup_markdown(dirty_md)
    
    # Enforces space after heading hash
    assert cleaned.startswith("# Heading 1")
    # Collapses 3+ newlines to exactly 2 newlines (one empty line)
    assert "\n\nThis is a paragraph" in cleaned
    assert "blank lines.\n\n- Item 1" in cleaned
    # Single trailing newline
    assert cleaned.endswith("\n")
    assert not cleaned.endswith("\n\n")
