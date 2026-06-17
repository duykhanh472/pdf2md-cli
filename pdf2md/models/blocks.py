from dataclasses import dataclass
from typing import List, Tuple
from pdf2md.models.spans import Span

@dataclass
class Line:
    spans: List[Span]
    page: int
    bbox: Tuple[float, float, float, float]
    
    @property
    def text(self) -> str:
        return "".join(span.text for span in self.spans)

@dataclass
class Block:
    lines: List[Line]
    page: int
    bbox: Tuple[float, float, float, float]
    block_id: int
    
    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)
