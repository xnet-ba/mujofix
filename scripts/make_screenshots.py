"""Generise README snimke (svijetla + tamna tema) iz stvarne aplikacije.

Offscreen render: `python scripts/make_screenshots.py` (bez prikaza prozora).
Snimke su commitovane u `docs/screenshots/` i linkovane iz README-a.
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "screenshots")

FINDINGS = [
    {"id": "disk-temp", "scanner": "disk",
     "title": "Privremeni fajlovi zauzimaju 4.8 GB",
     "why": "Windows TEMP i folderi starih instalacija drže fajlove koji više "
            "nisu potrebni.",
     "severity": "MEDIUM",
     "impact": "Manje slobodnog prostora i sporije instalacije.",
     "risk": "Nizak — fajlovi idu u karantin (30 dana), ne brišu se trajno.",
     "reversible": True,
     "evidence": {"temp_dir": "/tmp", "bytes": 4800000000, "files": 1834},
     "tech_details": "C:\\Windows\\Temp + %LOCALAPPDATA%\\Temp"},
    {"id": "startup-many", "scanner": "startup",
     "title": "14 programa se pokreće uz sistem",
     "why": "Mnogo startup stavki usporava prijavu i drži memoriju zauzetu.",
     "severity": "HIGH", "impact": "Prijava do 40 s duže.",
     "risk": "Srednji — potreban odabir; stanje se čuva i može vratiti.",
     "reversible": True, "evidence": {"count": 14},
     "tech_details": "HKCU\\...\\Run (14)"},
    {"id": "svc-crash", "scanner": "services",
     "title": "Servis 'Fax' se sam zaustavlja",
     "why": "Servis koji često pada ukazuje na grešku ili se ne koristi.",
     "severity": "LOW", "impact": "Bez direktnog uticaja osim što stoji bespotrebno.",
     "risk": "Nizak — automatski start se isključuje, stanje se čuva.",
     "reversible": True, "evidence": {"name": "Fax"},
     "tech_details": "StartType=Automatic"},
]


def shoot(name: str, dark: bool) -> str:
    from PySide6.QtWidgets import QApplication

    from mujofix.ui import theme
    from mujofix.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication(sys.argv)
    theme.apply(app, dark=dark)
    window = MainWindow(scan_fn=lambda: [], quarantine_dir=tempfile.mkdtemp(),
                        audit_dir=tempfile.mkdtemp(), lang="bs",
                        ai_build_fn=lambda *a, **k: None)
    window._findings = [dict(f) for f in FINDINGS]
    window._render_list()
    window.lbl_summary.setText("3 problema: 1 visok, 1 srednji, 1 nizak.")
    window.lbl_report.setText("Popravljeno: 1, preskočeno: 0, neuspjelo: 0.")
    for button in (window.btn_fix, window.btn_explain, window.btn_undo):
        button.setEnabled(True)
    window.log.appendPlainText("scan...")
    window.log.appendPlainText("[startup-many] Nađeno 14 startup stavki")
    window.log.appendPlainText(
        "clean_temp: 1834 fajla prebačena u karantin (4.8 GB)")
    window.log.appendPlainText(
        "Dnevnik izvršavanja sačuvan: C:\\Users\\...\\MujoFix\\audit\\"
        "audit-20261021-145501.json")
    window.resize(760, 640)
    window.show()
    app.processEvents()
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"mujofix-{name}.png")
    window.grab().save(path)
    window.close()
    app.setStyleSheet("")
    return path


def main() -> int:
    for name, dark in (("light", False), ("dark", True)):
        print("saved", shoot(name, dark))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
