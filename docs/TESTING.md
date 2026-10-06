# TESTING.md — ručna test-lista (CI ovo NE može: treba pravi Win10/Win11 VM)

CI vrti samo mockovane unit testove. Sve ispod se radi ručno na ČISTOM
Win10 22H2 i ČISTOM Win11 23H2 VM-u, s namjerno pokvarenim stanjem
(pun temp, suvišan startup, zaustavljen Spooler, pokvaren DNS).
Rezultat se upisuje: PASS / FAIL + datum + build.

## A. Faza 0 SPIKE (`scripts/phase0_spike.py --model <zen-model>`)
- [ ] 1. Bundlovani OpenCode se pokreće bez Node-a (Win10 / Win11)
- [ ] 2. `serve` sluša samo 127.0.0.1 i traži lozinku
- [ ] 3. Agent `mujofix` pozove MCP alat s lažnim podacima
- [ ] 4. Pokušaj `shell` poziva je odbijen (dokaz u logu)
- [ ] 5. Offline fallback radi s ugašenim internetom

## B. Scanneri uživo (`MujoFixCLI.exe scan`)
- [ ] startup nalazi Run stavku dodanu ručno u HKCU
- [ ] disk prijavi temp > 2 GB; Windows.old prepoznat ako postoji
- [ ] services prijavi zaustavljeni automatski servis (zaustavi Spooler)
- [ ] network: DNS kvar (loš DNS u adapteru) = CRITICAL; hosts hijack test-zapis
- [ ] config: mrtva PATH stavka; power saver plan
- [ ] drivers: prolazi bez rušenja (broj drajvera zabilježiti)
- [ ] duplicates: kopija 50 MB fajla na 2 mjesta = 1 grupa, certain
- [ ] suspicious: kopiraj potpisani exe u %TEMP% + Run stavka = sumnjiv
- [ ] permissions: EnableLUA=0 na test VM-u = CRITICAL (vratiti na 1!)

## C. Akcije uživo (SVAKA: apply → verify → rollback → identično stanje)
- [ ] disable_startup_item na test stavci (HKCU, bez UAC)
- [ ] clean_temp na test folderu (fajl stariji od 7 dana, sadržaj identičan nakon rollback-a)
- [ ] restart_service na Spooleru (treba UAC prompt + objašnjenje prije)
- [ ] "Poništi sve" iz GUI-a vraća sve tri promjene

## D. AI sloj uživo
- [ ] Ekran pristanka se pokaže prije prvog AI poziva; "Ostajem offline" radi
- [ ] "Pogledaj tačno šta je poslano" ne sadrži ime/IP/hostname
- [ ] Nevalidan JSON / nedostupan model → fallback lanac → offline, app radi
- [ ] Validator odbija: nepoznata akcija, System32 meta, >20 koraka

## E. GUI na Win11
- [ ] Screenshot 1080p + 4K DPI 150%: čitljivo, ništa odsječeno
- [ ] Tamni režim Windowsa; samo tastatura (Tab redoslijed)
- [ ] UAC prompt se pojavi TEK uz prethodno objašnjenje u aplikaciji

## F. Installer
- [ ] Instalacija bez admina radi (korisnički profil)
- [ ] OpenCode kopija u %LOCALAPPDATA%\MujoFix\opencode, verzija = pin
- [ ] Deinstalacija uklanja sve (opencode kopija + podaci)
- [ ] Build NIJE potpisan → SmartScreen upozorenje je očekivano, ne bug
