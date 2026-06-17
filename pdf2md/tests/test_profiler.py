from pdf2md.models import Span, Line, Block
from pdf2md.profiling.document_profile import build_document_profile

def test_build_document_profile():
    # Construct a set of blocks where 11.0 is the body font size (most characters)
    # and 18.0 and 14.0 are headings
    spans_body = [
        Span(
            text="This is a paragraph of body text that has a decent length to make it the dominant font.",
            page=1,
            bbox=(0, 0, 10, 10),
            font_size=11.0,
            font_name="Arial",
            bold=False,
            italic=False,
            flags=0
        )
        for _ in range(3)
    ]
    spans_heading1 = [
        Span(
            text="Main Title",
            page=1,
            bbox=(0, 0, 10, 10),
            font_size=18.0,
            font_name="Arial-Bold",
            bold=True,
            italic=False,
            flags=8
        )
    ]
    spans_heading2 = [
        Span(
            text="Subtitle",
            page=1,
            bbox=(0, 0, 10, 10),
            font_size=14.0,
            font_name="Arial-Bold",
            bold=True,
            italic=False,
            flags=8
        )
    ]
    
    block_body = Block(
        lines=[Line(spans=[s], page=1, bbox=s.bbox) for s in spans_body],
        page=1,
        bbox=(50, 100, 300, 150),
        block_id=0
    )
    block_h1 = Block(
        lines=[Line(spans=[s], page=1, bbox=s.bbox) for s in spans_heading1],
        page=1,
        bbox=(50, 20, 200, 40),
        block_id=1
    )
    block_h2 = Block(
        lines=[Line(spans=[s], page=1, bbox=s.bbox) for s in spans_heading2],
        page=1,
        bbox=(50, 50, 150, 70),
        block_id=2
    )
    
    profile = build_document_profile([block_h1, block_h2, block_body])
    
    assert profile.body_font_size == 11.0
    assert profile.body_font_family == "Arial"
    assert 18.0 in profile.heading_sizes
    assert 14.0 in profile.heading_sizes
    assert profile.heading_sizes == [18.0, 14.0]  # sorted descending
