"""
DHL Label Tool für Labeldrucker (Randlos & Batch-fähig)
- Verwirft die Kundenseite ohne Barcodes ("Sendungsinformation für Ihre Unterlagen")
- Dreht das Versandlabel automatisch aufrecht (90°-Drehung)
- Entfernt weiße Ränder (Randlos / 0 Margin exakt am Labelinhalt)
- Unterstützt Stapelverarbeitung (Batch): Mehrere PDFs gleichzeitig umwandeln oder zusammenführen
- GUI & Drag-and-Drop direkt auf die EXE
"""

import sys
import os
import glob
from typing import List, Tuple
import pymupdf


def extract_clean_label_bbox(page: pymupdf.Page) -> Tuple[pymupdf.Rect, int]:
    """
    Ermittelt die exakte Bounding-Box des Versandlabels (ohne weiße Ränder)
    und die Drehung, um das Label aufrecht zu stellen.
    """
    w, h = page.rect.width, page.rect.height

    si_matches = page.search_for("Sendungsinformation")
    
    if si_matches and si_matches[0].y0 > h * 0.4:
        # Typ: DHL Paketmarke (Sendungsinformation liegt unten, Label liegt oben)
        drawings = [d['rect'] for d in page.get_drawings() if 10 <= d['rect'].y1 <= 416 and 15 <= d['rect'].x0 <= 585]
        words = [pymupdf.Rect(wrd[:4]) for wrd in page.get_text('words') if 10 <= wrd[1] <= 416 and 15 <= wrd[0] <= 585]
        all_items = drawings + words
        if all_items:
            bbox = pymupdf.Rect(
                min(r.x0 for r in all_items),
                min(r.y0 for r in all_items),
                max(r.x1 for r in all_items),
                max(r.y1 for r in all_items)
            )
        else:
            bbox = pymupdf.Rect(20.0, 65.0, 565.0, 355.0)
        return bbox, 270

    elif si_matches and si_matches[0].x0 < w * 0.5:
        # Typ: DHL Retoure (Sendungsinformation liegt links, Label liegt rechts)
        drawings = [d['rect'] for d in page.get_drawings() if d['rect'].x0 >= w * 0.5]
        words = [pymupdf.Rect(wrd[:4]) for wrd in page.get_text('words') if wrd[0] >= w * 0.5]
        all_items = drawings + words
        if all_items:
            bbox = pymupdf.Rect(
                min(r.x0 for r in all_items),
                min(r.y0 for r in all_items),
                max(r.x1 for r in all_items),
                max(r.y1 for r in all_items)
            )
        else:
            bbox = pymupdf.Rect(w * 0.505, 50.0, w - 5.0, h - 10.0)
        return bbox, 0

    else:
        # Universeller Fallback
        drawings = [d['rect'] for d in page.get_drawings() if d['rect'].y1 <= h * 0.49 and d['rect'].x0 >= 15]
        words = [pymupdf.Rect(wrd[:4]) for wrd in page.get_text('words') if wrd[1] <= h * 0.49 and wrd[0] >= 15]
        all_items = drawings + words
        if all_items:
            bbox = pymupdf.Rect(
                min(r.x0 for r in all_items),
                min(r.y0 for r in all_items),
                max(r.x1 for r in all_items),
                max(r.y1 for r in all_items)
            )
        else:
            bbox = pymupdf.Rect(20.0, 65.0, 565.0, 355.0)
        return bbox, 270


def process_single_pdf(input_path: str, output_path: str, margin: float = 12.0) -> str:
    """Verarbeitet eine einzelne PDF-Datei und schneidet sie mit definiertem Rand (Margin) zu."""
    src_doc = pymupdf.open(input_path)
    out_doc = pymupdf.open()

    for page in src_doc:
        bbox, rot = extract_clean_label_bbox(page)

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

    out_doc.save(output_path)
    out_doc.close()
    src_doc.close()
    return output_path


