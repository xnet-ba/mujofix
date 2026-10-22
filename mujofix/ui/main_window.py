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

from PySide6.QtCore import QSettings, Qt, QThread, Signal  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QCheckBox,
    QComboBox,
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

from mujofix import audit  # noqa: E402
from mujofix import cli  # noqa: E402
from mujofix import update  # noqa: E402
from mujofix.actions.base import (  # noqa: E402
    ActionContext,
    Runner,
    purge_quarantine,
    quarantine_usage,
)
from mujofix.actions.mapping import finding_to_actions  # noqa: E402
from mujofix.ai.provider import (  # noqa: E402
    AIRequest,
    FallbackChain,
    build_chain,
    build_prompt,
    compact_findings,
    plan_lines,
)
from mujofix.ai.sanitize import sanitize  # noqa: E402
from mujofix.i18n.strings import tr  # noqa: E402
from mujofix.platform import windows  # noqa: E402
from mujofix.ui import theme  # noqa: E402
from mujofix.ui.quarantine import QuarantineDialog  # noqa: E402
from mujofix.ui.consent import ConsentDialog, SentLogViewer  # noqa: E402

QUARANTINE_SUBDIR = "quarantine"
AI_SUBDIR = "ai"


SETTINGS_ORG = "MujoFix"
SETTINGS_APP = "ui"
SUPPORTED_LANGS = ("bs", "en")


def stored_lang() -> str:
    """Sacuvani jezik iz QSettings; "bs" ako nista nije izabrano."""
    value = str(QSettings(SETTINGS_ORG, SETTINGS_APP).value("lang", "bs"))
    return value if value in SUPPORTED_LANGS else "bs"


def store_lang(lang: str) -> None:
    if lang in SUPPORTED_LANGS:
        QSettings(SETTINGS_ORG, SETTINGS_APP).setValue("lang", lang)


def default_quarantine_dir() -> str:
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    path = os.path.join(base, "MujoFix", QUARANTINE_SUBDIR)
    os.makedirs(path, exist_ok=True)
    return path


def _gb(num_bytes: int) -> str:
    """Bajtovi u citljive GB (jedna decimala), kao u scannerima."""
    return f"{num_bytes / 1024 ** 3:.1f} GB"


def default_audit_dir() -> str:
    """Folder za JSON dnevnik izvrsavanja (%LOCALAPPDATA%\\MujoFix\\audit).

    Ne pravi folder: `audit.write_record` ga napravi tek kad stvarno ima
    zapisa (nema praznih foldera na prvom pokretanju).
    """
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(base, "MujoFix", "audit")


def default_ai_workdir() -> str:
    """Radni dir za opencode child — tu se upisuje izolirani opencode.json.

    Ne smije biti cwd (u zamrznutom EXE-u moze biti nezapisiv, npr. System32).
    Dir ne pravimo ovdje: kreira ga `agent_config.write_config`, a kvar postaje
    iskren offline razlog umjesto pada GUI-a.
    """
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(base, "MujoFix", AI_SUBDIR)


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


class ExplainWorker(QThread):
    """Gradi lanac i objasnjava — van GUI niti (bez servera).

    Poziv modela zna potrajati, pa ne smije blokirati prozor. Sesiju vraca u
    `done` da GUI zna stanje (live/offline) i iskren razlog.
    """

    done = Signal(object, object)  # LiveSession, AIResponse
    failed = Signal(str)

    def __init__(self, findings, username, hostname, consent_on,
                 build_fn=None, workdir=None, parent=None, lang="bs"):
        super().__init__(parent)
        self._findings = findings
        self._username = username
        self._hostname = hostname
        self._consent_on = consent_on
        self._build = build_fn or build_chain
        self._workdir = workdir
        self._lang = lang

    def run(self):
        try:
            if self._build is build_chain:
                # pravi lanac: prosledi jezik (offline tekst je dvojezican)
                session = self._build(self._consent_on, self._workdir,
                                      lang=self._lang)
            else:
                # injektovan builder (testovi) — drzi se postojeceg ugovora
                session = self._build(self._consent_on, self._workdir)
            resp = session.chain.explain(
                AIRequest(self._findings, self._username, self._hostname))
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.done.emit(session, resp)


