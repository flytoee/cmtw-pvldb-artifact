param(
  [string]$OutputPath
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$artifactDir = Split-Path -Parent $scriptDir
$htmlPath = Join-Path $scriptDir 'fig4_submission.html'
if (-not $OutputPath) {
  $OutputPath = Join-Path $artifactDir 'reproduced\paper-figures\cmtw-v19-fig4-lifecycle-correctness.pdf'
}
$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
$outputDir = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

$browserCandidates = @(
  'C:\Program Files\Google\Chrome\Application\chrome.exe',
  'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
  'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
  'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
)
$browser = $browserCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $browser) {
  throw 'Chrome or Edge was not found in a standard installation path.'
}

if (Test-Path -LiteralPath $OutputPath) {
  Remove-Item -LiteralPath $OutputPath
}
$uri = 'file:///' + (($htmlPath -replace '\\', '/') -replace ' ', '%20')
& $browser --headless=new --disable-gpu --no-pdf-header-footer "--print-to-pdf=$OutputPath" $uri | Out-Null

$deadline = (Get-Date).AddSeconds(30)
do {
  Start-Sleep -Milliseconds 200
  $ready = (Test-Path -LiteralPath $OutputPath) -and ((Get-Item -LiteralPath $OutputPath).Length -gt 0)
} until ($ready -or (Get-Date) -gt $deadline)
if (-not $ready) {
  throw "Timed out while rendering $OutputPath"
}

$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $OutputPath).Hash
Write-Output "Rendered Figure 4: $OutputPath"
Write-Output "SHA-256: $hash"
