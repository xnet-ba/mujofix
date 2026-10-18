"""Glavni prozor: jedan ekran — SCAN, sazetak, odobravanje, progres, izvjestaj.

Tok: SCAN (worker nit) -> sazetak + stiklirana lista -> POPRAVI SVE ->
progres po koracima (sigurno zaustavljanje izmedju koraka) -> izvjestaj +
"Poništi sve" (rollback obrnutim redom). Akcije koje traze UAC se izvrsavaju
samo kad je proces vec admin; inace se preskacu uz dugme "Pokreni kao
administrator" (nista se ne lazira).
"""

from __future__ import annotations

import getpass
import os
import socket as std_socket
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from PySide6.QtCore import Qt, QThread, Signal  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mujofix import cli  # noqa: E402
from mujofix import update  # noqa: E402
from mujofix.actions.base import ActionContext, Runner  # noqa: E402
from mujofix.actions.mapping import finding_to_actions  # noqa: E402
from mujofix.ai.provider import (  # noqa: E402
    AIRequest,
    FallbackChain,
    OfflineProvider,
    compact_findings,
)
from mujofix.ai.sanitize import sanitize  # noqa: E402
from mujofix.i18n.strings import tr  # noqa: E402
from mujofix.platform import windows  # noqa: E402
from mujofix.ui.consent import ConsentDialog, SentLogViewer  # noqa: E402

QUARANTINE_SUBDIR = "quarantine"


