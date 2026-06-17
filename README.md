# PDF → Formatted Markdown CLI (pdf2md)

Heuristic-based Python CLI for converting digital PDFs (with text layer and font metadata) into clean, structured Markdown.

## Description

This project provides a robust, two-pass conversion pipeline designed to convert digital PDF documents (such as Ebooks, reports, and exported Word documents) into human-readable Markdown. It relies entirely on coordinates-based layout analysis and text statistics. By avoiding heavy OCR engines and LLMs, it remains lightweight, fast, and secure.

Key features include:

* **Style Profiling**: Statistical detection of the document's body font and vertical layout metrics to globally infer heading hierarchy levels (H1–H6).
* **Heuristic Layout Reconstruction**: Re-joins paragraph lines wrapped by PDF page boundaries, detects paragraph separation within blocks, and performs soft-hyphen repairs.
* **Boilerplate Removal**: Detects page numbers, running headers, and running footers located in top and bottom margins.
* **Lists Detection**: Identifies nested bullet and ordered lists (numbers, letters, roman numerals) using indentation tracker levels.
* **Table Extraction**: Uses `pdfplumber` to extract tables and converts them to Markdown grid tables while keeping correct vertical reading order.

## Getting Started

### Dependencies

* Python 3.8 or higher.
* Python packages: `pymupdf` (fitz), `pdfplumber`, and `typer`.

### Installing

1. Download or clone this project into your workspace:
   ```bash
   git clone <repository_url> pdf2md-cli
   cd pdf2md-cli
   ```
2. Set up a virtual environment and install the dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   pip install --upgrade pip
   pip install pymupdf pdfplumber typer pytest
   ```

### Executing program

* **Convert PDF to Markdown** (runs standard conversion flow, automatically outputting to `<input_name>.md` if the output path is omitted):
  ```bash
  python3 -m pdf2md input.pdf
  ```
* **Convert PDF to custom Markdown output path**:
  ```bash
  python3 -m pdf2md input.pdf output.md
  ```
* **Dump Document Profile** (prints the body font size and candidate heading sizes as JSON):
  ```bash
  python3 -m pdf2md input.pdf --dump-profile
  ```
* **Dump Detected Headings** (lists headings and their global level mapping, e.g., H1, H2, H3):
  ```bash
  python3 -m pdf2md input.pdf --dump-headings
  ```
* **Dump Block Classifications** (prints a JSON list of all extracted text blocks and their classification details for debugging):
  ```bash
  python3 -m pdf2md input.pdf --dump-blocks
  ```
* **Running Tests**:
  ```bash
  PYTHONPATH=. pytest pdf2md/tests
  ```

## Help

Common issues and advice:

* **Scanned PDFs / OCR**: If the input PDF is scanned (does not contain a text layer or font metadata), the converter will output an empty document or boilerplate elements. Ensure the PDF is a digital-born document with selectable text.
* **Table Extraction Failures**: If pdfplumber is unable to parse grid tables (e.g. because they lack border lines or have highly complex cells), they will fall back to `[TABLE DETECTED]` in the output markdown.

Run the helper command to see all available CLI options:
```bash
python3 -m pdf2md --help
```

## License

This project is licensed under the Unlicense License - see the LICENSE file for details.
