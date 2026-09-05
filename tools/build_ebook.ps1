# build_ebook.ps1 -- produce EPUB/HTML editions of "Mastering APIs"
# Requires: MiKTeX/TeX Live (latexpand) and pandoc on PATH.
#
# Usage (from the book root):
#   powershell -File tools\build_ebook.ps1            # EPUB + HTML into build\
#   powershell -File tools\build_ebook.ps1 -Format epub
#
# NOTE: Pandoc's LaTeX reader cannot execute TikZ/pgfplots, so diagrams are
# omitted from the EPUB/HTML editions (their captions remain). The PDF built
# from main.tex remains the canonical, fully-illustrated edition.
param(
    [ValidateSet('epub', 'html', 'both')] [string]$Format = 'both'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
New-Item -ItemType Directory -Force -Path build | Out-Null

Write-Host '==> Flattening LaTeX (tools\flatten_latex.py)'
python tools\flatten_latex.py main.tex build\book_flat.tex
if ($LASTEXITCODE -ne 0) { throw 'latex flattening failed' }

$common = @(
    'build\book_flat.tex',
    '--from', 'latex',
    '--toc', '--toc-depth=2',
    '--metadata', 'title=Mastering APIs: From Zero to Production Guru',
    '--metadata', 'author=API Engineering Education Team',
    '--metadata', 'lang=en'
)

if ($Format -in 'epub', 'both') {
    Write-Host '==> Building EPUB'
    pandoc @common -o build\mastering-apis.epub
    if ($LASTEXITCODE -ne 0) { throw 'pandoc epub failed' }
}
if ($Format -in 'html', 'both') {
    Write-Host '==> Building HTML'
    pandoc @common --standalone --mathjax -o build\mastering-apis.html
    if ($LASTEXITCODE -ne 0) { throw 'pandoc html failed' }
}

Get-ChildItem build\mastering-apis.* | ForEach-Object {
    '{0}  {1:N1} MB' -f $_.Name, ($_.Length / 1MB)
}
