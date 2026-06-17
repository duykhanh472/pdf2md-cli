import re
from typing import List, Set, Dict, Tuple
from pdf2md.models import Block

# Regex for common page number patterns
PAGE_NUMBER_PATTERNS = [
    re.compile(r'^\s*\d+\s*$', re.IGNORECASE),
    re.compile(r'^\s*page\s+\d+\s*$', re.IGNORECASE),
    re.compile(r'^\s*page\s+\d+\s+of\s+\d+\s*$', re.IGNORECASE),
    re.compile(r'^\s*-\s*\d+\s*-\s*$', re.IGNORECASE),
    re.compile(r'^\s*\d+\s*/\s*\d+\s*$', re.IGNORECASE),
]

def is_page_number_text(text: str) -> bool:
    """
    Checks if the given text matches common page number patterns.
    """
    cleaned = text.strip()
    return any(pattern.match(cleaned) for pattern in PAGE_NUMBER_PATTERNS)

def get_text_signature(text: str) -> str:
    """
    Creates a signature of the text by lowercasing, stripping,
    and removing digits/punctuation to identify running headers with variable page numbers.
    """
    cleaned = text.strip().lower()
    # Remove digits
    cleaned = re.sub(r'\d+', '', cleaned)
    # Remove extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def identify_boilerplate(
    blocks: List[Block],
    page_dims: Dict[int, Tuple[float, float]],
    margin_ratio: float = 0.12
) -> Set[int]:
    """
    Identifies block IDs that represent page numbers or running headers/footers.
    Returns a set of block IDs to be filtered out.
    """
    boilerplate_ids = set()
    
    # Track marginal blocks to find repeating running headers/footers
    # Key: signature, Value: set of page numbers where it appeared
    marginal_signatures: Dict[str, Set[int]] = {}
    
    # Store block details for a second pass
    marginal_blocks_info: List[Tuple[int, str, int, float]] = [] # (block_id, signature, page, center_y)

    for block in blocks:
        page = block.page
        if page not in page_dims:
            continue
        
        width, height = page_dims[page]
        y0, y1 = block.bbox[1], block.bbox[3]
        center_y = (y0 + y1) / 2.0
        
        # Check if block is inside top or bottom margin
        is_in_margin = (center_y < margin_ratio * height) or (center_y > (1.0 - margin_ratio) * height)
        
        if is_in_margin:
            text = block.text.strip()
            if not text:
                continue
                
            # First, check if it's a simple page number
            if is_page_number_text(text):
                boilerplate_ids.add(block.block_id)
                continue
                
            # Otherwise, analyze it as a potential running header/footer
            sig = get_text_signature(text)
            if sig:  # ignore empty signatures
                if sig not in marginal_signatures:
                    marginal_signatures[sig] = set()
                marginal_signatures[sig].add(page)
                marginal_blocks_info.append((block.block_id, sig, page, center_y))

    # Identify signatures that appear on more than one page
    running_boilerplate_signatures = {
        sig for sig, pages in marginal_signatures.items() if len(pages) >= 2
    }

    # Add block IDs of the running headers/footers to boilerplate set
    for block_id, sig, page, center_y in marginal_blocks_info:
        if sig in running_boilerplate_signatures:
            boilerplate_ids.add(block_id)

    return boilerplate_ids
