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
- Zivi AI: rucni lanci (`FallbackChain`) se ne prave u GUI kodu — koristi
  `ai/provider.build_chain` (offline bez pristanka, ziv Zen uz pristanak).
  `build_chain` MORA upisati izolirani `opencode.json` prije starta servera
  (`agent_config.write_config` + `mcp_command`); bez toga server nema agenta
  `mujofix` ni MCP alate. Agent MORA biti `mode: "all"` (ili `primary`): sa
  `subagent` `run --agent mujofix` tiho pada na default agent i zaobilazi
  zabranu alata. MCP server se pokrece kao `mujofix.cli mcp`
  (zamrznuto: `MujoFixCLI.exe mcp`) — GUI exe nema konzolu pa ne moze stdio.
  Radni dir za server nikad nije cwd: `default_ai_workdir()`
  (`%LOCALAPPDATA%\MujoFix\ai`).
  Sesiju (`LiveSession`) drzi GUI i UVEK je zatvori na `closeEvent`; nikad ne
  ostavljaj `opencode serve` kao zaostali proces.
- Agent config (`agent_config.build_config`): samo **V1** oblik (`mcp` mapa,
  `agent`, `prompt`, `tools`). V2 oblik (`agents` + `permissions` lista) V1
  binarni odbija sa 400 (`ConfigInvalidError`) — tada pada cijeli zivi put.
  Svaka promjena configa: pokreni integracioni test u `test_phase0_spike.py`
  (digne stvarni `opencode serve` i trazi 200 + deny). Imena alata samo iz
  `opencode agent create --help` pinovane verzije; izmisljena imena
  (`shell`, `write`, `patch`) tiho ne rade nista.
- Tvrdnje o privatnosti / AI uslovima (consent, README) samo iz primarnih
  izvora (ToS, docs) + datum provjere + link; nikad rijeci "privatno" bez
  dokaza. Dok se ne potvrdi: "NEPOTVRDJENO".
- Akcije: jedan modul po domeni (`temp.py`, `startup.py`, `service.py`, `env.py`,
  `proxy.py`); nalaz -> akcija mapira se u `actions/mapping.py` (bez Qt-a, da se
  testira bez PySide6). Novi nalaz bez rollback-a ostaje samo preporuka.
- Na kraju sesije azuriraj ovaj fajl i `docs/STATUS.md`.
