#Requires -Version 5.1
<#
.SYNOPSIS  MujoFix VM validacija iznutra (MujoWinPC Win10/11 kontejner ili bilo koji VM).
.DESCRIPTION
  Pokrece bundlovani MujoFixCLI.exe: summary + masinski JSON + findings za MCP.
  Ne trazi Python ni admina. Rezultate (mujofix-vm-rezultati/) kopiraj van VM-a
  i priloziti uz Issue #1. Rucne stavke (UAC prompt, GUI screenshot) su u
  docs/TESTING.md i rade se ocima.
#>
param(
  [string]$ExeDir = (Join-Path $env:LOCALAPPDATA "MujoFix"),
  [string]$OutDir = (Join-Path ([Environment]::GetFolderPath("Desktop")) "mujofix-vm-rezultati")
)

$ErrorActionPreference = "Stop"
$cli = Join-Path $ExeDir "MujoFixCLI.exe"
if (-not (Test-Path $cli)) {
  # fallback: raspakovani alpha zip na Desktopu
  $cand = Get-ChildItem ([Environment]::GetFolderPath("Desktop")) -Recurse -Filter MujoFixCLI.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($cand) { $cli = $cand.FullName } else { throw "Nema MujoFixCLI.exe (ocekivano: $cli)" }
}

New-Item -ItemType Directory $OutDir -Force | Out-Null
"== 1/3 Windows verzija ==" | Tee-Object (Join-Path $OutDir "00-winver.txt")
systeminfo | Select-String "OS Name", "OS Version" | Tee-Object -Append (Join-Path $OutDir "00-winver.txt")

"== 2/3 CLI scan (summary) ==" | Tee-Object (Join-Path $OutDir "01-summary.txt")
& $cli scan --summary | Tee-Object -Append (Join-Path $OutDir "01-summary.txt")
if ($LASTEXITCODE -ne 0) { throw "scan --summary pao (exit $LASTEXITCODE)" }

"== 3/3 CLI scan (JSON + findings za MCP) ==" | Tee-Object (Join-Path $OutDir "02-json.txt")
& $cli scan --out (Join-Path $OutDir "findings.json") | Tee-Object -Append (Join-Path $OutDir "02-json.txt")
if ($LASTEXITCODE -ne 0) { throw "scan --out pao (exit $LASTEXITCODE)" }

"GOTOVO. Folder '$OutDir' kopiraj van VM-a (findings.json je masinski dokaz)."
"Rucno jos: UAC prompt tok, GUI screenshot 1080p + tamni rezim (docs/TESTING.md E)."
