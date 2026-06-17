from dataclasses import dataclass
from typing import Tuple

@dataclass
class Span:
    text: str
    page: int
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font_size: float
    font_name: str
    bold: bool
    italic: bool
    flags: int
