import logging
from typing import List, Dict, Any, Tuple
from pdf2md.models import (
    Document,
    DocumentProfile,
    HeadingNode,
    ParagraphNode,
    ListItemNode,
    TableNode,
    Block,
    IRNode
)
from pdf2md.extract.pymupdf_extractor import extract_pdf_layout
from pdf2md.profiling.document_profile import build_document_profile
from pdf2md.classify.boilerplate import identify_boilerplate
from pdf2md.classify.table import extract_tables_from_pdf, block_overlaps_table
from pdf2md.classify.heading import score_block_as_heading, infer_heading_level
from pdf2md.classify.list import split_block_into_list_items, IndentTracker
from pdf2md.classify.paragraph import reconstruct_paragraph

logger = logging.getLogger(__name__)

def run_pipeline(pdf_path: str) -> Tuple[Document, DocumentProfile, List[Dict[str, Any]]]:
    """
    Runs the 2-pass PDF-to-Markdown processing pipeline.
    Returns:
      - Document: The AST-like IR Document.
      - DocumentProfile: The profiled layout statistics of the document.
      - List[Dict]: Debug block metadata for classification inspection.
    """
    # 1. Pass 1: Layout Extraction
    logger.info("Pass 1: Extracting layout from PDF...")
    blocks, page_dims = extract_pdf_layout(pdf_path)
    
    # 2. Pass 1: Document Profiling
    logger.info("Pass 1: Profiling document styling...")
    profile = build_document_profile(blocks)
    
    # 3. Pass 2: Boilerplate Detection
    logger.info("Pass 2: Identifying boilerplate headers/footers/page numbers...")
    boilerplate_ids = identify_boilerplate(blocks, page_dims)
    
    # 4. Pass 2: Table Detection
    logger.info("Pass 2: Extracting tables via pdfplumber...")
    tables_by_page = extract_tables_from_pdf(pdf_path)
    
    # Keep track of debug block metadata
    debug_blocks = []
    
    # Identify which blocks are associated with tables
    table_block_ids = set()
    for page_num, tables in tables_by_page.items():
        for table in tables:
            t_bbox = table["bbox"]
            for block in blocks:
                if block.page == page_num and block.block_id not in boilerplate_ids:
                    if block_overlaps_table(block.bbox, t_bbox):
                        table_block_ids.add(block.block_id)

    # Document AST
    doc_ast = Document()
    indent_tracker = IndentTracker()
    
    # Get all pages in the PDF
    total_pages = max(page_dims.keys()) if page_dims else 0
    
    for page_num in range(1, total_pages + 1):
        if page_num not in page_dims:
            continue
            
        # Get blocks on this page
        page_blocks = [b for b in blocks if b.page == page_num]
        
        # Identify boilerplate blocks for debug logging
        for b in page_blocks:
            if b.block_id in boilerplate_ids:
                debug_blocks.append({
                    "block_id": b.block_id,
                    "page": b.page,
                    "bbox": b.bbox,
                    "text": b.text,
                    "classification": "boilerplate",
                    "font_size": b.lines[0].spans[0].font_size if b.lines else None,
                    "font_name": b.lines[0].spans[0].font_name if b.lines else None,
                    "heading_score": None
                })
                
        # Non-boilerplate blocks
        active_blocks = [b for b in page_blocks if b.block_id not in boilerplate_ids]
        
        # Intersecting table blocks for debug logging
        for b in active_blocks:
            if b.block_id in table_block_ids:
                debug_blocks.append({
                    "block_id": b.block_id,
                    "page": b.page,
                    "bbox": b.bbox,
                    "text": b.text,
                    "classification": "table",
                    "font_size": b.lines[0].spans[0].font_size if b.lines else None,
                    "font_name": b.lines[0].spans[0].font_name if b.lines else None,
                    "heading_score": None
                })
                
        # Blocks that will be processed as text elements (non-boilerplate, non-table)
        text_blocks = [b for b in active_blocks if b.block_id not in table_block_ids]
        
        # Get pdfplumber tables on this page
        page_tables = tables_by_page.get(page_num, [])
        
        # Assemble Page Elements (blocks and tables)
        page_elements: List[Tuple[str, Any]] = []
        for b in text_blocks:
            page_elements.append(("block", b))
        for t in page_tables:
            page_elements.append(("table", t))
            
        # Sort page elements vertically by their top coordinate (bbox[1]) to preserve reading order
        page_elements.sort(key=lambda item: item[1].bbox[1] if item[0] == "block" else item[1]["bbox"][1])
        
        # Process elements sequentially
        for el_type, el_val in page_elements:
            if el_type == "table":
                # Reset list tracker when encountering non-list element
                indent_tracker = IndentTracker()
                
                table_data = el_val["data"]
                failed = el_val["extraction_failed"]
                
                if failed or not table_data:
                    doc_ast.nodes.append(TableNode(headers=[], rows=[], extraction_failed=True))
                else:
                    # Clean cell values
                    cleaned_rows = []
                    for r in table_data:
                        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in r]
                        cleaned_rows.append(cleaned_row)
                        
                    headers = cleaned_rows[0]
                    rows = cleaned_rows[1:]
                    doc_ast.nodes.append(TableNode(headers=headers, rows=rows))
                    
            elif el_type == "block":
                block: Block = el_val
                
                # Check for heading
                # Find neighboring blocks (in page blocks sorted list) for spacing scores
                # We can just look up standard neighbors in the text_blocks sorted vertically
                # Sorting text blocks vertically for contextual neighbors
                sorted_text_blocks = sorted(text_blocks, key=lambda b: b.bbox[1])
                b_idx = sorted_text_blocks.index(block)
                prev_b = sorted_text_blocks[b_idx - 1] if b_idx > 0 else None
                next_b = sorted_text_blocks[b_idx + 1] if b_idx < len(sorted_text_blocks) - 1 else None
                
                heading_score = score_block_as_heading(block, profile, prev_b, next_b)
                
                if heading_score >= 5.0:
                    # Reset list tracker
                    indent_tracker = IndentTracker()
                    
                    font_size = block.lines[0].spans[0].font_size if block.lines else profile.body_font_size
                    level = infer_heading_level(font_size, profile)
                    
                    doc_ast.nodes.append(HeadingNode(text=block.text.strip(), level=level))
                    
                    debug_blocks.append({
                        "block_id": block.block_id,
                        "page": block.page,
                        "bbox": block.bbox,
                        "text": block.text,
                        "classification": "heading",
                        "font_size": font_size,
                        "font_name": block.lines[0].spans[0].font_name if block.lines else None,
                        "heading_score": heading_score
                    })
                    continue
                    
                # Check for list items
                list_items = split_block_into_list_items(block)
                if list_items:
                    # Do not reset list tracker here as we are parsing list items
                    for ordered, marker, content, indent in list_items:
                        depth = indent_tracker.get_depth(indent)
                        doc_ast.nodes.append(
                            ListItemNode(text=content.strip(), level=depth, ordered=ordered, marker=marker)
                        )
                        
                    debug_blocks.append({
                        "block_id": block.block_id,
                        "page": block.page,
                        "bbox": block.bbox,
                        "text": block.text,
                        "classification": "list",
                        "font_size": block.lines[0].spans[0].font_size if block.lines else None,
                        "font_name": block.lines[0].spans[0].font_name if block.lines else None,
                        "heading_score": heading_score
                    })
                    continue
                    
                # Fallback: Paragraph
                # Reset list tracker
                indent_tracker = IndentTracker()
                
                para_text = reconstruct_paragraph(block)
                # Split if internal breaks exist
                for paragraph_chunk in para_text.split("\n\n"):
                    if paragraph_chunk.strip():
                        doc_ast.nodes.append(ParagraphNode(text=paragraph_chunk.strip()))
                        
                debug_blocks.append({
                    "block_id": block.block_id,
                    "page": block.page,
                    "bbox": block.bbox,
                    "text": block.text,
                    "classification": "paragraph",
                    "font_size": block.lines[0].spans[0].font_size if block.lines else None,
                    "font_name": block.lines[0].spans[0].font_name if block.lines else None,
                    "heading_score": heading_score
                })
                
    # Sort debug blocks by block_id to ensure consistent reporting order
    debug_blocks.sort(key=lambda db: db["block_id"])
    
    return doc_ast, profile, debug_blocks