def process_batch(input_paths: List[str], output_folder: str = "", merge_into_single_pdf: str = "", margin: float = 12.0) -> List[str]:
    """Verarbeitet mehrere PDF-Dateien im Stapel (Batch) mit Rand (Margin)."""
    results = []
    merged_doc = pymupdf.open() if merge_into_single_pdf else None

    for in_path in input_paths:
        if not os.path.isfile(in_path) or not in_path.lower().endswith(".pdf"):
            continue

        base = os.path.basename(in_path)
        out_folder = output_folder if output_folder else os.path.dirname(in_path)
        out_name = os.path.splitext(base)[0] + "_label.pdf"
        out_path = os.path.join(out_folder, out_name)

        if merge_into_single_pdf:
            src_doc = pymupdf.open(in_path)
            for page in src_doc:
                bbox, rot = extract_clean_label_bbox(page)
                if rot in (90, 270):
                    content_w = bbox.height
                    content_h = bbox.width
                else:
                    content_w = bbox.width
                    content_h = bbox.height

                target_w = content_w + 2 * margin
                target_h = content_h + 2 * margin

                p = merged_doc.new_page(width=target_w, height=target_h)
                dest_rect = pymupdf.Rect(margin, margin, margin + content_w, margin + content_h)
                p.show_pdf_page(dest_rect, src_doc, page.number, clip=bbox, rotate=rot)
            src_doc.close()
        else:
            process_single_pdf(in_path, out_path, margin=margin)
            results.append(out_path)

    if merge_into_single_pdf and merged_doc:
        merged_doc.save(merge_into_single_pdf)
        merged_doc.close()
        results.append(merge_into_single_pdf)

    return results


