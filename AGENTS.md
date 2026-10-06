# AGENTS.md — pravila za AI kodera na MujoFix-u

- Stack: Python 3.11+, PySide6 (od Faze 3), PyInstaller + Inno Setup. Samo stdlib
  gdje god je moguce; bez novih zavisnosti bez potvrde.
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
- Na kraju sesije azuriraj ovaj fajl i `docs/STATUS.md`.
