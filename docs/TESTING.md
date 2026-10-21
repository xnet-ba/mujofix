# TESTING.md — ručna test-lista (OPCIONA produzena validacija)

Status: faze 0–6 su vec potvrdjene *host-direct* na pravom Windows 11
(scan 9/9, 5/5 akcija s rollback-om, GUI smoke, spike 1–2). Ova lista je
zato OPCIONA: sluzi za punu matricu na CISTOM Win10 22H2 i Win11 23H2 VM-u
s namjerno pokvarenim stanjem, prije sireg javnog izdanja.

CI vrti samo mockovane unit testove; stavke ispod se rade rucno.
Rezultat se upisuje: PASS / FAIL + datum + build.
Automatizovani dio (scan, pin, live update provjera, sha256):
`scripts/vm_validate.ps1` (uz `-SetupExe` + `-SumsFile` za provjeru setup exe-a).

## A. Faza 0 SPIKE (`scripts/phase0_spike.py --model <zen-model>`)
- [ ] 1. Bundlovani OpenCode se pokreće bez Node-a (Win10 / Win11)
- [ ] 2. `opencode debug config` prihvata naš config (agent `mujofix`, 11 alata `deny`, samo naš MCP; 0 tuđih servera/pluginova)
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
- [ ] Instalater je na ENGLESKOM (Inno 6.7.1 nema Bosnian.isl — dokumentovano)
- [ ] `SHA256SUMS.txt` iz release-a: hash za `MujoFix-Setup-<ver>.exe` odgovara
      (`Get-FileHash ... -Algorithm SHA256`; provjeri i skriptom `-SetupExe`)

## G. Auto-update + elevacija (v0.2.0+)
- [ ] `MujoFixCLI.exe update` (bez `--apply`) ispiše "Nova verzija:" ili
      "je najnovija." i NE mijenja instalaciju
- [ ] `update --apply` na starijoj instalaciji: preuzme, provjeri sha256 i
      pokrene installer; verzija nakon toga = nova
- [ ] Pokvaren/prazan `SHA256SUMS.txt` → update se ODBIJA (nema tihe greške)
- [ ] Bez interneta: `update` vrati jasnu poruku i app radi dalje
- [ ] GUI: gumb "Provjeri ažuriranja" ne blokira prozor (radi u niti) i
      ispiše isti rezultat kao CLI
- [ ] UAC: akcija s `needs_elevation` se preskoči bez admina i NEMA lažnog
      "uspješno"; gumb "Pokreni kao administrator" tek tada traži UAC
- [ ] Nakon `runas` prompta i prihvatanja: akcija se izvrši; odbijanje UAC-a
      ostavlja stanje nepromijenjeno (bez pola-popravljenog sistema)
