# RYZEN-LAB.md — KVM lab za MujoFix na Ryzen laptopu (MujoWinPC + Win11)

Cilj: ponovljiva Windows validacija (Issue #1, docs/TESTING.md A–F).
Dvije uloge: **host korake** moze voziti agent preko SSH-a, **gost korak**
je jedno lijepljenje u PowerShell unutar Win11 (5 minuta).

## A. Host priprema (jednokratno, na Ryzen laptopu)

```bash
git clone git@github.com:xnet-ba/MujoWinPC.git && cd MujoWinPC
cp .env.example .env   # upisi jaku WINDOWS_PASSWORD (20+ znakova)
./scripts/mujowin doctor        # mora proci; bez /dev/kvm stani (TROUBLESHOOTING)
./scripts/mujowin up            # WIN=11 default; prvi boot skida image, ostavi da radi
```

Provjera: noVNC na portu 8006 → Windows setup → desktop → prijava podacima iz `.env`.

## B. Cista snapshot tacka (prije svakog test ciklusa)

```bash
./scripts/mujowin backup    # prvi backup dok je sve svjeze; rotacija ugradjena
```

Poslije destruktivnih testova (akcije C-grupe): restore na ovaj backup,
pa ponovi. Bez restore-a rezultati rollback testova ne vrijede.

## C. Gost korak (unutar Win11: PowerShell)

```powershell
# najlakse: Edge u VM-u otvori raw URL lab/guest-run.ps1, sacuvaj na Desktop,
# desni klik -> Run with PowerShell. Ili zalijepi preko RDP clipboarda.
powershell -ExecutionPolicy Bypass -File "$HOME\Desktop\guest-run.ps1"
```

Skripta sama skida alpha build s GitHub Releases, raspakuje, pokrene
`vm_validate.ps1` (summary + JSON + findings) i slozi rezultate na Desktop
u `mujofix-vm-rezultati/`.

## D. Rezultati van VM-a

- RDP (port 3389, pali samo kad treba): kopiraj `mujofix-vm-rezultati/`
  na host (drive redirection) → zakaciti `findings.json` na Issue #1.
- GUI stavke (E-grupa): screenshot 1080p + 4K/150% + tamni rezim, preko
  noVNC/RDP; UAC prompt tok opisati rijecima (sta je pisalo prije prompta).
- Namjerno pokvareno stanje za B-grupu: pun temp (`fsutil file createnew`
  veliki fajlovi u %TEMP%), suvisna Run stavka u HKCU, zaustavljen Spooler,
  los DNS u adapteru — svaku stavku testirati izmedju restore-a.

## E. Agent SSH pristup (da ja vozim host korake)

Treba mi: SSH nalog na Ryzen laptopu (ili WSL2) s pravom na docker,
mosj SSH kljuc `mujofix-agent` dodan u `~/.ssh/authorized_keys`,
i mreza do porta 22 (LAN / Tailscale / ZeroTier — sta god je vec podeseno).
Sta onda radim sam: `up/down/backup/restore/logs/status`, analiza
`findings.json` s hosta, commit/popravke ovdje. Gost korak (C) i dalje
radi covjek — ja nemam prste za RDP.
