# Gemini API Setup

VeriCircuit Tutor works without external API keys. In that mode, the deterministic demo parser handles the bundled examples. Gemini mode is optional and is only used to produce CircuitProblem JSON. It must not produce final numerical answers.

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

## Security And Authority Boundary

Do not put API keys in frontend code. The static UI never receives the key. Gemini mode runs only on the backend parser path.

Gemini may only return CircuitProblem JSON. The internal MNA solver generates node voltages and component quantities, and the verifier checks KCL, power balance, units, and requested answers.