def default_quarantine_dir() -> str:
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    path = os.path.join(base, "MujoFix", QUARANTINE_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


class ScanWorker(QThread):
    done = Signal(list)

    def __init__(self, scan_fn, parent=None):
        super().__init__(parent)
        self._scan_fn = scan_fn

    def run(self):
        self.done.emit(self._scan_fn())


class UpdateWorker(QThread):
    """info=None -> provjeri; info=<dict> -> preuzmi i pokreni."""

    done = Signal(dict)
    failed = Signal(str)

    def __init__(self, api_url, info=None, parent=None):
        super().__init__(parent)
        self._api = api_url
        self._info = info

    def run(self):
        try:
            if self._info is None:
                self.done.emit(update.check_for_update(api_url=self._api))
            else:
                info = dict(self._info)
                info["result"] = update.apply_update(info)
                self.done.emit(info)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, scan_fn=None, quarantine_dir=None, lang: str = "bs"):
        super().__init__()
        self.lang = lang
        self._t = lambda key, **kw: tr(key, lang, **kw)
        self._scan_fn = scan_fn or (lambda: cli.run_scan(None))
        self._ctx = ActionContext(
            quarantine_dir=quarantine_dir or default_quarantine_dir())
        self._runner = Runner()
        self._is_admin = windows.is_admin()
        self._findings: list[dict] = []
        self._undone: list = []  # (action, state) uspjesnih, za "Ponisti sve"
        self._worker: QThread | None = None
        self._upd: QThread | None = None
        self._stop_requested = False
        self._chain: FallbackChain | None = None
        self._build_ui()

    # -- UI -----------------------------------------------------------------
    def _build_ui(self):
        self.setWindowTitle(self._t("app_title"))
        self.resize(720, 560)
        root = QWidget()
        layout = QVBoxLayout(root)

        intro = QLabel(self._t("intro"))
        intro.setWordWrap(True)
        intro.setStyleSheet("font-size: 15px;")
        layout.addWidget(intro)

        row = QHBoxLayout()
        self.btn_scan = QPushButton(self._t("scan"))
        self.btn_scan.setStyleSheet("font-size: 18px; padding: 10px;")
        self.btn_scan.clicked.connect(self.start_scan)
        self.btn_cancel = QPushButton(self._t("cancel"))
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.request_stop)
        row.addWidget(self.btn_scan)
        row.addWidget(self.btn_cancel)
        layout.addLayout(row)

        self.lbl_summary = QLabel("")
        self.lbl_summary.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.lbl_summary.setWordWrap(True)
        layout.addWidget(self.lbl_summary)

        sel_row = QHBoxLayout()
        self.btn_all = QPushButton(self._t("select_all"))
        self.btn_all.clicked.connect(lambda: self._check_all(True))
        self.btn_none = QPushButton(self._t("select_none"))
        self.btn_none.clicked.connect(lambda: self._check_all(False))
        self.chk_tech = QCheckBox(self._t("show_tech"))
        self.chk_tech.stateChanged.connect(self._render_list)
        sel_row.addWidget(self.btn_all)
        sel_row.addWidget(self.btn_none)
        sel_row.addWidget(self.chk_tech)
        layout.addLayout(sel_row)

        self.list = QListWidget()
        layout.addWidget(self.list, stretch=1)

        self.btn_fix = QPushButton(self._t("fix_all"))
        self.btn_fix.setStyleSheet("font-size: 18px; padding: 10px;")
        self.btn_fix.setEnabled(False)
        self.btn_fix.clicked.connect(self.start_fix)
        layout.addWidget(self.btn_fix)

        self.btn_elevate = QPushButton(self._t("elevate_button"))
        self.btn_elevate.setVisible(windows.is_windows() and not self._is_admin)
        self.btn_elevate.clicked.connect(self.elevate)
        layout.addWidget(self.btn_elevate)

        self.btn_update = QPushButton(self._t("update_button"))
        self.btn_update.clicked.connect(self.check_updates)
        layout.addWidget(self.btn_update)

        ai_row = QHBoxLayout()
        self.btn_explain = QPushButton(self._t("explain_ai"))
        self.btn_explain.setEnabled(False)
        self.btn_explain.clicked.connect(self.explain_findings)
        self.btn_sent = QPushButton(self._t("sent_log"))
        self.btn_sent.setEnabled(False)
        self.btn_sent.clicked.connect(self.show_sent_log)
        ai_row.addWidget(self.btn_explain)
        ai_row.addWidget(self.btn_sent)
        layout.addLayout(ai_row)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(500)
        layout.addWidget(self.log, stretch=1)

        self.lbl_report = QLabel("")
        self.lbl_report.setWordWrap(True)
        layout.addWidget(self.lbl_report)

        self.btn_undo = QPushButton(self._t("undo_all"))
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self.undo_all)
        layout.addWidget(self.btn_undo)

        self.setCentralWidget(root)

    # -- SCAN ----------------------------------------------------------------
    def start_scan(self):
        self.btn_scan.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self._log("scan...")
        self._worker = ScanWorker(self._scan_fn, self)
        self._worker.done.connect(self._on_scan_done)
        self._worker.start()

    def _on_scan_done(self, reports: list):
        self.btn_scan.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self._findings = [f for r in reports for f in r.get("findings", [])]
        counts = {"CRITICAL": 0, "MEDIUM": 0, "LOW": 0}
        for finding in self._findings:
            counts[finding["severity"]] += 1
        total = sum(counts.values())
        if total == 0:
            self.lbl_summary.setText(self._t("summary_none"))
        else:
            self.lbl_summary.setText(
                self._t("summary_many", n=total) + "\n"
                + self._t("sev_line", c=counts["CRITICAL"],
                          m=counts["MEDIUM"], l=counts["LOW"]))
        self._render_list()
        self.btn_fix.setEnabled(total > 0)
        self.btn_explain.setEnabled(total > 0)

    def _render_list(self):
        self.list.clear()
        show_tech = self.chk_tech.isChecked()
        for finding in self._findings:
            text = (f"[{finding['severity']}] {finding['title']}\n"
                    f"Zašto: {finding['why']}\n"
                    f"Rizik: {finding['risk']}")
            if show_tech and finding.get("tech_details"):
                text += f"\nTehnički: {finding['tech_details']}"
            if not finding_to_actions(finding):
                text += f"\n({self._t('no_autofix')})"
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, finding["id"])
            self.list.addItem(item)

    def _check_all(self, checked: bool):
        state = Qt.Checked if checked else Qt.Unchecked
        for row in range(self.list.count()):
            self.list.item(row).setCheckState(state)

    def approved_findings(self) -> list[dict]:
        approved_ids = {self.list.item(row).data(Qt.UserRole)
                        for row in range(self.list.count())
                        if self.list.item(row).checkState() == Qt.Checked}
        return [f for f in self._findings if f["id"] in approved_ids]

    # -- AI OBJASNJENJE ------------------------------------------------------
    def explain_findings(self):
        try:
            username = getpass.getuser()
        except OSError:
            username = ""
        try:
            hostname = std_socket.gethostname()
        except OSError:
            hostname = ""
        payload = sanitize({"findings": compact_findings(self._findings)},
                           username, hostname)
        if ConsentDialog.stored_choice() is None:
            dlg = ConsentDialog(payload, self)
            if dlg.exec() != dlg.Accepted:
                self._log("AI odbijen — ostajem u offline modu.")
        # Lanac je trenutno offline-only; zivi model se kaci kad server radi
        # (VM validacija, Issue #1). Bezbednost ne zavisi od modela.
        self._chain = FallbackChain([OfflineProvider()])
        resp = self._chain.explain(
            AIRequest(payload["findings"], username, hostname))
        self._log(f"[AI: {resp.model}] {resp.text}")
        self.btn_sent.setEnabled(True)

    def show_sent_log(self):
        if self._chain is not None:
            SentLogViewer(self._chain.sent_log, self).exec()

    # -- ELEVACIJA -----------------------------------------------------------
    def elevate(self):
        """Ponovo pokreni kao admin (UAC); trenutni prozor se zatvara."""
        try:
            started = windows.relaunch_elevated()
        except windows.NotSupported as exc:
            self._log(str(exc))
            return
        if started:
            self._log(self._t("elevate_started"))
            QApplication.instance().quit()
        else:
            self._log(self._t("elevate_denied"))

    # -- AZURIRANJE ----------------------------------------------------------
    def check_updates(self):
        self.btn_update.setEnabled(False)
        self._log(self._t("update_checking"))
        self._upd = UpdateWorker(update.RELEASES_API, self)
        self._upd.done.connect(self._on_update_checked)
        self._upd.failed.connect(self._on_update_failed)
        self._upd.start()

    def _on_update_checked(self, info: dict):
        if not info.get("available"):
            self.btn_update.setEnabled(True)
            QMessageBox.information(
                self, self._t("app_title"),
                self._t("update_uptodate", v=info.get("current", "")))
            return
        asset = info.get("asset") or {}
        answer = QMessageBox.question(
            self, self._t("update_button"),
            self._t("update_available", v=info.get("latest", ""),
                    f=asset.get("name", "")))
        if answer != QMessageBox.Yes:
            self.btn_update.setEnabled(True)
            return
        self._log(self._t("update_checking"))
        self._upd = UpdateWorker(update.RELEASES_API, info, self)
        self._upd.done.connect(self._on_update_applied)
        self._upd.failed.connect(self._on_update_failed)
        self._upd.start()

    def _on_update_applied(self, info: dict):
        path = info.get("result", {}).get("path", "")
        self._log(self._t("update_done", p=path))
        QMessageBox.information(self, self._t("app_title"),
                                self._t("update_done", p=path))
        QApplication.instance().quit()

    def _on_update_failed(self, message: str):
        self.btn_update.setEnabled(True)
        self._log(self._t("update_failed", e=message))
        QMessageBox.warning(self, self._t("app_title"),
                            self._t("update_failed", e=message))

    # -- FIX -----------------------------------------------------------------
    def start_fix(self):
        approved = self.approved_findings()
        steps = [(f, a) for f in approved for a in finding_to_actions(f)]
        if not steps:
            QMessageBox.information(self, self._t("app_title"),
                                    self._t("no_autofix"))
            return
        self.btn_fix.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress.setVisible(True)
        self.progress.setMaximum(len(steps))
        self.progress.setValue(0)
        self._stop_requested = False
        self._undone = []
        ok = skipped = failed = 0
        for finding, action in steps:
            if self._stop_requested:
                self._log("zaustavljeno, vraćam tekući korak po runneru")
                break
            if action.needs_elevation and not self._is_admin:
                self._log(self._t("uac_note", a=action.name))
                skipped += 1
                self.progress.setValue(self.progress.value() + 1)
                continue
            result = self._runner.run(action, self._ctx)
            self._log(f"{action.name}: {result.message}")
            self.progress.setValue(self.progress.value() + 1)
            if result.ok and result.verified and result.state is not None:
                ok += 1
                self._undone.append((action, result.state))
            else:
                failed += 1
        self.btn_cancel.setEnabled(False)
        self.progress.setVisible(False)
        self.lbl_report.setText(
            self._t("report_ok", ok=ok, skip=skipped, fail=failed))
        self.btn_undo.setEnabled(bool(self._undone))
        self.btn_fix.setEnabled(True)

    def undo_all(self):
        count = 0
        for action, state in reversed(self._undone):
            try:
                action.rollback(self._ctx, state)
                count += 1
                self._log(f"poništeno: {action.name}")
            except Exception as exc:
                self._log(f"PONIŠTAVANJE PALO {action.name}: {exc}")
        self._undone = []
        self.btn_undo.setEnabled(False)
        self.lbl_report.setText(self.lbl_report.text()
                                + f" Poništeno: {count}.")

    # -- misc -----------------------------------------------------------------
    def request_stop(self):
        self._stop_requested = True
        self.btn_cancel.setEnabled(False)

    def _log(self, message: str):
        self.log.appendPlainText(message)


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