class MainWindow(QMainWindow):
    def __init__(self, scan_fn=None, quarantine_dir=None, lang: str = "bs",
                 ai_build_fn=None, ai_workdir=None, audit_dir=None):
        super().__init__()
        self.lang = lang
        self._t = lambda key, **kw: tr(key, lang, **kw)
        self._scan_fn = scan_fn or (lambda: cli.run_scan(None))
        self._ai_build_fn = ai_build_fn
        self._ai_workdir = ai_workdir
        self._audit_dir = audit_dir or default_audit_dir()
        self._ctx = ActionContext(
            quarantine_dir=quarantine_dir or default_quarantine_dir())
        self._runner = Runner()
        self._is_admin = windows.is_admin()
        self._findings: list[dict] = []
        self._undone: list = []  # (action, state) uspjesnih, za "Ponisti sve"
        self._worker: QThread | None = None
        self._upd: QThread | None = None
        self._ai: QThread | None = None
        self._session = None
        self._stop_requested = False
        self._chain: FallbackChain | None = None
        self._build_ui()

    # -- UI -----------------------------------------------------------------
    def _build_ui(self):
        self.setWindowTitle(self._t("app_title"))
        self.resize(720, 560)
        root = QWidget()
        root.setObjectName("root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        intro = QLabel(self._t("intro"))
        intro.setObjectName("subtitle")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        row = QHBoxLayout()
        self.btn_scan = QPushButton(self._t("scan"))
        self.btn_scan.setObjectName("primary")
        self.btn_scan.clicked.connect(self.start_scan)
        self.btn_cancel = QPushButton(self._t("cancel"))
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.request_stop)
        row.addWidget(self.btn_scan)
        row.addWidget(self.btn_cancel)
        layout.addLayout(row)

        self.lbl_summary = QLabel("")
        self.lbl_summary.setObjectName("h1")
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
        self.list.setObjectName("findings")
        layout.addWidget(self.list, stretch=1)

        self.btn_fix = QPushButton(self._t("fix_all"))
        self.btn_fix.setObjectName("primary")
        self.btn_fix.setEnabled(False)
        self.btn_fix.clicked.connect(self.start_fix)
        layout.addWidget(self.btn_fix)

        self.chk_dry = QCheckBox(self._t("dry_run_label"))
        layout.addWidget(self.chk_dry)

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
        self.btn_consent = QPushButton(self._t("ai_settings"))
        self.btn_consent.clicked.connect(self.open_consent_settings)
        ai_row.addWidget(self.btn_explain)
        ai_row.addWidget(self.btn_sent)
        ai_row.addWidget(self.btn_consent)
        layout.addLayout(ai_row)

        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel(self._t("lang_label")))
        self.cmb_lang = QComboBox()
        self.cmb_lang.addItem("Bosanski", "bs")
        self.cmb_lang.addItem("English", "en")
        self.cmb_lang.setCurrentIndex(
            0 if self.lang == "bs" else 1)
        self.cmb_lang.currentIndexChanged.connect(self._on_lang_changed)
        lang_row.addWidget(self.cmb_lang)
        lang_row.addStretch(1)
        layout.addLayout(lang_row)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.log = QPlainTextEdit()
        self.log.setObjectName("log")
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(500)
        layout.addWidget(self.log, stretch=1)

        self.lbl_report = QLabel("")
        self.lbl_report.setObjectName("report")
        self.lbl_report.setWordWrap(True)
        layout.addWidget(self.lbl_report)

        report_row = QHBoxLayout()
        self.btn_undo = QPushButton(self._t("undo_all"))
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self.undo_all)
        self.btn_purge = QPushButton(self._t("purge_quarantine"))
        self.btn_purge.clicked.connect(self.purge_quarantine_clicked)
        self.btn_quarantine = QPushButton(self._t("quarantine_view"))
        self.btn_quarantine.clicked.connect(self.open_quarantine)
        report_row.addWidget(self.btn_undo)
        report_row.addWidget(self.btn_purge)
        report_row.addWidget(self.btn_quarantine)
        layout.addLayout(report_row)
        self._refresh_quarantine_button()

        self.setCentralWidget(root)

    # -- SCAN ----------------------------------------------------------------
    def start_scan(self):
        self.btn_scan.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self._log(self._t("log_scanning"))
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
    def _on_lang_changed(self, index: int):
        """Izbor jezika se pamti; primjenjuje se pri sljedecem pokretanju."""
        store_lang(self.cmb_lang.currentData())
        self._log(self._t("lang_restart"))

    def _restore_geometry(self):
        saved = QSettings(SETTINGS_ORG, SETTINGS_APP).value("geometry")
        if saved is not None:
            self.restoreGeometry(saved)

    def _save_geometry(self):
        QSettings(SETTINGS_ORG, SETTINGS_APP).setValue(
            "geometry", self.saveGeometry())

    def _identity(self) -> tuple[str, str]:
        """(korisnik, racunar) — treba za anonimizaciju prije slanja."""
        try:
            username = getpass.getuser()
        except OSError:
            username = ""
        try:
            hostname = std_socket.gethostname()
        except OSError:
            hostname = ""
        return username, hostname

    def _example_prompt(self) -> str:
        """Tacan tekst zahtjeva za OVE nalaze (isti koji gradi i provider)."""
        username, hostname = self._identity()
        payload = sanitize({"findings": compact_findings(self._findings)},
                           username, hostname)
        return build_prompt(payload["findings"])

    def open_consent_settings(self):
        """Ukljuci/iskljuci AI bilo kad — obecanje iz ekrana pristanka."""
        text = (self._example_prompt() if self._findings
                else self._t("ai_example_none"))
        dlg = ConsentDialog(text, self,
                            current=ConsentDialog.stored_choice(),
                            lang=self.lang)
        dlg.exec()
        choice = ConsentDialog.stored_choice()
        self._log(self._t("ai_state_now",
                          s=self._t("ai_state_on" if choice == "on"
                                    else "ai_state_off")))

    def explain_findings(self):
        username, hostname = self._identity()
        payload = sanitize({"findings": compact_findings(self._findings)},
                           username, hostname)
        if ConsentDialog.stored_choice() is None:
            dlg = ConsentDialog(build_prompt(payload["findings"]), self,
                                lang=self.lang)
            if dlg.exec() != dlg.Accepted:
                self._log(self._t("log_ai_declined"))
        # Bez pristanka lanac je offline; sa pristankom se u pozadini proba ziv
        # Zen (free model), a svaki kvar se iskreno prijavi i vrati na offline.
        consent_on = ConsentDialog.stored_choice() == "on"
        self.btn_explain.setEnabled(False)
        self._log(self._t("log_ai_explaining"))
        self._ai = ExplainWorker(payload["findings"], username, hostname,
                                 consent_on, build_fn=self._ai_build_fn,
                                 workdir=self._ai_workdir or default_ai_workdir(),
                                 parent=self, lang=self.lang)
        self._ai.done.connect(self._on_explained)
        self._ai.failed.connect(self._on_explain_failed)
        self._ai.start()

    def _on_explained(self, session, resp):
        self._session = session
        self._chain = session.chain
        self._log(f"[{session.note}]")
        self._log(f"[AI: {resp.model}] {resp.text}")
        # Plan je PREDLOG koji korisnik vidi; primjena ide preko akcija
        # odabranih nalaza (deterministicki, sa verify + rollback).
        plan = plan_lines(resp.plan)
        if plan:
            self._log(self._t("plan_ai_header"))
            for line in plan:
                self._log("   " + line)
        self.btn_sent.setEnabled(True)
        self.btn_explain.setEnabled(True)

    def _on_explain_failed(self, message: str):
        self._log(self._t("log_ai_failed", m=message))
        self.btn_explain.setEnabled(True)

    def show_sent_log(self):
        if self._chain is not None:
            SentLogViewer(self._chain.sent_log, self, lang=self.lang).exec()

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
        dry = self.chk_dry.isChecked()
        self._ctx.dry_run = dry
        ok = skipped = failed = 0
        for finding, action in steps:
            if self._stop_requested:
                self._log(self._t("fix_stopped"))
                break
            if action.needs_elevation and not self._is_admin:
                self._log(self._t("uac_note", a=action.name))
                skipped += 1
                self.progress.setValue(self.progress.value() + 1)
                continue
            result = self._runner.run(action, self._ctx)
            self._log(f"{action.name}: {result.message}")
            self.progress.setValue(self.progress.value() + 1)
            if result.dry_run:
                if result.ok:
                    ok += 1
                else:
                    failed += 1
            elif result.ok and result.verified and result.state is not None:
                ok += 1
                self._undone.append((action, result.state))
            else:
                failed += 1
        self.btn_cancel.setEnabled(False)
        self.progress.setVisible(False)
        if dry:
            self.lbl_report.setText(
                self._t("report_dry", ok=ok, skip=skipped, fail=failed))
        else:
            self.lbl_report.setText(
                self._t("report_ok", ok=ok, skip=skipped, fail=failed))
        self._write_audit(dry, ok, skipped, failed)
        self._refresh_quarantine_button()
        self.btn_undo.setEnabled(bool(self._undone))
        self.btn_fix.setEnabled(True)

    def _write_audit(self, dry: bool, ok: int, skipped: int, failed: int,
                     suffix: str = "", steps: list[dict] | None = None):
        """Upisi JSON dnevnik koraka; kvar dnevnika ne smije srusiti app."""
        try:
            path = audit.audit_path(self._audit_dir, suffix=suffix)
            audit.write_record(path, audit.build_record(
                self._runner.audit if steps is None else steps,
                {"ok": ok, "skipped": skipped, "failed": failed}, dry))
            self._log(self._t("audit_saved", p=path))
        except Exception as exc:
            self._log(self._t("audit_failed", e=exc))

    def _refresh_quarantine_button(self):
        """Dugme za ciscenje karantina pokazuje koliko je tamo i zauzeto."""
        files, total = quarantine_usage(self._ctx.quarantine_dir)
        self._quarantine_usage = (files, total)
        self.btn_purge.setEnabled(files > 0)
        if files:
            self.btn_purge.setText(
                self._t("purge_quarantine_now", n=files, gb=_gb(total)))
            self.btn_quarantine.setText(self._t("quarantine_view_now", n=files))
        else:
            self.btn_purge.setText(self._t("purge_quarantine"))
            self.btn_quarantine.setText(self._t("quarantine_view"))

    def open_quarantine(self):
        """Pregled karantina — vracanje pojedinacnih fajlova iz ranijih sesija."""
        dialog = QuarantineDialog(self._ctx.quarantine_dir, self,
                                  lang=self.lang)
        dialog.exec()
        self._refresh_quarantine_button()

    def purge_quarantine_clicked(self):
        """Trajno brisanje karantina — samo uz izricitu potvrdu korisnika."""
        files, total = self._quarantine_usage
        if not files:
            return
        answer = QMessageBox.question(
            self, self._t("app_title"),
            self._t("purge_confirm", n=files, gb=_gb(total)))
        if answer != QMessageBox.Yes:
            self._log(self._t("purge_cancelled"))
            return
        deleted, freed = purge_quarantine(self._ctx.quarantine_dir)
        self._log(self._t("quarantine_purged", n=deleted, gb=_gb(freed)))
        self._write_audit(False, 0, 0, 0, suffix="purge", steps=[
            {"action": "purge_quarantine", "phase": "done", "ok": True,
             "message": f"{deleted} fajlova, {_gb(freed)}"}])
        self.lbl_report.setText(
            self.lbl_report.text() + " " + self._t("report_freed", gb=_gb(freed)))
        self._refresh_quarantine_button()

    def undo_all(self):
        count = 0
        for action, state in reversed(self._undone):
            try:
                action.rollback(self._ctx, state)
                count += 1
                self._log(self._t("undo_one", a=action.name))
            except Exception as exc:
                self._log(self._t("undo_failed", a=action.name, e=exc))
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

    def closeEvent(self, event):
        """Sacekaj objasnjenje u toku; MujoFix ne drzi proces izmedju poziva."""
        if self._ai is not None and self._ai.isRunning():
            self._ai.wait(3000)
        self._session = None
        self._save_geometry()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    if hasattr(app, "setApplicationName"):
        app.setApplicationName("MujoFix")
    window = MainWindow(lang=stored_lang())
    window._restore_geometry()
    theme.setup(app, window)  # Fluent 2 + Segoe UI + Mica (best-effort)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