def run_gui(initial_files: List[str] = None):
    """Startet die moderne PyQt6-Benutzeroberfläche mit Batch-Funktion."""
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QFileDialog, QGroupBox, QScrollArea,
        QMessageBox, QFrame, QListWidget, QCheckBox, QSpinBox
    )
    from PyQt6.QtGui import QPixmap, QImage, QDragEnterEvent, QDropEvent
    from PyQt6.QtCore import Qt

    class BatchLabelTool(QMainWindow):
        def __init__(self, initial_files=None):
            super().__init__()
            self.setWindowTitle("DHL Label Tool (Randlos & Batch)")
            self.setMinimumSize(960, 750)
            self.files = []
            self.setup_ui()

            if initial_files:
                self.add_files(initial_files)
            else:
                # Prüfe Standard-Downloads
                for candidate in [
                    r"C:\Users\jbudz.SUSSYNET\Downloads\DHL-Paketmarke_PAKM66HC4LYH_Paul_Schlenker.pdf",
                    r"C:\Users\jbudz.SUSSYNET\Downloads\Label.pdf"
                ]:
                    if os.path.isfile(candidate):
                        self.add_files([candidate])
                        break

        def setup_ui(self):
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            main_layout = QHBoxLayout(main_widget)
            main_layout.setContentsMargins(16, 16, 16, 16)
            main_layout.setSpacing(16)

            left_panel = QWidget()
            left_layout = QVBoxLayout(left_panel)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.setSpacing(12)
            left_panel.setFixedWidth(380)

            self.drop_label = QLabel("PDFs hier ablegen\n(Einzeln oder mehrere für Stapelverarbeitung)")
            self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.drop_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #0066cc;
                    border-radius: 8px;
                    background-color: #f0f7ff;
                    color: #004488;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 20px;
                }
                QLabel:hover {
                    background-color: #e5f1ff;
                    border-color: #004488;
                }
            """)
            self.drop_label.setAcceptDrops(True)
            self.drop_label.mousePressEvent = lambda e: self.choose_files()
            self.drop_label.dragEnterEvent = self.drag_enter_event
            self.drop_label.dropEvent = self.drop_event
            left_layout.addWidget(self.drop_label)

            list_group = QGroupBox("Dateien in der Warteschlange")
            list_group.setStyleSheet("QGroupBox { font-weight: bold; }")
            list_layout = QVBoxLayout(list_group)

            self.file_list = QListWidget()
            self.file_list.setStyleSheet("font-size: 11px;")
            self.file_list.currentRowChanged.connect(self.on_selection_changed)
            list_layout.addWidget(self.file_list)

            btn_file_layout = QHBoxLayout()
            btn_add = QPushButton("+ Dateien...")
            btn_add.clicked.connect(self.choose_files)
            btn_clear = QPushButton("Liste leeren")
            btn_clear.clicked.connect(self.clear_files)
            btn_file_layout.addWidget(btn_add)
            btn_file_layout.addWidget(btn_clear)
            list_layout.addLayout(btn_file_layout)

            left_layout.addWidget(list_group)

            margin_layout = QHBoxLayout()
            margin_label = QLabel("Randabstand (Margin):")
            margin_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            self.margin_spin = QSpinBox()
            self.margin_spin.setRange(0, 50)
            self.margin_spin.setValue(12)
            self.margin_spin.setSuffix(" pt")
            self.margin_spin.setToolTip("Abstand um das Label (12 pt ≈ 4,2 mm)")
            self.margin_spin.valueChanged.connect(self.on_margin_changed)
            margin_layout.addWidget(margin_label)
            margin_layout.addWidget(self.margin_spin)
            left_layout.addLayout(margin_layout)

            self.cb_merge = QCheckBox("Alle in einer Sammel-PDF zusammenführen")
            self.cb_merge.setStyleSheet("font-weight: bold; color: #222;")
            left_layout.addWidget(self.cb_merge)

            self.btn_convert_all = QPushButton("Alle umwandeln (Batch)...")
            self.btn_convert_all.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 12px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #0060aa;
                }
                QPushButton:disabled {
                    background-color: #ccc;
                    color: #888;
                }
            """)
            self.btn_convert_all.setEnabled(False)
            self.btn_convert_all.clicked.connect(self.convert_all)
            left_layout.addWidget(self.btn_convert_all)

            self.btn_print_current = QPushButton("Ausgewähltes Label drucken...")
            self.btn_print_current.setStyleSheet("""
                QPushButton {
                    background-color: #2b882b;
                    color: white;
                    font-weight: bold;
                    font-size: 13px;
                    padding: 10px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #206620;
                }
                QPushButton:disabled {
                    background-color: #ccc;
                    color: #888;
                }
            """)
            self.btn_print_current.setEnabled(False)
            self.btn_print_current.clicked.connect(self.print_selected)
            left_layout.addWidget(self.btn_print_current)

            self.status_label = QLabel("Bereit")
            self.status_label.setStyleSheet("color: #666; font-size: 12px;")
            left_layout.addWidget(self.status_label)

            main_layout.addWidget(left_panel)

            right_panel = QGroupBox("Vorschau: Versandlabel (hochkant mit Rand)")
            right_panel.setStyleSheet("QGroupBox { font-weight: bold; }")
            right_layout = QVBoxLayout(right_panel)

            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_content = QWidget()
            self.scroll_layout = QHBoxLayout(self.scroll_content)
            self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_area.setWidget(self.scroll_content)

            right_layout.addWidget(self.scroll_area)
            main_layout.addWidget(right_panel, 1)

        def drag_enter_event(self, event: QDragEnterEvent):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()

        def drop_event(self, event: QDropEvent):
            paths = []
            for url in event.mimeData().urls():
                p = url.toLocalFile()
                if os.path.isfile(p) and p.lower().endswith(".pdf"):
                    paths.append(p)
                elif os.path.isdir(p):
                    for sub in glob.glob(os.path.join(p, "*.pdf")):
                        paths.append(sub)
            if paths:
                self.add_files(paths)

        def choose_files(self):
            paths, _ = QFileDialog.getOpenFileNames(
                self, "DHL PDFs auswählen (Mehrfachauswahl möglich)", "", "PDF-Dokumente (*.pdf)"
            )
            if paths:
                self.add_files(paths)

        def add_files(self, paths: List[str]):
            for p in paths:
                if p not in self.files and os.path.isfile(p):
                    self.files.append(p)
                    self.file_list.addItem(os.path.basename(p))

            self.btn_convert_all.setEnabled(len(self.files) > 0)
            self.btn_print_current.setEnabled(len(self.files) > 0)
            self.status_label.setText(f"{len(self.files)} Datei(en) geladen")
            if self.file_list.currentRow() < 0 and self.files:
                self.file_list.setCurrentRow(0)

        def clear_files(self):
            self.files.clear()
            self.file_list.clear()
            self.btn_convert_all.setEnabled(False)
            self.btn_print_current.setEnabled(False)
            self.status_label.setText("Liste geleert")
            self.clear_preview()

        def on_selection_changed(self, row: int):
            if 0 <= row < len(self.files):
                self.update_preview(self.files[row])

        def on_margin_changed(self):
            row = self.file_list.currentRow()
            if 0 <= row < len(self.files):
                self.update_preview(self.files[row])

        def clear_preview(self):
            while self.scroll_layout.count():
                item = self.scroll_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

        def update_preview(self, pdf_path: str):
            self.clear_preview()
            if not os.path.isfile(pdf_path):
                return

            try:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
                    temp_preview_pdf = tf.name

                margin = float(self.margin_spin.value())
                process_single_pdf(pdf_path, temp_preview_pdf, margin=margin)

                preview_doc = pymupdf.open(temp_preview_pdf)
                page = preview_doc[0]
                pix = page.get_pixmap(dpi=140)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                qpix = QPixmap.fromImage(img)

                card = QFrame()
                card.setFrameShape(QFrame.Shape.StyledPanel)
                card.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border: 2px solid #0066cc;
                        border-radius: 4px;
                        padding: 4px;
                    }
                """)
                card_layout = QVBoxLayout(card)

                img_lbl = QLabel()
                img_lbl.setPixmap(qpix)
                img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                card_layout.addWidget(img_lbl)

                size_lbl = QLabel(f"Label ({pix.width} × {pix.height} px | Rand: {int(margin)} pt)")
                size_lbl.setStyleSheet("color: #666; font-size: 11px;")
                size_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                card_layout.addWidget(size_lbl)

                self.scroll_layout.addWidget(card)
                preview_doc.close()

                try:
                    os.remove(temp_preview_pdf)
                except Exception:
                    pass
            except Exception as ex:
                self.status_label.setText(f"Vorschau-Fehler: {ex}")

        def convert_all(self):
            if not self.files:
                return

            margin = float(self.margin_spin.value())
            if self.cb_merge.isChecked():
                default_name = os.path.join(os.path.dirname(self.files[0]), "Alle_Labels_Sammeldatei.pdf")
                save_path, _ = QFileDialog.getSaveFileName(
                    self, "Sammel-PDF speichern", default_name, "PDF-Dokumente (*.pdf)"
                )
                if not save_path:
                    return
                process_batch(self.files, merge_into_single_pdf=save_path, margin=margin)
                QMessageBox.information(self, "Erfolg", f"Sammel-PDF mit allen Labels erstellt:\n{save_path}")
            else:
                out_folder = QFileDialog.getExistingDirectory(self, "Zielordner für umgewandelte Labels wählen", os.path.dirname(self.files[0]))
                if not out_folder:
                    return
                results = process_batch(self.files, output_folder=out_folder, margin=margin)
                QMessageBox.information(self, "Erfolg", f"{len(results)} Labels erfolgreich umgewandelt im Ordner:\n{out_folder}")

        def print_selected(self):
            row = self.file_list.currentRow()
            if row < 0 or row >= len(self.files):
                return
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
                temp_print_pdf = tf.name
            margin = float(self.margin_spin.value())
            process_single_pdf(self.files[row], temp_print_pdf, margin=margin)
            os.startfile(temp_print_pdf, "open")

    app = QApplication(sys.argv)
    window = BatchLabelTool(initial_files=initial_files)
    window.show()
    sys.exit(app.exec())


def main():
    files = [arg for arg in sys.argv[1:] if not arg.startswith("-") and os.path.isfile(arg)]

    # Wenn Batch-Flag explizit übergeben wird
    if "--batch" in sys.argv:
        results = process_batch(files)
        print(f"Batch abgeschlossen: {len(results)} Datei(en) umgewandelt.")
    else:
        # Standard: GUI starten (mit optional übergebenen Dateien vorgeladen)
        run_gui(initial_files=files)


if __name__ == "__main__":
    main()
