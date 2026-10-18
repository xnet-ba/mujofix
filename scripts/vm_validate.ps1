#Requires -Version 5.1
<#
.SYNOPSIS  MujoFix VM validacija iznutra (MujoWinPC Win10/11 kontejner ili bilo koji VM).
.DESCRIPTION
  Pokrece bundlovani MujoFixCLI.exe: summary + masinski JSON + live auto-update
  provjera. Ne trazi Python ni admina. Rezultate (mujofix-vm-rezultati/) kopiraj
  van VM-a i priloziti uz Issue #1.
  Rucne stavke (UAC prompt, GUI screenshot) su u docs/TESTING.md i rade se ocima.
.PARAMETER ApplyUpdate
  OPCIONO i mijenja instalaciju: pokrece `update --apply` (preuzme novi release,
  provjeri sha256 i pokrene installer). Bez ovog prekidaca se samo provjerava.
.PARAMETER SetupExe
  OPCIONO: putanja do MujoFix-Setup-*.exe za nezavisnu provjeru sha256.
.PARAMETER SumsFile
  Uz -SetupExe: putanja do SHA256SUMS.txt (isti release).
.NOTES
  netestirano: skripta nije pokrenuta (u razvojnom okruzenju nema PowerShell-a).
#>
param(
  [string]$ExeDir = (Join-Path $env:LOCALAPPDATA "MujoFix"),
  [string]$OutDir = (Join-Path ([Environment]::GetFolderPath("Desktop")) "mujofix-vm-rezultati"),
  [switch]$ApplyUpdate,
  [string]$SetupExe,
  [string]$SumsFile
)

$ErrorActionPreference = "Stop"
$cli = Join-Path $ExeDir "MujoFixCLI.exe"
if (-not (Test-Path $cli)) {
  # fallback: raspakovani alpha zip na Desktopu
  $cand = Get-ChildItem ([Environment]::GetFolderPath("Desktop")) -Recurse -Filter MujoFixCLI.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($cand) { $cli = $cand.FullName } else { throw "Nema MujoFixCLI.exe (ocekivano: $cli)" }
}

New-Item -ItemType Directory $OutDir -Force | Out-Null
$winLog = Join-Path $OutDir "00-winver.txt"
$sumLog = Join-Path $OutDir "01-summary.txt"
$jsonLog = Join-Path $OutDir "02-json.txt"
$updLog = Join-Path $OutDir "03-update.txt"
$shaLog = Join-Path $OutDir "04-sha256.txt"
$ocvLog = Join-Path $OutDir "05-opencode.txt"

"== 1/6 Windows verzija ==" | Tee-Object $winLog
systeminfo | Select-String "OS Name", "OS Version" | Tee-Object -Append $winLog

"== 2/6 CLI scan (summary) ==" | Tee-Object $sumLog
& $cli scan --summary | Tee-Object -Append $sumLog
if ($LASTEXITCODE -ne 0) { throw "scan --summary pao (exit $LASTEXITCODE)" }

"== 3/6 CLI scan (JSON + findings za MCP) ==" | Tee-Object $jsonLog
& $cli scan --out (Join-Path $OutDir "findings.json") | Tee-Object -Append $jsonLog
if ($LASTEXITCODE -ne 0) { throw "scan --out pao (exit $LASTEXITCODE)" }

# --- v0.2.0+: bundlovani opencode + pin (F/PIN) ---
"== 4/6 Bundlovani opencode + pin ==" | Tee-Object $ocvLog
$ocDir = Join-Path $ExeDir "opencode"
$ocBin = Join-Path $ocDir "opencode.exe"
if (Test-Path $ocBin) {
  & $ocBin --version 2>&1 | Tee-Object -Append $ocvLog
} else {
  "NEMA opencode.exe u $ocDir" | Tee-Object -Append $ocvLog
}
$pin = Join-Path $ExeDir "OPENCODE_PIN.txt"
if (Test-Path $pin) { (Get-Content $pin -Raw).Trim() | Tee-Object -Append $ocvLog }
else { "NEMA OPENCODE_PIN.txt u $ExeDir" | Tee-Object -Append $ocvLog }

# --- v0.2.0+: live auto-update provjera (samo cita GitHub Releases) ---
"== 5/6 Auto-update provjera (live) ==" | Tee-Object $updLog
$upd = & $cli update 2>&1 | Tee-Object -Append $updLog
$updExit = $LASTEXITCODE
$updText = ($upd | Out-String)
if ($updExit -ne 0) {
  ("UPOZORENJE: 'update' exit $updExit (mreza ili GitHub rate limit). "
   + "Ponovi sa internetskom vezom.") | Tee-Object -Append $updLog
} elseif ($updText -match "je najnovija" -or $updText -match "Nova verzija:") {
  "OK: ispis update-a u ocekivanom formatu." | Tee-Object -Append $updLog
} else {
  "UPOZORENJE: neocekivan ispis update-a — pogledaj 03-update.txt." | Tee-Object -Append $updLog
}

if ($ApplyUpdate) {
  "== update --apply (OPCIONO: mijenja instalaciju) ==" | Tee-Object -Append $updLog
  & $cli update --apply 2>&1 | Tee-Object -Append $updLog
  "exit --apply: $LASTEXITCODE" | Tee-Object -Append $updLog
}

# --- OPCIONO: nezavisna provjera sha256 setup exe-a ---
if ($SetupExe) {
  if (-not $SumsFile -or -not (Test-Path $SumsFile)) {
    throw "Za -SetupExe treba -SumsFile (SHA256SUMS.txt iz istog release-a)."
  }
  $name = Split-Path $SetupExe -Leaf
  $want = Get-Content $SumsFile | Where-Object {
    $_ -match ([regex]::Escape($name) + "\s*$") } | Select-Object -First 1
  if (-not $want) { throw "Nema '$name' u SHA256SUMS.txt" }
  $wantHash = ($want -split "\s+")[0].ToLower()
  $gotHash = (Get-FileHash $SetupExe -Algorithm SHA256).Hash.ToLower()
  if ($wantHash -ne $gotHash) { throw "SHA256 NE odgovara za $name" }
  "SHA256 OK: $name = $gotHash" | Tee-Object $shaLog
} else {
  "Preskoceno: sha256 provjera (daj -SetupExe + -SumsFile)." | Tee-Object $shaLog
}

"== 6/6 GOTOVO =="
"Folder '$OutDir' kopiraj van VM-a (findings.json je masinski dokaz)."
"Rucno jos: UAC prompt tok + gumb 'Pokreni kao administrator', auto-update iz GUI-a,"
"GUI screenshot 1080p + tamni rezim (docs/TESTING.md E i G)."
