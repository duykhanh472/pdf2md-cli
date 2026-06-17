import re
from typing import List, Tuple, Optional
from pdf2md.models import Block

# Bullet markers patterns (including unicode characters commonly used in PDFs)
BULLET_PATTERN = re.compile(r'^([•\-*▪o\u2022\u2023\u2043·\u00b7]|\uf0b7|\uf02d)\s+(.*)$')

# Ordered list patterns (numbers, letters, roman numerals)
ORDERED_PATTERN = re.compile(r'^([0-9]+|[a-zA-Z]|[ivxlcdmIVXLCDM]+)[\.\)]\s+(.*)$')
ORDERED_PAREN_PATTERN = re.compile(r'^\(([0-9]+|[a-zA-Z]|[ivxlcdmIVXLCDM]+)\)\s+(.*)$')

# Simple Roman Numeral validator (up to 39, e.g. xxxix)
ROMAN_RE = re.compile(r'^m{0,4}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$', re.IGNORECASE)

def is_valid_marker(marker: str) -> bool:
    """
    Checks if a matched marker is valid (e.g. single character, digits, or valid roman numeral).
    """
    marker_clean = marker.strip().strip('.()')
    if not marker_clean:
        return False
    if marker_clean.isdigit():
        return True
    if len(marker_clean) == 1:
        return True
    # Check if it's a valid roman numeral
    if ROMAN_RE.match(marker_clean):
        return True
    return False

def parse_list_item(text: str) -> Optional[Tuple[bool, str, str]]:
    """
    Parses a single line of text. If it starts with a list marker,
    returns (is_ordered, marker, remaining_text), else None.
    """
    cleaned = text.strip()
    if not cleaned:
        return None
        
    # 1. Bullet list check
    bullet_match = BULLET_PATTERN.match(cleaned)
    if bullet_match:
        return False, bullet_match.group(1), bullet_match.group(2)
        
    # 2. Ordered list with parentheses check: (a) item
    paren_match = ORDERED_PAREN_PATTERN.match(cleaned)
    if paren_match:
        marker = paren_match.group(1)
        if is_valid_marker(marker):
            return True, f"({marker})", paren_match.group(2)
            
    # 3. Ordered list with dots/parentheses: 1. item or a) item
    ordered_match = ORDERED_PATTERN.match(cleaned)
    if ordered_match:
        marker = ordered_match.group(1)
        if is_valid_marker(marker):
            # Extract full marker with its suffix (. or ))
            full_marker = cleaned.split()[0]
            return True, full_marker, ordered_match.group(2)
            
    return None

class IndentTracker:
    """
    Tracks list indentation levels dynamically to determine nesting depth.
    """
    def __init__(self, tolerance: float = 8.0):
        self.levels: List[float] = []
        self.tolerance = tolerance

    def get_depth(self, indent: float) -> int:
        if not self.levels:
            self.levels.append(indent)
            return 0
            
        # Check if indent matches any existing level
        for i, val in enumerate(self.levels):
            if abs(val - indent) <= self.tolerance:
                # Truncate any levels deeper than this (we went back up the tree)
                self.levels = self.levels[:i+1]
                return i
                
        # If it is deeper than the deepest level, append it
        if indent > self.levels[-1] + self.tolerance:
            self.levels.append(indent)
            return len(self.levels) - 1
            
        # If it is shallower than the first level, reset
        if indent < self.levels[0] - self.tolerance:
            self.levels = [indent]
            return 0
            
        # Fallback
        return 0

def split_block_into_list_items(block: Block) -> List[Tuple[bool, str, str, float]]:
    """
    Splits a PyMuPDF text block into separate list items if it contains multiple list entries.
    Returns a list of (ordered, marker, text, indent) tuples.
    """
    items = []
    current_item = None
    
    # First line must start with a list marker to classify the block as a list
    first_line_parsed = parse_list_item(block.lines[0].text)
    if not first_line_parsed:
        return []
        
    for line in block.lines:
        line_text = line.text
        parsed = parse_list_item(line_text)
        
        if parsed:
            # Save previous item
            if current_item:
                items.append(current_item)
            ordered, marker, content = parsed
            # Indent is the X-coordinate of the line's bounding box
            indent = line.bbox[0]
            current_item = (ordered, marker, content, indent)
        else:
            if current_item:
                # Append line to active list item
                ordered, marker, content, indent = current_item
                current_item = (ordered, marker, content + " " + line_text, indent)
            else:
                # If first line was parsed but somehow we hit an empty case
                pass
                
    if current_item:
        items.append(current_item)
        
    return items
