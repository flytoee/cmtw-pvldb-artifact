$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$artifactDir = Split-Path -Parent $scriptDir
$manifest = Join-Path $artifactDir 'SHA256SUMS.txt'
$tracked = & git -C $artifactDir ls-files
if ($LASTEXITCODE -ne 0) {
  throw 'Could not enumerate tracked artifact files.'
}

$lines = $tracked |
  Where-Object { $_ -ne 'SHA256SUMS.txt' } |
  ForEach-Object {
    $relative = $_.Replace('\', '/')
    $path = Join-Path $artifactDir ($relative.Replace('/', '\'))
    if (-not (Test-Path -LiteralPath $path)) {
      throw "Tracked artifact file is missing: $relative"
    }
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    "$hash  $relative"
  } |
  Sort-Object

[System.IO.File]::WriteAllLines($manifest, $lines, [System.Text.UTF8Encoding]::new($false))
Write-Output "Wrote $($lines.Count) entries to $manifest"
