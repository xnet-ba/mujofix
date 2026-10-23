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

# 6) sta dalje
$outDir = Join-Path ([Environment]::GetFolderPath("Desktop")) "mujofix-vm-rezultati"
Info ""
Info "GOTOVO. Rezultati: $outDir"
Info "Pošalji mi taj folder (ili ga zapakuj: Compress-Archive '$outDir' '$outDir.zip')."
Info ""
Info "Rucno u aplikaciji (GUI) — kratka lista:"
Info "  1) pokreni MujoFix.exe iz: $exeDir"
Info "  2) SCAN -> provjeri sažetak (broj problema + koliko se može popraviti)"
Info "  3) uključi 'Probni mod (ništa se ne mijenja)' -> POPRAVI SVE -> report kaže 'Probni mod'"
Info "  4) isključi probni mod, odaberi JEDAN bezopasan nalaz (npr. privremeni fajlovi) -> POPRAVI SVE"
Info "     pa provjeri: izvještaj, dugme 'Karantin', i 'Poništi sve' (mora vratiti)"
Info "  5) 'Jezik: English' -> restart -> provjeri da su i NALAZI na engleskom"
Info "  6) screenshot (svijetla + tamna tema) i kratak opis UAC prompta ako se pojavio"
