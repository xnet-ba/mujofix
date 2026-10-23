#Requires -Version 5.1
<#
.SYNOPSIS  MujoFix lab korak (VM gost ILI prava Windows masina).
.DESCRIPTION
  Zamjena za staru verziju koja je skidala `MujoFix-windows-alpha.1.zip` iz taga
  `v0.1.0-alpha.1` — taj asset vise ne postoji, pa je stara skripta pucala.

  Sada samo pokrece `scripts/install-and-validate.ps1` s `main` grane, koji:
  skine zvanicni release, PROVJERI SHA-256 protiv SHA256SUMS.txt, raspakuje
  portabilnu verziju (bez admina) i pokrene validaciju. Rezultati idu na Desktop
  u `mujofix-vm-rezultati/`.

  Pokretanje (gost ili host PowerShell, zalijepi jedan red):
    powershell -ExecutionPolicy Bypass -File guest-run.ps1
    powershell -ExecutionPolicy Bypass -File guest-run.ps1 -Tag v0.4.0
    powershell -ExecutionPolicy Bypass -File guest-run.ps1 -Installer
#>
param(
  [string]$Tag = "",
  [switch]$Installer,
  [string]$WorkDir = (Join-Path $env:USERPROFILE "mujofix-test")
)

$ErrorActionPreference = "Stop"
$url = "https://raw.githubusercontent.com/xnet-ba/mujofix/main/scripts/install-and-validate.ps1"
$script = Join-Path $env:TEMP "mujofix-install-and-validate.ps1"
Write-Host "[mujofix] Skidam $url ..."
Invoke-WebRequest -Uri $url -OutFile $script

$args = @{ WorkDir = $WorkDir }
if ($Tag) { $args.Tag = $Tag }
if ($Installer) { $args.Installer = $true }
& $script @args
