from pdf2md.models import Span, Line, Block
from pdf2md.classify.list import parse_list_item, split_block_into_list_items, IndentTracker

def test_list_parsing_and_tracking():
    # 1. Test bullet list items
    assert parse_list_item("• Bullet item") == (False, "•", "Bullet item")
    assert parse_list_item("- Dash item") == (False, "-", "Dash item")
    assert parse_list_item("* Asterisk item") == (False, "*", "Asterisk item")
    
    # 2. Test ordered list items
    assert parse_list_item("1. Numbered item") == (True, "1.", "Numbered item")
    assert parse_list_item("a) Alphabetic item") == (True, "a)", "Alphabetic item")
    assert parse_list_item("(i) Roman item") == (True, "(i)", "Roman item")
    
    # 3. Invalid items (should not parse as list items)
    assert parse_list_item("No. 5 is correct") is None
    assert parse_list_item("Normal sentence without list.") is None

    # 4. Test IndentTracker nesting logic
    tracker = IndentTracker(tolerance=8.0)
    assert tracker.get_depth(50.0) == 0
    assert tracker.get_depth(70.0) == 1
    assert tracker.get_depth(72.0) == 1  # within tolerance of 8.0 relative to 70.0
    assert tracker.get_depth(90.0) == 2
    assert tracker.get_depth(70.0) == 1  # climbs back up to index 1
    assert tracker.get_depth(48.0) == 0  # within tolerance of 50.0, climbs back to 0
    
    # 5. Test block containing multiple list items and multi-line continuations
    s1 = Span(
        text="1. First list entry",
        page=1,
        bbox=(50, 10, 150, 20),
        font_size=11.0,
        font_name="Arial",
        bold=False,
        italic=False,
        flags=0
    )
    s2 = Span(
        text="wrapped line for first entry",
        page=1,
        bbox=(50, 20, 150, 30),
        font_size=11.0,
        font_name="Arial",
        bold=False,
        italic=False,
        flags=0
    )
    s3 = Span(
        text="2. Second list entry",
        page=1,
        bbox=(50, 30, 150, 40),
        font_size=11.0,
        font_name="Arial",
        bold=False,
        italic=False,
        flags=0
    )
    
    block = Block(
        lines=[
            Line(spans=[s1], page=1, bbox=s1.bbox),
            Line(spans=[s2], page=1, bbox=s2.bbox),
            Line(spans=[s3], page=1, bbox=s3.bbox)
        ],
        page=1,
        bbox=(50, 10, 150, 40),
        block_id=0
    )
    
    items = split_block_into_list_items(block)
    assert len(items) == 2
    assert items[0] == (True, "1.", "First list entry wrapped line for first entry", 50.0)
    assert items[1] == (True, "2.", "Second list entry", 50.0)
