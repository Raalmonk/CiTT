# Local Debugging And Visual QA

## Circuit Diagram Checks

Run the app:

```powershell
cd vericircuit-tutor\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

Check these demo paths:

1. Run **Bridge Network**.
2. Run **Second Bridge Network**.
3. Generate and load a **Goal variant**.
4. Generate and load a **Value variant**.

In the Circuit Diagram panel, verify:

- R1, R2, R3, R4, and R5 labels are readable.
- n1/src, n2/a, n3/b, and 0 node labels are separated from component labels.
- V1 label does not collide with the source or ground symbol.
- The bridge resistor R5 label is above the horizontal resistor.
- The diagram remains full-width and is not squeezed in the two-column UI.

Diagram generation is deterministic and based only on Circuit IR. It does not affect solver output, MNA verification, or tutor answers.

