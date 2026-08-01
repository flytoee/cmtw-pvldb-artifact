$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$artifactDir = Split-Path -Parent $scriptDir
$manifest = Join-Path $artifactDir 'SHA256SUMS.txt'
$gitPrefix = (Join-Path $artifactDir '.git') + [System.IO.Path]::DirectorySeparatorChar

$lines = Get-ChildItem -LiteralPath $artifactDir -Recurse -File |
  Where-Object {
    -not $_.FullName.StartsWith($gitPrefix, [System.StringComparison]::OrdinalIgnoreCase) -and
    $_.FullName -ne $manifest
  } |
  ForEach-Object {
    $relative = $_.FullName.Substring($artifactDir.Length + 1).Replace('\', '/')
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
    "$hash  $relative"
  } |
  Sort-Object

[System.IO.File]::WriteAllLines($manifest, $lines, [System.Text.UTF8Encoding]::new($false))
Write-Output "Wrote $($lines.Count) entries to $manifest"
