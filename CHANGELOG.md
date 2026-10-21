# Changelog

All notable changes to the DHL Label Tool are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.2.0] - 2026-10-21

### Added
- **Configurable Margin**: Added custom padding on all four edges (default: 12 pt / ~4.2 mm) to prevent barcodes, recipient details, and borders from being clipped by thermal printer hardware margins.
- **GUI Margin Controller**: Added an interactive `QSpinBox` in the UI to dynamically adjust margins from 0 to 50 pt with live preview re-rendering.
- **Repository Documentation**: Added `AGENTS.md` developer guide and `CHANGELOG.md`.
- **Git Setup**: Initialized Git repository with comprehensive `.gitignore` and `requirements.txt`.

### Changed
- Rebuilt standalone executable `DHL_Label_Tool.exe` with updated margin geometry.
- Updated default output filename pattern from `_label_randlos.pdf` to `_label.pdf`.

---

## [1.1.0] - 2026-10-19

### Added
- **PyQt6 GUI Application**: Complete graphical user interface with drag-and-drop zone, file queue management, and live rendering preview.
- **Batch Processing**: Support for converting multiple PDFs simultaneously.
- **PDF Merge Option**: Checkbox to combine all processed labels into a single unified multi-page PDF (`Alle_Labels_Sammeldatei.pdf`).
- **Direct Print Integration**: One-click printing of selected labels via system default PDF handler.
- **Batch Script Launcher**: `Start-Label-Tool.bat` for quick launch and drag-and-drop support directly in Windows Explorer.
- **PyInstaller Build Pipeline**: Build configuration to produce a standalone Windows `.exe`.

### Fixed
- Fixed `TypeError` in `BatchLabelTool.__init__()` when passing initial file lists from CLI/batch launcher.
- Uninstalled incompatible legacy `pathlib` PyPI backport package interfering with Python 3.14 standard library.

---

## [1.0.0] - 2026-10-19

### Added
- **Core Splitting Engine**: Automatic identification and extraction of DHL shipping labels using PyMuPDF.
- **Layout Separation**: Automatic discard of sender copy instructions ("Sendungsinformation für Ihre Unterlagen").
- **Auto-Rotation**: 90° upright (portrait / hochkant) rotation for landscape-printed DHL online postage labels.
- **Dual Format Detection**: Support for both DHL Online Frankierung (Paketmarke) and DHL Retoure (momox / GKP) layouts.
- **Vector Bounding Box Extraction**: Boundary calculation based on drawing vectors and text element positions.
