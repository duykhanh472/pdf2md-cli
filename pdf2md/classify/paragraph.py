import re
from pdf2md.models import Block

def reconstruct_paragraph(block: Block) -> str:
    """
    Reconstructs paragraphs from block lines by merging wrapped lines.
    Applies hyphen repair (e.g., 'informa-' + 'tion' -> 'information')
    and preserves internal paragraph boundaries if significant indentation changes occur.
    """
    merged_text = ""
    
    for i, line in enumerate(block.lines):
        line_text = line.text.strip()
        if not line_text:
            continue
            
        if not merged_text:
            merged_text = line_text
            continue
            
        # 1. Hyphen Repair
        # Check if previous text ends with a letter and a hyphen, and current line starts with a letter
        if (len(merged_text) >= 2 and 
            merged_text[-1] == '-' and 
            merged_text[-2].isalpha() and 
            line_text[0].isalpha()):
            # Strip the hyphen and merge directly
            merged_text = merged_text[:-1] + line_text
        else:
            # 2. Check for sub-paragraph break within the same block
            # If the previous line ended with sentence-ending punctuation
            # and the current line is significantly indented relative to the previous line (e.g., > 15 points)
            prev_line = block.lines[i - 1]
            indent_diff = line.bbox[0] - prev_line.bbox[0]
            
            # Ends with sentence punctuation
            ends_with_sentence_punct = merged_text[-1] in ['.', '!', '?']
            
            if ends_with_sentence_punct and indent_diff > 15.0:
                # Insert paragraph break
                merged_text += "\n\n" + line_text
            else:
                # Regular word wrapping: merge with a space
                # Check to avoid adding double space if merged_text ends with space or line_text starts with space
                if merged_text.endswith(" ") or line_text.startswith(" "):
                    merged_text += line_text
                else:
                    merged_text += " " + line_text
                    
    return merged_text
