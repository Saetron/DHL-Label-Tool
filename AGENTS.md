# AGENTS.md

Instructions and context for AI agents working on the DHL Label Tool codebase.

---

## 1. Project Overview

**DHL Label Tool** is a desktop utility (Python / PyQt6 / PyMuPDF) designed to prepare DHL shipping labels (Paketmarken & Retouren) for direct printing on 4x6" thermal label printers.

### Core Problems Solved:
1. **Discarding unnecessary pages / sections**: DHL provides labels on A4 pages containing both the shipping label and sender instructions ("Sendungsinformation für Ihre Unterlagen"). The tool detects and isolates only the printable shipping label portion.
2. **Upright (Portrait / Hochkant) Orientation**: Original label contents run horizontally across the A4 sheet. The tool rotates the label by 90° (270° counter-clockwise) to render it upright.
3. **Bounding Box & Margin**: Detects vector drawings and text items to tightly crop the label while applying a configurable margin (default: 12 pt ≈ 4.2 mm) around all 4 edges so thermal printer edge tolerances do not cut off barcodes or borders.
4. **Batch & Merge**: Supports processing multiple PDFs at once, either into individual cropped PDFs or merged into a single multi-page PDF.

---

## 2. Repository Layout

```
.
├── dhl_label_splitter.py    # Main application logic (PDF engine + PyQt6 GUI + CLI)
├── Start-Label-Tool.bat     # Windows launcher (supports double-click GUI & drag-and-drop batch)
├── requirements.txt         # Python dependencies (PyQt6, pymupdf)
├── README.md                # User-facing documentation
├── CHANGELOG.md             # Version history
└── AGENTS.md                # Agent reference and engineering guidelines
```

---

## 3. Architecture & Key Functions

All application logic resides in [`dhl_label_splitter.py`](dhl_label_splitter.py):

### 3.1 PDF Layout Detection & Bounding Box
- `extract_clean_label_bbox(page: pymupdf.Page) -> Tuple[pymupdf.Rect, int]`
  - Searches for `"Sendungsinformation"`.
  - **DHL Paketmarke (Online Frankierung)**: Sendungsinformation is at the bottom ($y > 0.4h$). The label is in the top section ($y \le 416, 15 \le x \le 585$). Returns the computed bounding box and `rot = 270`.
  - **DHL Retoure (momox / GKP)**: Sendungsinformation is on the left ($x < 0.5w$). The label is on the right half ($x \ge 0.5w$). Returns bounding box and `rot = 0`.
  - **Universal Fallback**: Safe defaults if no markers are matched.

### 3.2 Page Rendering & Margin Geometry
- `process_single_pdf(input_path: str, output_path: str, margin: float = 12.0) -> str`
  - Rotates and scales according to `rot`:
    ```python
    if rot in (90, 270):
        content_w = bbox.height
        content_h = bbox.width
    else:
        content_w = bbox.width
        content_h = bbox.height

    target_w = content_w + 2 * margin
    target_h = content_h + 2 * margin

    new_page = out_doc.new_page(width=target_w, height=target_h)
    dest_rect = pymupdf.Rect(margin, margin, margin + content_w, margin + content_h)
    new_page.show_pdf_page(dest_rect, src_doc, page.number, clip=bbox, rotate=rot)
    ```

### 3.3 Batch Processing
- `process_batch(input_paths, output_folder, merge_into_single_pdf, margin) -> List[str]`
  - Iterates over all files. If `merge_into_single_pdf` is set, appends all cropped pages into a single `pymupdf.Document`.

### 3.4 PyQt6 GUI (`run_gui(initial_files=None)`)
- **Drag-and-Drop Area**: Accepts single or multiple PDF files or directories.
- **Queue List (`QListWidget`)**: Displays loaded files; selecting an item updates the preview.
- **Margin SpinBox (`QSpinBox`)**: Adjusts margin in points (0–50 pt, default 12 pt). Automatically triggers live preview re-rendering.
- **Merge Checkbox (`QCheckBox`)**: Toggles between separate PDFs and a single merged file.
- **Live Preview (`QScrollArea`)**: Renders first page at 140 DPI into `QPixmap`.
- **Direct Print**: Uses temporary file and `os.startfile(..., "open")` to invoke default Windows PDF viewer/print dialog.

---

## 4. Development & Build Instructions

### Running Locally
```bash
python dhl_label_splitter.py
# or via batch launcher:
Start-Label-Tool.bat
```

### CLI / Batch Mode
```bash
python dhl_label_splitter.py --batch file1.pdf file2.pdf
```

### Building Standalone Windows Executable
PyInstaller command with exclusions to keep executable size around ~70 MB:
```powershell
pyinstaller --onefile --noconsole --name "DHL_Label_Tool" `
  --exclude-module torch --exclude-module scipy --exclude-module sympy `
  --exclude-module pandas --exclude-module onnxruntime --exclude-module matplotlib `
  --exclude-module jinja2 --exclude-module lxml dhl_label_splitter.py
```

---

## 5. Important Guidelines for AI Agents

- **Do Not Revert Direct Python Execution**: `Start-Label-Tool.bat` must directly invoke `python "%~dp0dhl_label_splitter.py"` unless the user explicitly requests using the built `.exe`.
- **Preserve Orientation**: Shipping labels must remain upright (hochkant / portrait). Do not rotate into landscape orientation.
- **Maintain Margins**: Thermal printer hardware feeds require a ~3–5 mm safety margin around the label edges. Always preserve the `margin` parameter in processing and preview functions.
- **Privacy & Cleanliness**: Never commit actual shipping labels, customer address PDFs, or large compiled binaries (`.exe`) to git.
