#Requires -Version 5.1
<#
.SYNOPSIS  MujoFix: skini, provjeri hash i pokreni validaciju NA OVOJ MASINI.
.DESCRIPTION
  Za pravi Windows 11 (fizicka masina) — bez VM-a, bez SSH-a, bez Dockera.
  Skida zvanicni release s GitHuba, PROVJERAVA SHA-256 protiv SHA256SUMS.txt,
  raspakuje portabilnu verziju i pokrene `scripts/vm_validate.ps1` (summary +
  JSON nalaza + provjera update-a). Rezultati idu na Desktop u
  `mujofix-rezultati/` — taj folder posalji nazad.

  Ova skripta NE MIJENJA sistem: samo skenira i prijavljuje. Nikakve popravke se
  ne primjenjuju (popravke se rade rucno u aplikaciji, uz tvoje odobrenje).

.PARAMETER Tag
  Release tag (npr. v0.4.0). Bez njega se koristi najnoviji release.

.PARAMETER Installer
  Umjesto portabilnog zip-a, skini i pokreni pravi installer (MujoFix-Setup-*.exe).
  OVO instalira aplikaciju u %LOCALAPPDATA%\MujoFix (bez admina); deinstalacija
  je kroz "Apps & features" i uklanja i podatke aplikacije.

.PARAMETER WorkDir
  Gdje se raspakuje portabilna verzija (default: %USERPROFILE%\mujofix-test).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File install-and-validate.ps1
  powershell -ExecutionPolicy Bypass -File install-and-validate.ps1 -Tag v0.4.0
  powershell -ExecutionPolicy Bypass -File install-and-validate.ps1 -Installer

.NOTES
  netestirano: skripta nije izvrsena u razvojnom okruzenju (nema PowerShell-a).
  Prvo pokretanje ide na pravoj masini; javi ishod.
#>
param(
  [string]$Tag = "",
  [switch]$Installer,
  [string]$WorkDir = (Join-Path $env:USERPROFILE "mujofix-test")
)

$ErrorActionPreference = "Stop"
$api = "https://api.github.com/repos/xnet-ba/mujofix/releases/latest"
$assetBase = "https://github.com/xnet-ba/mujofix/releases/download"

function Info($m) { Write-Host "[mujofix] $m" }
function Fail($m) { Write-Host "[mujofix][GRESKA] $m" -ForegroundColor Red; exit 1 }

# 1) release (jedan API poziv; -Tag bira konkretan, inace najnoviji)
$relApi = if ($Tag) { "https://api.github.com/repos/xnet-ba/mujofix/releases/tags/$Tag" } else { $api }
Info "Tražim release ..."
try {
  $rel = Invoke-RestMethod -Uri $relApi -Headers @{ "User-Agent" = "mujofix-validate" }
  $Tag = $rel.tag_name
  $names = @($rel.assets | ForEach-Object { $_.name })
} catch {
  Fail "Ne mogu da dohvatim release ($_). Provjeri ime taga ili internet."
}
Info "Release: $Tag"
$wantInstaller = $Installer
$asset = $null
foreach ($n in $names) {
  if ($wantInstaller -and $n -like "MujoFix-Setup-*.exe") { $asset = $n; break }
  if (-not $wantInstaller -and $n -like "MujoFix-v*.zip") { $asset = $n; break }
}
if (-not $asset) {
  if ($wantInstaller) { $asset = "MujoFix-Setup-$($Tag.TrimStart('v')).exe" }
  else { $asset = "MujoFix-$Tag.zip" }
  Info "Asset nije u listi release-a; pokušavam očekivano ime: $asset"
}
Info "Preuzimam: $asset"

New-Item -ItemType Directory $WorkDir -Force | Out-Null
$file = Join-Path $WorkDir $asset
Invoke-WebRequest -Uri "$assetBase/$Tag/$asset" -OutFile $file
$sumsFile = Join-Path $WorkDir "SHA256SUMS.txt"
Invoke-WebRequest -Uri "$assetBase/$Tag/SHA256SUMS.txt" -OutFile $sumsFile

# 3) FAIL CLOSED: hash se mora poklopiti (isto pravilo kao u aplikaciji)
$expected = (Select-String -Path $sumsFile -Pattern ([regex]::Escape($asset)) |
             Select-Object -First 1).Line
if (-not $expected) { Fail "SHA256SUMS.txt nema hash za $asset — prekidam." }
$expected = ($expected -split '\s+')[0].ToLower()
$actual = (Get-FileHash $file -Algorithm SHA256).Hash.ToLower()
if ($expected -ne $actual) { Fail "SHA-256 se NE poklapa! ocekivano=$expected dobijeno=$actual" }
Info "SHA-256 OK ($($actual.Substring(0,16))...)"

