from dataclasses import dataclass
from typing import List

@dataclass
class DocumentProfile:
    body_font_size: float
    body_font_family: str
    heading_sizes: List[float]  # Sorted descending
    avg_line_height: float
    avg_block_spacing: float
