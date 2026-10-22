# AGENTS.md — pravila za AI kodera na MujoFix-u

- Stack: Python 3.11+, PySide6 (od Faze 3), PyInstaller + Inno Setup. Samo stdlib
  gdje god je moguce; bez novih zavisnosti bez potvrde.
- Installer: `installer/mujofix.iss` se kompajlira u CI (job `installer-windows`)
  na svakom push-u; `SourceDir=..` (repo root), `OutputDir=installer\Output`.
  Release dodaje `MujoFix-Setup-<ver>.exe`, a `SHA256SUMS.txt` mora biti
  `sha256sum` format (`<hash>  <ime>`) da bi ga `mujofix.update` verifikovao.
- Mali koraci: jedan modul/akcija po iteraciji, max ~5 fajlova odjednom.
  Poslije svakog koraka: `py_compile` + `unittest`, pa tek onda dalje.
- Potpun pokretljiv kod, bez pseudo-koda i bez TODO za kriticne dijelove.
- Oznake iskrenosti: `netestirano` za sve sto nije pokrenuto na Win10/Win11 VM-u;
  nista se ne tvrdi na osnovu pamcenja — samo docs + izvrsenje.
- Svaka akcija koja mijenja sistem: rizik + rollback() + test
  apply -> verify -> rollback -> identicno stanje. Bez rollback()-a nema auto-fixa.
- Zabranjeno: `--dangerously-skip-permissions`, `--auto`, `--share`, `--mdns`
  u bilo kojoj komandi; OpenCode proces nikad elevated.
- Akcije nad sistemom postoje samo kroz katalog + validator; AI samo objasnjava
  i predlaze. MCP alati nikad ne mijenjaju sistem.
- Elevacija: akcije s `needs_elevation` izvrsavaju se samo kad je proces vec
  admin (`windows.is_admin()`). Inace se preskacu; korisnik klikom bira
  "Pokreni kao administrator" (`windows.relaunch_elevated`, runas). Nikad
  auto-relaunch bez klika i nikad lazna tvrdnja da je popravka uspjela.
- Privatnost: anonimizacija se radi JEDNOM, na ulazu u `FallbackChain.explain`
  (`sanitize(compact_findings(...))`), nikad po provideru i nikad samo za log —
  poslano i logovano moraju biti isti payload. Novi provider ne smije sam
  graditi payload iz sirovih nalaza.
- Zivi AI: rucni lanci (`FallbackChain`) se ne prave u GUI kodu — koristi
  `ai/provider.build_chain` (offline bez pristanka, ziv Zen uz pristanak).
  MujoFix NEMA lokalni backend: nikad `opencode serve`, nikad port/lozinka,
  nista se ne izlaze na mrezu. Ziv poziv je `opencode run` kao child proces
  (jedan po zahtjevu, bez `--attach`/`--password`).
  `build_chain` MORA upisati izolirani `opencode.json`
  (`agent_config.write_config` + `mcp_command`); bez toga `run --agent mujofix`
  ne bi nasao agenta ni MCP alate. Agent MORA biti `mode: "all"` (ili
  `primary`): sa `subagent` `run --agent mujofix` tiho pada na default agent i
  zaobilazi zabranu alata. MCP server se pokrece kao `mujofix.cli mcp`
  (zamrznuto: `MujoFixCLI.exe mcp`) — GUI exe nema konzolu pa ne moze stdio.
  Radni dir nikad nije cwd: `default_ai_workdir()` (`%LOCALAPPDATA%\MujoFix\ai`).
  Child se pokrece sa env iz `agent_config.child_env(workdir)`
  (`XDG_CONFIG_HOME=<workdir>/config-home`, + PYTHONPATH u dev-u): bez toga se
  nas config stapa sa korisnickim globalnim (globalni MCP serveri + pluginovi u
  nasem agentu, dokazano protiv binarnog). Nikad ne diraj DATA dir — `auth.json`.
  Zabranjeni flagovi (`--attach`, `--port`, `--hostname`, `--auto`, `--share`,
  `--mdns`, `--dangerously-skip-permissions`) se provjeravaju u
  `OpenCodeProvider._cmd`; server se ne smije vratiti u projekat.
- Agent config (`agent_config.build_config`): samo **V1** oblik (`mcp` mapa,
  `agent`, `prompt`, `tools`). V2 oblik (`agents` + `permissions` lista) V1
  binarni odbija sa 400 (`ConfigInvalidError`) — tada pada cijeli zivi put.
  Svaka promjena configa: pokreni integracioni test u `test_phase0_spike.py`
  (`opencode debug config` sa izolovanim config-home: agent + `deny` + mcp).
  Imena alata samo iz
  `opencode agent create --help` pinovane verzije; izmisljena imena
  (`shell`, `write`, `patch`) tiho ne rade nista.
- Tvrdnje o privatnosti / AI uslovima (consent, README) samo iz primarnih
  izvora (ToS, docs) + datum provjere + link; nikad rijeci "privatno" bez
  dokaza. Dok se ne potvrdi: "NEPOTVRDJENO".
- Akcije: jedan modul po domeni (`temp.py`, `startup.py`, `service.py`, `env.py`,
  `proxy.py`); nalaz -> akcija mapira se u `actions/mapping.py` (bez Qt-a, da se
  testira bez PySide6). Novi nalaz bez rollback-a ostaje samo preporuka.
- Izgled: `mujofix/ui/theme.py` (Fluent 2 QSS + Segoe UI + Mica). Bez
  novih zavisnosti za UI; Mica samo preko `ctypes`/DWM i SAMO ako poziv
  uspije (van Windowsa i na starijem buildu -> False, solidna boja).
  Nikad ne tvrdi da je Mica aktivna ako nije. Novi widget: daj mu
  objectName i stil u theme.qss, ne inline `setStyleSheet`.
- Tekst akcija: poruke idu kroz `ctx.t("act_...")` (jezik iz
  `ActionContext.lang`), a `description`/`risk` preko `action_text(...)` —
  `tests/test_action_i18n.py` to provjerava (ratchet + bs/en paritet).
- Tekst nalaza u scannerima: nikad hardkodovan — `title`/`why`/`impact`/
  `risk` i `unavailable_reason` idu kroz `self.t("sc_...")` (jezik dolazi
  iz `ScanContext.lang`; `tests/test_scanner_i18n.py` to provjerava).
  Novi kljuc mora imati i bs i en vrijednost.
- UI tekst nikad hardkodovan: ide kroz `tr()`/`self._t()`, oba jezika
  (bs+en) — `tests/test_i18n.py` pada i na nepostojeci kljuc i na
  hardkodovan bosanski tekst u `mujofix/ui/`.
- Na kraju sesije azuriraj ovaj fajl i `docs/STATUS.md`.