# 4) portabilno ili installer
if ($Installer) {
  Info "Pokrećem installer (bez admina, u korisnicki profil) ..."
  Start-Process -FilePath $file -ArgumentList "/SILENT" -Wait
  $exeDir = Join-Path $env:LOCALAPPDATA "MujoFix"
  Info "Instalirano u: $exeDir"
} else {
  $exeDir = Join-Path $WorkDir "app"
  Info "Raspakujem u: $exeDir"
  Expand-Archive $file $exeDir -Force
  $found = Get-ChildItem $exeDir -Recurse -Filter "MujoFixCLI.exe" -ErrorAction SilentlyContinue |
           Select-Object -First 1
  if ($found) { $exeDir = $found.DirectoryName }
}

# 5) validacija (summary + JSON + update provjera)
$validate = Join-Path $WorkDir "vm_validate.ps1"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/xnet-ba/mujofix/main/scripts/vm_validate.ps1" -OutFile $validate
Info "Pokrećem validaciju (samo čita, ništa ne mijenja) ..."
& $validate -ExeDir $exeDir

# 6) dodatni kontekst masine (bez izmjena) + uputstvo sta dalje
#    (isti folder u koji je vm_validate.ps1 pisao svoje rezultate)
$outDir = Join-Path ([Environment]::GetFolderPath("Desktop")) "mujofix-vm-rezultati"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory $outDir -Force | Out-Null }

$isAdmin = [bool](New-Object Security.Principal.WindowsPrincipal(
  [Security.Principal.WindowsIdentity]::GetCurrent())
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$ctxLog = Join-Path $outDir "06-masina.txt"
@(
  "== Masina ==",
  "Korisnik: $env:USERNAME",
  "Admin: $isAdmin",
  "Napomena: fizicka masina (ne VM)"
) | Out-File $ctxLog -Encoding utf8

# ZIP se pravi POSLIJE 06-masina.txt (da i taj fajl bude unutra)
$zipPath = "$outDir.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path $outDir -DestinationPath $zipPath -Force

$gui = Join-Path $exeDir "MujoFix.exe"
Write-Host ""
Write-Host "================= GOTOVO (automatski dio) =================" -ForegroundColor Green
Write-Host "Rezultati: $outDir"
Write-Host "ZIP za slanje: $zipPath"
Write-Host ""
Write-Host "SLJEDECE (rucno, ~5 minuta) — pokreni aplikaciju:" -ForegroundColor Cyan
Write-Host "  $gui"
Write-Host ""
Write-Host "  1) SCAN -> pogledaj sazetak: broj problema + koliko se moze popraviti"
Write-Host "  2) ukljuci 'Probni mod (nista se ne mijenja)' -> POPRAVI SVE"
Write-Host "     -> izvjestaj mora pisati 'Probni mod' (i nista se nije promijenilo)"
Write-Host "  3) iskljuci probni mod, oznaci JEDAN bezopasan nalaz (npr. privremeni fajlovi)"
Write-Host "     -> POPRAVI SVE -> provjeri: izvjestaj, dugme 'Karantin', pa 'Poništi sve' (mora vratiti)"
Write-Host "  4) ako aplikacija ponudi 'Pokreni kao administrator' (za nalaz koji to trazi),"
Write-Host "     klikni i PRIHVATI UAC — to je test elevacije; zapisi sta je pisalo PRIJE prompta"
Write-Host "  5) 'Jezik: English' -> zatvori i ponovo otvori aplikaciju -> provjeri da su"
Write-Host "     i NASLOVI NALAZA na engleskom (ne samo dugmadi)"
Write-Host "  6) (opciono) 'Objasni nalaze (AI)' -> ako model nije dostupan, mora ISKRENO pisati offline"
Write-Host ""
Write-Host "Slikaj (Win+Shift+S) i posalji:" -ForegroundColor Cyan
Write-Host "  - glavni prozor (svijetla tema) i isti prozor u tamnoj temi (Windows Settings -> Personalization -> Colors)"
Write-Host "  - ako je bilo UAC prompta: screenshot prompta"
Write-Host ""
Write-Host "Posalji mi: $zipPath  (+ screenshotove)" -ForegroundColor Yellow
if (Test-Path $gui) {
  $ans = Read-Host "Da otvorim aplikaciju sada? (d/n)"
  if ($ans -match '^[dDyY]') { Start-Process $gui }
}
