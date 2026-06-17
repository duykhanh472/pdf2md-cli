from dataclasses import dataclass, field
from typing import List

@dataclass
class IRNode:
    pass

@dataclass
class HeadingNode(IRNode):
    text: str
    level: int

@dataclass
class ParagraphNode(IRNode):
    text: str

@dataclass
class ListItemNode(IRNode):
    text: str
    level: int  # Nesting depth: 0, 1, 2...
    ordered: bool
    marker: str  # e.g., "•", "1.", "a."

@dataclass
class TableNode(IRNode):
    headers: List[str]
    rows: List[List[str]]
    extraction_failed: bool = False

@dataclass
class Document:
    nodes: List[IRNode] = field(default_factory=list)
