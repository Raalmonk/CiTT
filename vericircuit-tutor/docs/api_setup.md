# Gemini API Setup

VeriCircuit Tutor works without external API keys. In that mode, the deterministic demo parser handles the bundled examples. Gemini mode is optional and is only used to produce CircuitProblem JSON. It must not produce final numerical answers.

## Get A Key

Create an API key in Google AI Studio, then set it as a server-side environment variable before starting FastAPI. Never commit API keys. Never paste real API keys into chat or GitHub. Revoke keys if exposed.

## Windows PowerShell

From the project backend directory:

```powershell
cd vericircuit-tutor\backend
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
```

Set environment variables for the current PowerShell session:

```powershell
$env:GEMINI_API_KEY = "your_key_here"
$env:GEMINI_MODEL = "gemini-3.5-flash"
```

Run the app:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

You may also use `GOOGLE_API_KEY` instead of `GEMINI_API_KEY`.

To run strict Gemini mode manually, choose "Gemini strict" in the demo UI or call:

```powershell
Invoke-RestMethod `
  -Method Post `
  -ContentType "application/json" `
  -Uri "http://127.0.0.1:8000/full_pipeline" `
  -Body '{"problem_text":"A 5 V voltage source is connected in series with R1 = 1 kOhm and R2 = 4 kOhm. Find the voltage across R2 and the current through the circuit.","mode":"gemini_strict"}'
```

Run the manual Gemini smoke test:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_test_gemini.py
```

Windows CMD smoke test:

```cmd
set "GEMINI_API_KEY=your_key_here"
set "GEMINI_MODEL=gemini-3.5-flash"
.\.venv\Scripts\python.exe scripts\smoke_test_gemini.py
```

PowerShell smoke test:

```powershell
$env:GEMINI_API_KEY="your_key_here"
$env:GEMINI_MODEL="gemini-3.5-flash"
.\.venv\Scripts\python.exe scripts\smoke_test_gemini.py
```

## macOS And Linux

From the project backend directory:

```bash
cd vericircuit-tutor/backend
python -m venv .venv
./.venv/bin/python -m pip install -e '.[dev]'
```

Set environment variables for the current shell:

```bash
export GEMINI_API_KEY="your_key_here"
export GEMINI_MODEL="gemini-3.5-flash"
```

Run the app:

```bash
./.venv/bin/python -m uvicorn app.main:app --reload
```

To run strict Gemini mode manually:

```bash
curl -s http://127.0.0.1:8000/full_pipeline \
  -H 'Content-Type: application/json' \
  -d '{"problem_text":"A 5 V voltage source is connected in series with R1 = 1 kOhm and R2 = 4 kOhm. Find the voltage across R2 and the current through the circuit.","mode":"gemini_strict"}'
```

Run the manual Gemini smoke test:

```bash
./.venv/bin/python scripts/smoke_test_gemini.py
```

## Security And Authority Boundary

Do not put API keys in frontend code. The static UI never receives the key. Gemini mode runs only on the backend parser path.

Gemini may only return CircuitProblem JSON. The internal MNA solver generates node voltages and component quantities, and the verifier checks KCL, power balance, units, and requested answers.

Parser modes:

- `demo`: deterministic offline parser for bundled examples.
- `gemini`: Gemini parser with deterministic demo fallback if Gemini is unavailable.
- `gemini_strict`: Gemini parser only. If Gemini is unavailable or returns invalid JSON, the API returns a controlled ambiguous CircuitProblem instead of silently falling back.

## Packaging Note

If `python -m pip install -e ".[dev]"` fails with `schematic_exports` discovered as a top-level package, `backend/pyproject.toml` should explicitly restrict setuptools package discovery to `app*`. Generated SVG exports may live in `backend/schematic_exports`, but they are not Python packages and should be ignored by Git.
