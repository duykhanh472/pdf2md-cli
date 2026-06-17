import re
from typing import Tuple, List, Optional
from pdf2md.models import Block, DocumentProfile

# Regexes for heading numbering patterns
HEADING_PATTERNS = [
    re.compile(r'^\s*Chương\s+[a-zA-Z0-9IVX]+\b', re.IGNORECASE),
    re.compile(r'^\s*Chapter\s+[a-zA-Z0-9IVX]+\b', re.IGNORECASE),
    re.compile(r'^\s*Section\s+[a-zA-Z0-9IVX]+\b', re.IGNORECASE),
    re.compile(r'^\s*Appendix\s+[A-Z0-9]+\b', re.IGNORECASE),
    re.compile(r'^\s*Phần\s+[IVXLCDM0-9]+\b', re.IGNORECASE),
    re.compile(r'^\s*Mục\s+[0-9]+\b', re.IGNORECASE),
    # Numerical patterns like: 1., 1.1, 2.3.4 (must be followed by text)
    re.compile(r'^\s*(\d+(\.\d+)*)\.?\s+[A-ZÀ-Ỹa-zà-ỹ]'),
    # Roman numerals: I., II., IV.
    re.compile(r'^\s*([IVXLCDM]+)\.\s+[A-ZÀ-Ỹa-zà-ỹ]'),
    # Alphabetical patterns: A., B., a., b.
    re.compile(r'^\s*([A-Za-z])\.\s+[A-ZÀ-Ỹa-zà-ỹ]'),
]

def matches_heading_pattern(text: str) -> bool:
    """
    Checks if the text starts with a typical heading numbering or prefix pattern.
    """
    cleaned = text.strip()
    return any(pattern.match(cleaned) for pattern in HEADING_PATTERNS)

def score_block_as_heading(
    block: Block,
    profile: DocumentProfile,
    prev_block: Optional[Block] = None,
    next_block: Optional[Block] = None
) -> float:
    """
    Evaluates the block using a scoring heuristic. Returns the total score.
    """
    text = block.text.strip()
    if not text:
        return 0.0
        
    # Headings are rarely long paragraph blocks
    if len(block.lines) > 2 or len(text) > 160:
        return 0.0
        
    score = 0.0
    
    # Inspect font size and style of the first span of the first line
    first_line = block.lines[0]
    first_span = first_line.spans[0]
    
    size = first_span.font_size
    is_bold = first_span.bold
    is_italic = first_span.italic
    
    # 1. Font Size relative to body font size
    if size > profile.body_font_size + 3.5:
        score += 6.0
    elif size > profile.body_font_size + 0.5:
        score += 4.5
    elif size < profile.body_font_size - 0.5:
        score -= 4.0  # severely penalize smaller text
        
    # 2. Bold Style
    if is_bold:
        score += 3.5
        
    # 3. Italic Style
    if is_italic:
        score += 0.5
        
    # 4. Heading Prefixes / Patterns
    if matches_heading_pattern(text):
        score += 2.5
        
    # 5. Length
    if len(text) < 40:
        score += 2.0
    elif len(text) < 80:
        score += 1.0
        
    # 6. Ends with sentence-ending punctuation (usually a paragraph line, not heading)
    if text.endswith(('.', '?', '!', ':')) and not matches_heading_pattern(text):
        score -= 2.5

    # 7. Block spacing (empty lines above/below)
    # Check spacing above
    if prev_block and prev_block.page == block.page:
        spacing_above = block.bbox[1] - prev_block.bbox[3]
        if spacing_above > profile.avg_block_spacing * 1.3:
            score += 1.5
            
    # Check spacing below
    if next_block and next_block.page == block.page:
        spacing_below = next_block.bbox[1] - block.bbox[3]
        if spacing_below > profile.avg_block_spacing * 1.3:
            score += 1.0

    return score

def infer_heading_level(size: float, profile: DocumentProfile) -> int:
    """
    Infers the heading level (1 to 6) based on the font size distribution in the DocumentProfile.
    """
    if not profile.heading_sizes:
        return 1
        
    # If the font size is close to the body font size (or smaller), it's a low-level header
    if size <= profile.body_font_size + 0.5:
        return min(6, len(profile.heading_sizes) + 1)
        
    # Find closest heading size in profile.heading_sizes
    closest_idx = 0
    min_diff = float('inf')
    
    for idx, h_size in enumerate(profile.heading_sizes):
        diff = abs(h_size - size)
        if diff < min_diff:
            min_diff = diff
            closest_idx = idx
            
    return min(6, closest_idx + 1)
