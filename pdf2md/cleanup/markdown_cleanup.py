import re

def cleanup_markdown(md_text: str) -> str:
    """
    Cleans up and normalizes the rendered markdown content:
    - Standardizes line endings and removes trailing spaces from lines.
    - Collapses consecutive empty lines (no more than one blank line between blocks).
    - Enforces a space between heading markers (#) and heading text.
    - Strips leading and trailing blank lines from the document, adding a single trailing newline.
    """
    # 1. Trim trailing spaces on each line
    lines = [line.rstrip() for line in md_text.splitlines()]
    content = "\n".join(lines)
    
    # 2. Ensure heading formatting is clean (e.g., #Title -> # Title)
    # Match lines starting with hashes followed by letters/digits without space
    content = re.sub(r'^(#+)([a-zA-Z0-9À-Ỹà-ỹ])', r'\1 \2', content, flags=re.MULTILINE)
    
    # 3. Collapse multiple consecutive empty lines (3 or more newlines -> 2 newlines)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 4. Strip leading/trailing whitespaces from the whole document
    content = content.strip()
    
    # Return with a single trailing newline
    return content + "\n"
