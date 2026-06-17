import logging
from typing import List, Dict, Any, Tuple
import pdfplumber
from pdf2md.models import Block

logger = logging.getLogger(__name__)

def extract_tables_from_pdf(pdf_path: str) -> Dict[int, List[Dict[str, Any]]]:
    """
    Uses pdfplumber to locate and extract tables from all pages of the PDF.
    Returns a dictionary mapping page number (1-indexed) to a list of tables.
    Each table is represented as:
      {
          "bbox": (x0, top, x1, bottom),
          "data": List[List[str]]
      }
    """
    tables_by_page = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                tables_in_page = []
                try:
                    tables = page.find_tables()
                    for t in tables:
                        try:
                            data = t.extract()
                            if data:
                                tables_in_page.append({
                                    "bbox": t.bbox,
                                    "data": data,
                                    "extraction_failed": False
                                })
                        except Exception as e:
                            logger.error(f"Failed to extract table cells on page {page_num}: {e}")
                            tables_in_page.append({
                                "bbox": t.bbox,
                                "data": [],
                                "extraction_failed": True
                            })
                except Exception as e:
                    logger.error(f"Failed to find tables on page {page_num}: {e}")
                tables_by_page[page_num] = tables_in_page
    except Exception as e:
        logger.error(f"Failed to open PDF with pdfplumber: {e}")
        
    return tables_by_page

def block_overlaps_table(
    block_bbox: Tuple[float, float, float, float],
    table_bbox: Tuple[float, float, float, float],
    overlap_threshold: float = 0.5
) -> bool:
    """
    Checks if a block's bounding box overlaps significantly with a table's bounding box.
    """
    bx0, by0, bx1, by1 = block_bbox
    tx0, ty0, tx1, ty1 = table_bbox
    
    # Calculate intersection coordinates
    ix0 = max(bx0, tx0)
    iy0 = max(by0, ty0)
    ix1 = min(bx1, tx1)
    iy1 = min(by1, ty1)
    
    if ix1 > ix0 and iy1 > iy0:
        intersection_area = (ix1 - ix0) * (iy1 - iy0)
        block_area = (bx1 - bx0) * (by1 - by0)
        if block_area > 0:
            return (intersection_area / block_area) > overlap_threshold
            
    return False
