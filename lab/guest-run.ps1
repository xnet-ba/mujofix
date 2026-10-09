#Requires -Version 5.1
<#
.SYNOPSIS  MujoFix lab korak UNUTAR Win11 gosta (MujoWinPC / bilo koji VM).
.DESCRIPTION
  Skida alpha build + vm_validate.ps1 s GitHuba i pokrece validaciju.
  U gostu je dovoljan internet; Python/admin nisu potrebni.
  Pokretanje u gostujucoj PowerShell konzoli (zalijepi cijeli red):
    powershell -ExecutionPolicy Bypass -File \\putanja\\guest-run.ps1
  ili preuzmi fajl RDP-om / browserom pa pokreni lokalno.
#>
param(
  [string]$Tag = "v0.1.0-alpha.1",
  [string]$WorkDir = (Join-Path $env:TEMP "mujofix-lab")
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory $WorkDir -Force | Out-Null

$zipUrl = "https://github.com/xnet-ba/mujofix/releases/download/$Tag/MujoFix-windows-alpha.1.zip"
$zip = Join-Path $WorkDir "alpha.zip"
Write-Host "Skidam $zipUrl ..."
Invoke-WebRequest -Uri $zipUrl -OutFile $zip

$validateUrl = "https://raw.githubusercontent.com/xnet-ba/mujofix/main/scripts/vm_validate.ps1"
$validate = Join-Path $WorkDir "vm_validate.ps1"
Write-Host "Skidam vm_validate.ps1 ..."
Invoke-WebRequest -Uri $validateUrl -OutFile $validate

Expand-Archive $zip (Join-Path $WorkDir "app") -Force
& $validate -ExeDir (Join-Path $WorkDir "app\MujoFix")
