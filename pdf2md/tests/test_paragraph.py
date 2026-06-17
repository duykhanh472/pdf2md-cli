from pdf2md.models import Span, Line, Block
from pdf2md.classify.paragraph import reconstruct_paragraph

def test_paragraph_reconstruction():
    # 1. Test basic paragraph wrapping with space insertion
    s1 = Span(
        text="This is a wrapped line inside a block",
        page=1,
        bbox=(50, 10, 200, 20),
        font_size=11.0,
        font_name="Arial",
        bold=False,
        italic=False,
        flags=0
    )
    s2 = Span(
        text="and this is the subsequent line.",
        page=1,
        bbox=(50, 20, 200, 30),
        font_size=11.0,
        font_name="Arial",
        bold=False,
        italic=False,
        flags=0
    )
    
    block1 = Block(
        lines=[
            Line(spans=[s1], page=1, bbox=s1.bbox),
            Line(spans=[s2], page=1, bbox=s2.bbox)
        ],
        page=1,
        bbox=(50, 10, 200, 30),
        block_id=0
    )
    
    assert reconstruct_paragraph(block1) == "This is a wrapped line inside a block and this is the subsequent line."

    # 2. Test soft hyphen repair (informa- + tion -> information)
    s3 = Span(
        text="This contains informa-",
        page=1,
        bbox=(50, 10, 200, 20),
        font_size=11.0,
        font_name="Arial",
        bold=False,
        italic=False,
        flags=0
    )
    s4 = Span(
        text="tion about the company.",
        page=1,
        bbox=(50, 20, 200, 30),
        font_size=11.0,
        font_name="Arial",
        bold=False,
        italic=False,
        flags=0
    )
    
    block2 = Block(
        lines=[
            Line(spans=[s3], page=1, bbox=s3.bbox),
            Line(spans=[s4], page=1, bbox=s4.bbox)
        ],
        page=1,
        bbox=(50, 10, 200, 30),
        block_id=1
    )
    
    assert reconstruct_paragraph(block2) == "This contains information about the company."

    # 3. Test paragraph breaks inside block based on indent change
    # S5 is standard indent (50pt), ends with a dot.
    # S6 is indented (70pt), which signifies a new paragraph chunk.
    s5 = Span(
        text="This is the end of paragraph one.",
        page=1,
        bbox=(50, 10, 250, 20),
        font_size=11.0,
        font_name="Arial",
        bold=False,
        italic=False,
        flags=0
    )
    s6 = Span(
        text="And this begins paragraph two.",
        page=1,
        bbox=(70, 20, 250, 30),  # x0 = 70 (indentation diff = 20)
        font_size=11.0,
        font_name="Arial",
        bold=False,
        italic=False,
        flags=0
    )
    
    block3 = Block(
        lines=[
            Line(spans=[s5], page=1, bbox=s5.bbox),
            Line(spans=[s6], page=1, bbox=s6.bbox)
        ],
        page=1,
        bbox=(50, 10, 250, 30),
        block_id=2
    )
    
    assert reconstruct_paragraph(block3) == "This is the end of paragraph one.\n\nAnd this begins paragraph two."
