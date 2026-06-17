import fitz
from typing import List
from pdf2md.models import Span, Line, Block

def extract_pdf_layout(pdf_path: str) -> tuple[List[Block], dict[int, tuple[float, float]]]:
    """
    Opens the PDF file and extracts text layout blocks, lines, spans, and page dimensions using PyMuPDF.
    """
    doc = fitz.open(pdf_path)
    all_blocks = []
    block_id_counter = 0
    page_dims = {}
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_dims[page_num + 1] = (page.rect.width, page.rect.height)
        text_page = page.get_text("dict")
        
        for b in text_page.get("blocks", []):
            if b.get("type") != 0:  # Only process text blocks (ignore image blocks)
                continue
                
            lines_in_block = []
            for l in b.get("lines", []):
                spans_in_line = []
                for s in l.get("spans", []):
                    text = s.get("text", "")
                    if not text:
                        continue
                    
                    font_name = s.get("font", "")
                    font_size = s.get("size", 0.0)
                    flags = s.get("flags", 0)
                    bbox = s.get("bbox", (0.0, 0.0, 0.0, 0.0))
                    
                    # Parse bold and italic flags from PyMuPDF flags & font name heuristics
                    # Bit 2 (italic) = 4, Bit 3 (bold) = 8
                    bold = bool(flags & 8) or any(
                        kwd in font_name.lower() for kwd in ["bold", "black", "heavy", "semibold", "medium"]
                    )
                    italic = bool(flags & 4) or any(
                        kwd in font_name.lower() for kwd in ["italic", "oblique"]
                    )
                    
                    span_obj = Span(
                        text=text,
                        page=page_num + 1,
                        bbox=bbox,
                        font_size=font_size,
                        font_name=font_name,
                        bold=bold,
                        italic=italic,
                        flags=flags
                    )
                    spans_in_line.append(span_obj)
                
                if spans_in_line:
                    line_obj = Line(
                        spans=spans_in_line,
                        page=page_num + 1,
                        bbox=l.get("bbox", (0.0, 0.0, 0.0, 0.0))
                    )
                    lines_in_block.append(line_obj)
            
            if lines_in_block:
                block_obj = Block(
                    lines=lines_in_block,
                    page=page_num + 1,
                    bbox=b.get("bbox", (0.0, 0.0, 0.0, 0.0)),
                    block_id=block_id_counter
                )
                all_blocks.append(block_obj)
                block_id_counter += 1
                
    doc.close()
    return all_blocks, page_dims
