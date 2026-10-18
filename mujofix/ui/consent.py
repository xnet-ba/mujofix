"""Ekran pristanka za AI + pregled odlaznih zahtjeva.

Default je offline dok korisnik ne pristane. Izbor se pamti u QSettings.
Besplatni modeli su cloud: podaci napustaju racunar — dialog pokazuje
kategorije + TACAN tekst zahtjeva (anonimiziran) koji ide modelu.

Uslovi OpenCode Zen besplatne razine: POTVRDJENI (provjereno 2026-10-18) iz
primarnih izvora — https://opencode.ai/legal/terms-of-service (za neplacene
racune sadrzaj se smije koristiti za unapredjenje usluge) i
https://opencode.ai/v2/docs/console/models/ (provajderi uglavnom
zero-retention, ali pojedini besplatni modeli tokom promo perioda mogu
koristiti podatke za poboljsanje modela; dio zahtjeva se cuva 30 dana).
Dialog zato izricito kaze da besplatna razina NIJE privatna.
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
from mujofix.i18n.strings import tr  # noqa: E402

CATEGORIES_BS = (
    "Šalje se (anonimizirano): vrste i broj nalaza, putanje sistemskih "
    "foldera, imena servisa, verzija Windowsa.\n"
    "Nikad se ne šalje: sadržaj tvojih fajlova, lozinke, tokeni, "
    "korisničko ime, hostname, IP/MAC adrese.\n"
    "Kome: odabrani AI provider (cloud).\n"
    "POTVRDJENO (OpenCode Zen, 2026-10-18): besplatna razina NIJE privatna. "
    "Provajderi su uglavnom zero-retention, ALI: za neplacene racune sadrzaj "
    "smije koristiti za unapredjenje usluge; pojedini besplatni modeli tokom "
    "promo perioda mogu koristiti poslane podatke za poboljsanje modela; "
    "NVIDIA besplatni endpointi se loguju; zahtjevi ka OpenAI/Anthropic "
    "modelima cuvaju se 30 dana. Ne salji licne ili povjerljive podatke.\n"
    "Izvori: opencode.ai/legal/terms-of-service | opencode.ai/v2/docs/console/models/\n"
    "AI se može isključiti bilo kad (povratak na offline mod)."
)

CATEGORIES_EN = (
    "SENT (anonymized): types and count of findings, system folder paths, "
    "service names, Windows version.\n"
    "NEVER sent: contents of your files, passwords, tokens, username, "
    "hostname, IP/MAC addresses.\n"
    "TO WHOM: the selected AI provider (cloud).\n"
    "CONFIRMED (OpenCode Zen, 2026-10-18): the free tier is NOT private. "
    "Providers are mostly zero-retention, BUT: for unpaid accounts content may "
    "be used to improve the service; some free models during a promo period "
    "may use submitted data for model improvement; NVIDIA free endpoints are "
    "logged; requests to OpenAI/Anthropic models are kept for 30 days. Do not "
    "send personal or confidential data.\n"
    "Sources: opencode.ai/legal/terms-of-service | "
    "opencode.ai/v2/docs/console/models/\n"
    "AI can be turned off at any time (back to offline mode)."
)


class ConsentDialog(QDialog):
    SETTINGS_KEY = "ai/consent"

    def __init__(self, example_text: str, parent=None,
                 current: str | None = None, lang: str = "bs"):
        super().__init__(parent)
        self._t = lambda key, **kw: tr(key, lang, **kw)
        self.setWindowTitle(self._t("consent_title"))
        self.resize(560, 480)
        layout = QVBoxLayout(self)
        intro = QLabel(self._t("consent_intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        cats = QLabel(CATEGORIES_BS if lang == "bs"
                      else CATEGORIES_EN)
        cats.setWordWrap(True)
        layout.addWidget(cats)
        if current is not None:
            layout.addWidget(QLabel(self._t(
                "consent_current_on" if current == "on"
                else "consent_current_off")))
        layout.addWidget(QLabel(self._t("consent_example_label")))
        example = QPlainTextEdit(
            example_text if isinstance(example_text, str)
            else json.dumps(example_text, indent=2, ensure_ascii=False))
        example.setReadOnly(True)
        layout.addWidget(example, stretch=1)
        self.chk_remember = QCheckBox(self._t("consent_remember"))
        self.chk_remember.setChecked(True)
        layout.addWidget(self.chk_remember)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(
            self._t("consent_accept"))
        buttons.button(QDialogButtonBox.Cancel).setText(
            self._t("consent_reject"))
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

    def __init__(self, sent_log: list[dict], parent=None, lang: str = "bs"):
        super().__init__(parent)
        self.setWindowTitle(tr("sent_log_title", lang))
        self.resize(560, 400)
        layout = QVBoxLayout(self)
        view = QPlainTextEdit(
            json.dumps(sent_log, indent=2, ensure_ascii=False))
        view.setReadOnly(True)
        layout.addWidget(view, stretch=1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
