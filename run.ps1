param([ValidateSet('all','data','train','evaluate','test','api','demo')][string]$Stage='all')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$python=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $python)) { throw 'Najpierw: uv venv --python 3.13 .venv; uv pip install --python .venv/Scripts/python.exe -r requirements.txt' }
$env:PYTHONIOENCODING='utf-8'
switch ($Stage) {
 'test' { & $python -m pytest -q }
 'api' { & $python -m uvicorn api.app:app --host 127.0.0.1 --port 8000 }
 'demo' { & $python -m streamlit run app.py }
 default { & $python -m src.pipeline $Stage }
}
if ($LASTEXITCODE -ne 0) { throw "Polecenie zakończone kodem $LASTEXITCODE" }
