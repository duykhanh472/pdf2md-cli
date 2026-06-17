from collections import Counter, defaultdict
from typing import List
from pdf2md.models import Block, DocumentProfile

def build_document_profile(blocks: List[Block]) -> DocumentProfile:
    """
    Analyzes the extracted layout blocks to determine the document profile:
    - Most common font size and family (body font).
    - Potential heading font sizes (larger than body font, grouped by similarity).
    - Average line height and block spacing.
    """
    font_size_chars = Counter()
    font_family_chars = Counter()
    
    # Track character count per font size and family to find the body font
    for block in blocks:
        for line in block.lines:
            for span in line.spans:
                char_count = len(span.text)
                if char_count == 0:
                    continue
                # Round font size to 1 decimal place to group minor variations
                size_rounded = round(span.font_size, 1)
                font_size_chars[size_rounded] += char_count
                font_family_chars[span.font_name] += char_count

    # Determine body font size and family
    body_font_size = 11.0  # default fallback
    if font_size_chars:
        body_font_size = font_size_chars.most_common(1)[0][0]
        
    body_font_family = "sans-serif"  # default fallback
    if font_family_chars:
        body_font_family = font_family_chars.most_common(1)[0][0]

    # Find heading candidate sizes: sizes larger than body font size with a gap
    candidate_sizes = [
        size for size in font_size_chars.keys()
        if size > body_font_size + 0.5 and font_size_chars[size] >= 3
    ]
    
    # Group heading sizes that are very close (tolerance = 0.8 points)
    candidate_sizes.sort(reverse=True)
    grouped_heading_sizes = []
    
    for size in candidate_sizes:
        # Check if it fits in an existing group
        placed = False
        for i, group in enumerate(grouped_heading_sizes):
            # If size is close to any representative size in the group
            if abs(group[0] - size) <= 0.8:
                # Add to group, recompute average weighted by character count
                grouped_heading_sizes[i].append(size)
                placed = True
                break
        if not placed:
            grouped_heading_sizes.append([size])
            
    # Compute representative size for each group (weighted by character count)
    heading_sizes = []
    for group in grouped_heading_sizes:
        total_chars = sum(font_size_chars[size] for size in group)
        if total_chars > 0:
            weighted_size = sum(size * font_size_chars[size] for size in group) / total_chars
            heading_sizes.append(round(weighted_size, 1))
        else:
            heading_sizes.append(round(sum(group) / len(group), 1))
            
    # Sort heading sizes descending
    heading_sizes.sort(reverse=True)

    # Compute average line height (distance between baseline or Y-centers of consecutive lines in a block)
    line_spacings = []
    for block in blocks:
        if len(block.lines) > 1:
            for i in range(len(block.lines) - 1):
                l1 = block.lines[i]
                l2 = block.lines[i + 1]
                # Spacing based on top coordinates
                spacing = l2.bbox[1] - l1.bbox[1]
                if 0 < spacing < 100:  # ignore weird anomalies
                    line_spacings.append(spacing)
                    
    avg_line_height = sum(line_spacings) / len(line_spacings) if line_spacings else 14.0

    # Compute average block spacing (distance between blocks on the same page)
    # Group blocks by page
    page_blocks = defaultdict(list)
    for block in blocks:
        page_blocks[block.page].append(block)
        
    block_spacings = []
    for page, p_blocks in page_blocks.items():
        # Sort blocks by top Y coordinate
        sorted_p_blocks = sorted(p_blocks, key=lambda b: b.bbox[1])
        for i in range(len(sorted_p_blocks) - 1):
            b1 = sorted_p_blocks[i]
            b2 = sorted_p_blocks[i + 1]
            spacing = b2.bbox[1] - b1.bbox[3]  # top of second minus bottom of first
            if 0 < spacing < 200:  # ignore large gaps / page breaks
                block_spacings.append(spacing)
                
    avg_block_spacing = sum(block_spacings) / len(block_spacings) if block_spacings else 18.0

    return DocumentProfile(
        body_font_size=body_font_size,
        body_font_family=body_font_family,
        heading_sizes=heading_sizes,
        avg_line_height=avg_line_height,
        avg_block_spacing=avg_block_spacing
    )
