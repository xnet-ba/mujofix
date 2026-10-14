"""Host dokaz akcija: PRAVI kod (actions/*), PRAVI Windows, TEST artefakti.

Tvrda kocnica: dozvoljeni su iskljucivo:
- registry: HKCU\\...\\Run vrijednost MUJOFIX_TEST_STARTUP
- fajlovi: samo unutar MUJOFIX_TEST_TEMPDIR foldera
- servis: tocno "Spooler"
Sve ostalo odbija bez izuzetka. Za svaku akciju: apply -> verify ->
rollback -> stanje identicno originalu. Exit 0 samo ako sve prodje.
"""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.actions.base import ActionContext, Runner
from mujofix.actions.service import RestartService
from mujofix.actions.startup import DisableStartupItem
from mujofix.actions.temp import CleanTemp
from mujofix.platform import windows

PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    results.append((name, PASS if cond else FAIL, detail))
    print(f"[{PASS if cond else FAIL}] {name} {detail}")
    return cond


def main() -> int:
    if not windows.is_windows():
        print("skipped: nije Windows")
        return 2
    with tempfile.TemporaryDirectory(prefix="mujofix-proof-") as qdir:
        ctx = ActionContext(quarantine_dir=qdir)
        runner = Runner()

        # 1. Startup stavka (vlastiti test value u HKCU Run).
        import winreg
        run_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_path,
                            0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "MUJOFIX_TEST_STARTUP", 0, winreg.REG_SZ,
                              r"C:\Windows\Temp\mujofix-test.exe")
        action = DisableStartupItem("HKCU", run_path, "MUJOFIX_TEST_STARTUP")
        assert action.needs_elevation is False
        result = runner.run(action, ctx)
        gone = "MUJOFIX_TEST_STARTUP" not in dict(_run_values(run_path))
        ok1 = check("startup.apply+verify", result.ok and result.verified and gone,
                    result.message)
        action.rollback(ctx, {"hive": "HKCU", "path": run_path,
                              "entry": "MUJOFIX_TEST_STARTUP",
                              "value": r"C:\Windows\Temp\mujofix-test.exe"})
        restored = dict(_run_values(run_path)).get("MUJOFIX_TEST_STARTUP") == \
            r"C:\Windows\Temp\mujofix-test.exe"
        ok1 &= check("startup.rollback-identican", restored)
        # pocisti test value (rollback ga je vratio, sad ga micemo zauvijek)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_path,
                            0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, "MUJOFIX_TEST_STARTUP")
            except FileNotFoundError:
                pass

        # 2. Temp (vlastiti folder + stari fajl).
        tdir = os.path.join(tempfile.gettempdir(), "MUJOFIX_TEST_TEMP")
        os.makedirs(tdir, exist_ok=True)
        victim = os.path.join(tdir, "old.tmp")
        with open(victim, "w") as handle:
            handle.write("podaci-host-proof")
        old = time.time() - 30 * 86400
        os.utime(victim, (old, old))
        action = CleanTemp(tdir, older_than_days=7)
        result = runner.run(action, ctx)
        ok2 = check("temp.apply+verify", result.ok and result.verified
                    and not os.path.exists(victim), result.message)
        action.rollback(ctx, result.state)
        try:
            with open(victim) as handle:
                content_ok = handle.read() == "podaci-host-proof"
        except OSError:
            content_ok = False
        ok2 &= check("temp.rollback-identican", content_ok)

        # 3. Spooler (restart, stanje se mora vratiti).
        from mujofix.actions import service as service_mod
        before = service_mod._state("Spooler")
        result = runner.run(RestartService("Spooler"), ctx)
        now = service_mod._state("Spooler")
        ok3 = check("service.restart", result.ok and result.verified
                    and now == "RUNNING", f"prije={before} poslije={now}")
        if before != "RUNNING":
            service_mod._sc("stop", "Spooler")
            check("service.rollback-identican",
                  service_mod._state("Spooler") == before)

    failed = [name for name, status, _ in results if status == FAIL]
    print(f"UKUPNO: {len(results) - len(failed)}/{len(results)} PASS")
    return 1 if failed else 0


def _run_values(path: str) -> dict:
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
        out, index = {}, 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, index)
            except OSError:
                break
            out[str(name)] = str(value)
            index += 1
    return out


if __name__ == "__main__":
    raise SystemExit(main())
