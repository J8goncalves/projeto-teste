# V5 overlay installer. Preview by default, copies ONLY supplied files, backs up overwritten files.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Repository,
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path $PSScriptRoot).Path
$target = (Resolve-Path $Repository).Path
if ($source.TrimEnd('\') -eq $target.TrimEnd('\')) { throw 'O overlay deve ser extraído fora do repositório para prevenir sobreposição.' }
if (-not (Test-Path (Join-Path $target '.git'))) { throw 'A pasta indicada não contém .git; escolha a raiz correta do repositório.' }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path ([IO.Path]::GetTempPath()) "org-v5-backup-$stamp"
$files = Get-ChildItem -LiteralPath $source -File -Recurse | Where-Object {
    $_.FullName -notmatch '[\\/](?:__pycache__|\.git)[\\/]' -and
    $_.Name -notlike '*.pyc' -and $_.Name -notin @('apply_overlay.ps1', 'MANIFEST.sha256', 'test-results.txt')
}
Write-Host "Overlay: $source"
Write-Host "Repository: $target"
Write-Host "Arquivos no overlay: $($files.Count)"
if (-not $Apply) { Write-Host 'MODO SIMULAÇÃO: nenhum arquivo será alterado. Use -Apply após revisar o git status.' }
foreach ($file in $files) {
    $relative = $file.FullName.Substring($source.Length).TrimStart('\','/')
    $dest = Join-Path $target $relative
    $exists = Test-Path -LiteralPath $dest
    Write-Host ("{0} {1}" -f $(if ($exists) { 'REPLACE' } else { 'CREATE ' }), $relative)
    if ($Apply) {
        if ($exists) {
            $save = Join-Path $backup $relative
            $saveParent = Split-Path -Parent $save
            New-Item -Path $saveParent -ItemType Directory -Force | Out-Null
            Copy-Item -LiteralPath $dest -Destination $save -Force
        }
        $parent = Split-Path -Parent $dest
        New-Item -Path $parent -ItemType Directory -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
    }
}
if ($Apply) {
    Write-Host "ARQUIVOS COPIADOS. Backup de arquivos substituídos: $backup"
    Write-Host 'Execute: git status --short; python .agents/scripts/org_check.py; python -m unittest discover -s tests -v'
} else {
    Write-Host 'Revise a lista acima e execute novamente com -Apply para aplicar o overlay.'
}
