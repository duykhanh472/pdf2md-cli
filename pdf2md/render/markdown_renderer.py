from pdf2md.models import Document, HeadingNode, ParagraphNode, ListItemNode, TableNode

def render_markdown(doc: Document) -> str:
    """
    Renders the AST-like IR Document into a markdown string.
    """
    chunks = []
    in_list = False
    
    for node in doc.nodes:
        if isinstance(node, HeadingNode):
            in_list = False
            # Standardize headings with blank lines
            chunks.append(f"\n\n{'#' * node.level} {node.text}\n\n")
            
        elif isinstance(node, ParagraphNode):
            in_list = False
            chunks.append(f"{node.text}\n\n")
            
        elif isinstance(node, ListItemNode):
            # If transitioning into a list, add a newline before the list
            if not in_list:
                chunks.append("\n")
                in_list = True
                
            indent = "  " * node.level
            marker = "-" if not node.ordered else node.marker
            chunks.append(f"{indent}{marker} {node.text}\n")
            
        elif isinstance(node, TableNode):
            in_list = False
            if node.extraction_failed or not node.headers:
                chunks.append("\n\n[TABLE DETECTED]\n\n")
                continue
                
            table_lines = []
            
            # Helper to clean table cell content for markdown compliance (no raw newlines)
            def clean_cell(text: str) -> str:
                return text.replace("\n", " ").replace("\r", " ").replace("|", "\\|").strip()
                
            clean_headers = [clean_cell(h) for h in node.headers]
            
            # Header Row
            table_lines.append("| " + " | ".join(clean_headers) + " |")
            
            # Separator Row
            seps = ["---"] * len(clean_headers)
            table_lines.append("| " + " | ".join(seps) + " |")
            
            # Data Rows
            for row in node.rows:
                # Pad row cells to match headers length if they are shorter
                padded_row = list(row) + [""] * (len(clean_headers) - len(row))
                # Truncate if longer
                padded_row = padded_row[:len(clean_headers)]
                
                clean_row = [clean_cell(cell) for cell in padded_row]
                table_lines.append("| " + " | ".join(clean_row) + " |")
                
            chunks.append("\n\n" + "\n".join(table_lines) + "\n\n")
            
    # Join chunks
    return "".join(chunks)
