"""Pregled karantina: vrati pojedinacne fajlove ili obrisi odabrane.

Bez ovoga su fajlovi iz RANIJIH sesija bili nedostupni: "Poništi sve" zna samo
za tekuću sesiju, pa je poslije restarta preostajalo samo trajno brisanje.
Fajl bez manifesta nema poznatu originalnu putanju — tada je moguće samo
brisanje (i to se izričito kaže).
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from PySide6.QtWidgets import (  # noqa: E402
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from mujofix.actions.base import (  # noqa: E402
    list_quarantine,
    restore_quarantine_file,
)
from mujofix.i18n.strings import tr  # noqa: E402


def _gb(num_bytes: int) -> str:
    return f"{num_bytes / 1024 ** 3:.3f} GB"


class QuarantineDialog(QDialog):
    """Lista karantina + vrati/obrisi odabrano. Svaka promjena osvjezi listu."""

    def __init__(self, quarantine_dir: str, parent=None, lang: str = "bs"):
        super().__init__(parent)
        self._t = lambda key, **kw: tr(key, lang, **kw)
        self.quarantine_dir = quarantine_dir
        self.lang = lang
        self._entries: list[dict] = []
        self.setWindowTitle(self._t("quarantine_title"))
        self.resize(680, 420)

        layout = QVBoxLayout(self)
        self.info = QLabel()
        self.info.setWordWrap(True)
        layout.addWidget(self.info)

        self.list = QListWidget()
        layout.addWidget(self.list, stretch=1)

        self.details = QPlainTextEdit()
        self.details.setObjectName("log")
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(110)
        layout.addWidget(self.details)

        row = QHBoxLayout()
        self.btn_restore = QPushButton(self._t("quarantine_restore"))
        self.btn_restore.clicked.connect(self.restore_selected)
        self.btn_delete = QPushButton(self._t("quarantine_delete"))
        self.btn_delete.clicked.connect(self.delete_selected)
        row.addWidget(self.btn_restore)
        row.addWidget(self.btn_delete)
        layout.addLayout(row)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.list.currentRowChanged.connect(self._show_details)
        self.refresh()

    # -- podaci -------------------------------------------------------------
    def refresh(self):
        self._entries = list_quarantine(self.quarantine_dir)
        self.list.clear()
        for entry in self._entries:
            when = time.strftime("%Y-%m-%d %H:%M",
                                 time.localtime(entry["mtime"]))
            origin = entry.get("original") or self._t("quarantine_unknown_source")
            item = QListWidgetItem(
                f"{when} · {_gb(entry['size'])} · {entry['name']}\n{origin}")
            self.list.addItem(item)
        total = sum(entry["size"] for entry in self._entries)
        self.info.setText(self._t("quarantine_info", n=len(self._entries),
                                  gb=_gb(total)))
        has_any = bool(self._entries)
        self.btn_delete.setEnabled(has_any)
        self._update_restore_enabled()

    def _selected(self) -> dict | None:
        row = self.list.currentRow()
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None

    def _update_restore_enabled(self):
        entry = self._selected()
        self.btn_restore.setEnabled(bool(entry and entry.get("original")))

    def _show_details(self, _row: int):
        entry = self._selected()
        self._update_restore_enabled()
        if not entry:
            self.details.clear()
            return
        self.details.setPlainText(
            f"{entry['name']}\n{self._t('quarantine_size')}: {_gb(entry['size'])}"
            f"\n{self._t('quarantine_original')}: "
            f"{entry.get('original') or self._t('quarantine_unknown_source')}")

    # -- akcije -------------------------------------------------------------
    def restore_selected(self):
        entry = self._selected()
        if not entry:
            return
        try:
            original = restore_quarantine_file(self.quarantine_dir, entry["name"])
        except OSError as exc:
            QMessageBox.warning(self, self._t("app_title"),
                                self._t("quarantine_restore_failed", e=exc))
        else:
            QMessageBox.information(
                self, self._t("app_title"),
                self._t("quarantine_restored", p=original))
        self.refresh()

    def delete_selected(self):
        entry = self._selected()
        if not entry:
            return
        answer = QMessageBox.question(
            self, self._t("app_title"),
            self._t("quarantine_delete_confirm", name=entry["name"],
                    gb=_gb(entry["size"])))
        if answer != QMessageBox.Yes:
            return
        try:
            os.remove(entry["path"])
        except OSError as exc:
            QMessageBox.warning(self, self._t("app_title"), str(exc))
        self.refresh()
