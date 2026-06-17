import typer
import json
import os
from typing import Optional
from pdf2md.pipeline import run_pipeline
from pdf2md.render.markdown_renderer import render_markdown
from pdf2md.cleanup.markdown_cleanup import cleanup_markdown

app = typer.Typer(add_completion=False)

@app.command()
def main(
    input_pdf: str = typer.Argument(..., help="Path to the digital PDF file to convert."),
    output_md: Optional[str] = typer.Argument(None, help="Path to save the generated markdown file. If omitted, input name will be used with .md extension."),
    dump_profile: bool = typer.Option(False, "--dump-profile", help="Dump the computed DocumentProfile JSON to stdout and exit."),
    dump_headings: bool = typer.Option(False, "--dump-headings", help="Dump all detected headings and exit."),
    dump_blocks: bool = typer.Option(False, "--dump-blocks", help="Dump all classified blocks as JSON and exit."),
):
    """
    Convert a digital PDF with text layer to a structured Markdown document.
    """
    if not os.path.exists(input_pdf):
        typer.echo(f"Error: Input file '{input_pdf}' does not exist.", err=True)
        raise typer.Exit(code=1)
        
    try:
        # Run pipeline
        doc_ast, profile, debug_blocks = run_pipeline(input_pdf)
        
        # 1. Dump Profile
        if dump_profile:
            output_profile = {
                "body_font": profile.body_font_size,
                "heading_fonts": profile.heading_sizes
            }
            typer.echo(json.dumps(output_profile, indent=2))
            raise typer.Exit()
            
        # 2. Dump Headings
        if dump_headings:
            from pdf2md.models import HeadingNode
            for node in doc_ast.nodes:
                if isinstance(node, HeadingNode):
                    typer.echo(f"H{node.level} {node.text}")
            raise typer.Exit()
            
        # 3. Dump Blocks
        if dump_blocks:
            serialized_blocks = []
            for db in debug_blocks:
                block_copy = dict(db)
                block_copy["bbox"] = list(db["bbox"])
                serialized_blocks.append(block_copy)
            typer.echo(json.dumps(serialized_blocks, indent=2, ensure_ascii=False))
            raise typer.Exit()
            
        # 4. Standard Conversion Flow
        rendered = render_markdown(doc_ast)
        cleaned = cleanup_markdown(rendered)
        
        if not output_md:
            base, _ = os.path.splitext(input_pdf)
            output_md = base + ".md"
            
        with open(output_md, "w", encoding="utf-8") as f:
            f.write(cleaned)
            
        typer.echo(f"Successfully converted '{input_pdf}' to '{output_md}'.")
        
    except typer.Exit:
        pass
    except Exception as e:
        typer.echo(f"An error occurred: {e}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
