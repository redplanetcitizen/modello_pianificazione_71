# prepara_ambiente.ps1 - crea l'ambiente Python, installa il pacchetto e verifica tutto.
# Uso, dalla cartella del repository:
#   powershell -ExecutionPolicy Bypass -File .\prepara_ambiente.ps1
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not (Test-Path .venv)) {
    Write-Host 'Creo l''ambiente .venv ...'
    python -m venv .venv
}
$py = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

& $py -m pip install --upgrade pip
& $py -m pip install -e ".[test]"
if ($LASTEXITCODE -ne 0) { throw 'Installazione non riuscita.' }
& $py -m pip freeze --exclude-editable | Out-File -Encoding utf8 requisiti-bloccati.txt

Write-Host ''
Write-Host '== Test automatici =='
& $py -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Test non superati.' }

Write-Host ''
Write-Host '== Verifica dei dati =='
& $py -m pianificazione71 verifica-dati
if ($LASTEXITCODE -ne 0) { throw 'Archivio non integro.' }

Write-Host ''
Write-Host '== Controllo del solver =='
& $py -m pianificazione71 controllo-solver
if ($LASTEXITCODE -ne 0) { throw 'Controllo del solver non superato.' }

Write-Host ''
Write-Host 'Ambiente pronto.'
