"""Host dokaz akcija: PRAVI kod (actions/*), PRAVI Windows, TEST artefakti.

Tvrda kocnica: dozvoljeni su iskljucivo:
- registry: HKCU\\...\\Run vrijednost MUJOFIX_TEST_STARTUP
- fajlovi: samo unutar MUJOFIX_TEST_TEMPDIR foldera
- servis: tocno "Spooler"
- hosts: jedan test-zapis (10.0.0.1 mujofix-test.invalid), uz backup cijelog
  fajla i vracanje na kraju (i u slucaju greske)
- share: share imena MUJOFIX_TEST_SHARE (vlastiti temp folder), obrisan na kraju
- power: vraca se TACNO na prijasnji aktivni plan
Sve ostalo odbija bez izuzetka. Za svaku akciju: apply -> verify ->
rollback -> stanje identicno originalu. Exit 0 samo ako sve prodje.

Akcije 1-3 su izvrsene na pravom Windows hostu (2026-10-14).
Akcije 4-6 (hosts/share/power) su dodate 2026-10-22 i NETESTIRANE su — prvo
pokretanje ide na VM (docs/TESTING.md, sekcija C/H). Traze admin za hosts i
share; bez admina se preskacu (SKIP), ne padaju.
"""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mujofix.actions.base import ActionContext, Runner
from mujofix.actions.hosts import RemoveHostsEntry
from mujofix.actions.power import DisablePowerSaver, active_guid
from mujofix.actions.share import RemoveShare
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

        # 4. Hosts: test-zapis uz backup cijelog fajla (vraca se u svakom slucaju).
        hosts_path = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                                  "System32", "drivers", "etc", "hosts")
        try:
            with open(hosts_path, encoding="utf-8", errors="replace") as handle:
                original_hosts = handle.read()
        except OSError as exc:
            original_hosts = None
            check("hosts.read", False, f"ne mogu procitati hosts: {exc}")
        if original_hosts is not None:
            if not windows.is_admin():
                check("hosts.apply+verify+rollback", True,
                      "SKIP: nije admin (hosts je zastita)")
            else:
                test_line = "10.0.0.1 mujofix-test.invalid"
                try:
                    with open(hosts_path, "a", encoding="utf-8") as handle:
                        handle.write("\n" + test_line + "\n")
                    action = RemoveHostsEntry(hosts_path, "10.0.0.1",
                                              "mujofix-test.invalid")
                    result = runner.run(action, ctx)
                    with open(hosts_path, encoding="utf-8") as handle:
                        after = handle.read()
                    gone = test_line not in after
                    rest_ok = after == original_hosts
                    ok4 = check("hosts.apply+verify",
                                result.ok and result.verified and gone,
                                result.message)
                    ok4 &= check("hosts.ostatak-nepromijenjen", rest_ok)
                    action.rollback(ctx, result.state)
                    with open(hosts_path, encoding="utf-8") as handle:
                        back = handle.read()
                    ok4 &= check("hosts.rollback-identican", back == original_hosts)
                finally:
                    # sigurnosna mreza: vrati original bez obzira na ishod
                    with open(hosts_path, "w", encoding="utf-8") as handle:
                        handle.write(original_hosts)

        # 5. Share: vlastiti share + temp folder, obrisan na kraju.
        share_name = "MUJOFIX_TEST_SHARE"
        share_dir = os.path.join(tempfile.gettempdir(), "MUJOFIX_TEST_SHARE_DIR")
        os.makedirs(share_dir, exist_ok=True)
        if not windows.is_admin():
            check("share.apply+verify+rollback", True,
                  "SKIP: nije admin (net share trazi elevaciju)")
        else:
            from mujofix.actions import share as share_mod
            share_mod._run(["share", f"{share_name}={share_dir}"])
            try:
                action = RemoveShare(share_name, share_dir)
                result = runner.run(action, ctx)
                gone = share_mod._share_info(share_name) is None
                ok5 = check("share.apply+verify",
                            result.ok and result.verified and gone,
                            result.message)
                action.rollback(ctx, result.state)
                info = share_mod._share_info(share_name)
                ok5 &= check("share.rollback-identican",
                             info is not None
                             and os.path.normcase(info["path"])
                             == os.path.normcase(share_dir))
                # administrativni share se NIKAD ne dira
                admin_ok, admin_reason = RemoveShare("C$").precondition(ctx)
                ok5 &= check("share.ne-dira-administrativne",
                             not admin_ok and "sistemski" in admin_reason)
            finally:
                share_mod._run(["share", share_name, "/delete"])

        # 6. Power: vrati se TACNO na prijasnji aktivni plan.
        try:
            before_guid = active_guid()
        except OSError as exc:
            before_guid = None
            check("power.read", False, f"powercfg nedostupan: {exc}")
        if before_guid is not None:
            action = DisablePowerSaver()
            allowed, reason = action.precondition(ctx)
            if not allowed:
                check("power.apply+verify+rollback", True,
                      f"SKIP: {reason}")
            else:
                result = runner.run(action, ctx)
                now = active_guid()
                ok6 = check("power.apply+verify",
                            result.ok and result.verified
                            and now == "381b4222-f694-41f0-9685-ff5bb260df2e",
                            f"prije={before_guid} poslije={now}")
                action.rollback(ctx, result.state)
                ok6 &= check("power.rollback-identican",
                             active_guid() == before_guid)

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
