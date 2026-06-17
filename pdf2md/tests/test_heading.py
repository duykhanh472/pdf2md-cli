from pdf2md.models import Span, Line, Block, DocumentProfile
from pdf2md.classify.heading import score_block_as_heading, infer_heading_level

def test_heading_scoring_and_level():
    profile = DocumentProfile(
        body_font_size=11.0,
        body_font_family="Arial",
        heading_sizes=[24.0, 18.0, 14.0],
        avg_line_height=14.0,
        avg_block_spacing=18.0
    )
    
    # 1. H2 Heading Candidate: large font size, bold, short text, starts with heading pattern
    s_h1 = Span(
        text="1 Introduction",
        page=1,
        bbox=(50, 50, 150, 68),
        font_size=18.0,
        font_name="Arial-Bold",
        bold=True,
        italic=False,
        flags=8
    )
    line_h1 = Line(spans=[s_h1], page=1, bbox=(50, 50, 150, 68))
    block_h1 = Block(lines=[line_h1], page=1, bbox=(50, 50, 150, 68), block_id=0)
    
    score_h1 = score_block_as_heading(block_h1, profile)
    level_h1 = infer_heading_level(18.0, profile)
    
    assert score_h1 >= 5.0
    assert level_h1 == 2  # 18.0 is second in heading_sizes [24.0, 18.0, 14.0]
    
    # 2. Sub-heading Candidate: body font size, bold, short text, starts with heading pattern
    s_h2 = Span(
        text="1.1 Background Study",
        page=1,
        bbox=(50, 100, 200, 111),
        font_size=11.0,
        font_name="Arial-Bold",
        bold=True,
        italic=False,
        flags=8
    )
    line_h2 = Line(spans=[s_h2], page=1, bbox=(50, 100, 200, 111))
    block_h2 = Block(lines=[line_h2], page=1, bbox=(50, 100, 200, 111), block_id=1)
    
    score_h2 = score_block_as_heading(block_h2, profile)
    level_h2 = infer_heading_level(11.0, profile)
    
    assert score_h2 >= 5.0
    assert level_h2 == 4  # body font sized headings map to min(6, len(heading_sizes) + 1)
    
    # 3. Non-heading: normal paragraph, body font size, normal weight, ends with dot
    s_para = Span(
        text="This is a simple text sentence that is supposed to be a normal paragraph block.",
        page=1,
        bbox=(50, 150, 300, 161),
        font_size=11.0,
        font_name="Arial",
        bold=False,
        italic=False,
        flags=0
    )
    line_para = Line(spans=[s_para], page=1, bbox=(50, 150, 300, 161))
    block_para = Block(lines=[line_para], page=1, bbox=(50, 150, 300, 161), block_id=2)
    
    score_para = score_block_as_heading(block_para, profile)
    
    assert score_para < 5.0
