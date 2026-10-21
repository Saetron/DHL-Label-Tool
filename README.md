# DHL Label Tool

Tool zur Vorbereitung und Optimierung von DHL-Paketmarken und Retouren-Labels für Thermodrucker (z. B. 4x6 Zoll).

## Funktionen
- **Automatische 90°-Drehung**: Richtet das Label aufrecht (hochkant) aus.
- **Entfernung unnötiger Seiteninhalte**: Schneidet Kundenbelege ("Sendungsinformation für Ihre Unterlagen") und ungenutzte Leerbereiche ab.
- **Konfigurierbarer Randabstand (Margin)**: Standardmäßig ca. 4,2 mm (12 pt), damit keine Barcodes oder Kanten abgeschnitten werden.
- **Stapelverarbeitung (Batch)**: Mehrere PDFs gleichzeitig verarbeiten (als einzelne Dateien oder zusammengefügt in einer Sammel-PDF).
- **Moderne PyQt6 Benutzeroberfläche**: Mit Live-Vorschau und Drag-and-Drop Unterstützung.

## Installation
```bash
pip install -r requirements.txt
```

## Nutzung
- **Per GUI**: `python dhl_label_splitter.py` oder Doppelklick auf `Start-Label-Tool.bat`
- **Per Batch-Drag-and-Drop**: PDF-Dateien einfach auf `Start-Label-Tool.bat` ziehen
- **Per CLI**: `python dhl_label_splitter.py --batch datei1.pdf datei2.pdf`

## Lizenz
Lizenziert unter der [EUPL v1.2](LICENSE).
