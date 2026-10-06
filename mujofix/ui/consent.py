"""Ekran pristanka za AI + pregled odlaznih zahtjeva.

Default je offline dok korisnik ne pristane. Izbor se pamti u QSettings.
Besplatni modeli su cloud: podaci napustaju racunar — dialog pokazuje
kategorije + primjer STVARNOG (anonimiziranog) payload-a. Uslovi OpenCode Zen
razine: NEPOTVRDJENI, dialog to izricito kaze (ne tvrdi "privatno").
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from PySide6.QtWidgets import (  # noqa: E402
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)
from PySide6.QtCore import QSettings  # noqa: E402

CATEGORIES_BS = (
    "Šalje se (anonimizirano): vrste i broj nalaza, putanje sistemskih "
    "foldera, imena servisa, verzija Windowsa.\n"
    "Nikad se ne šalje: sadržaj tvojih fajlova, lozinke, tokeni, "
    "korisničko ime, hostname, IP/MAC adrese.\n"
    "Kome: odabrani AI provider (cloud). Uslovi čuvanja podataka na "
    "besplatnoj razini: NEPOTVRĐENI — ne tvrdimo da su podaci privatni.\n"
    "AI se može isključiti bilo kad (povratak na offline mod)."
)


class ConsentDialog(QDialog):
    SETTINGS_KEY = "ai/consent"

    def __init__(self, example_payload: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MujoFix — pristanak za AI")
        self.resize(560, 480)
        layout = QVBoxLayout(self)
        intro = QLabel(
            "AI objašnjenja znače da podaci o tvom računaru napuštaju računar. "
            "Bez pristanka aplikacija radi u offline modu.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        cats = QLabel(CATEGORIES_BS)
        cats.setWordWrap(True)
        layout.addWidget(cats)
        layout.addWidget(QLabel("Primjer stvarnog payload-a koji bi se poslao:"))
        example = QPlainTextEdit(
            json.dumps(example_payload, indent=2, ensure_ascii=False))
        example.setReadOnly(True)
        layout.addWidget(example, stretch=1)
        self.chk_remember = QCheckBox("Zapamti izbor")
        self.chk_remember.setChecked(True)
        layout.addWidget(self.chk_remember)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Prihvatam AI")
        buttons.button(QDialogButtonBox.Cancel).setText("Ostajem offline")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        if self.chk_remember.isChecked():
            QSettings("MujoFix", "ai").setValue(self.SETTINGS_KEY, "on")
        super().accept()

    def reject(self):
        if self.chk_remember.isChecked():
            QSettings("MujoFix", "ai").setValue(self.SETTINGS_KEY, "off")
        super().reject()

    @classmethod
    def stored_choice(cls) -> str | None:
        value = QSettings("MujoFix", "ai").value(cls.SETTINGS_KEY)
        return str(value) if value in ("on", "off") else None


class SentLogViewer(QDialog):
    """"Pogledaj tacno sta je poslano": citljiv prikaz odlaznih zahtjeva."""

    def __init__(self, sent_log: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("MujoFix — šta je poslano AI-ju")
        self.resize(560, 400)
        layout = QVBoxLayout(self)
        view = QPlainTextEdit(
            json.dumps(sent_log, indent=2, ensure_ascii=False))
        view.setReadOnly(True)
        layout.addWidget(view, stretch=1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
