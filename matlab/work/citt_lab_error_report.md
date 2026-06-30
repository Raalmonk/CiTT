# CiTT Lab Error Report

- CSV: /Users/Raalm/Documents/GitHub/CiTT/matlab/work/test_lab_delta.csv
- JSON: /Users/Raalm/Documents/GitHub/CiTT/matlab/work/test_lab_delta_report.json
- Spec: /Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_last_circuit_spec.json
- Probe map: /Users/Raalm/Documents/GitHub/CiTT/matlab/work/citt_probe_map.json

## Rows

| Quantity | Unit | Measured | Reference | Difference | Status | Probe |
| --- | --- | --- | --- | --- | --- | --- |
| fc_hz | Hz | 251.3 | sim 40.1 | 527% | INVESTIGATE | P_VIN |

## Nonideal Device Profiles

- None detected.

## Likely Causes

- **Large error in fc_hz** (likely): Measured value differs from the reference by more than 15%. Next: Check units, reference node, probe placement, and settling for this quantity first.
- **2*pi error** (likely): The measured/reference ratio is close to 2*pi or 1/(2*pi). Next: Check whether one side used Hz and the other used rad/s.
- **Probe unit mismatch** (warning): The CSV unit differs from the probe-map unit. Next: Normalize units before comparing numeric values.
- **Model assumption may not match lab hardware** (possible): The circuit spec includes idealized or simplified assumptions that can produce lab/model mismatch. Next: Check which assumptions are invalid in the lab setup before treating the error as a component fault.

## Next Actions

- Check units, reference node, probe placement, and settling for this quantity first.
- Check whether one side used Hz and the other used rad/s.
- Normalize units before comparing numeric values.
- Check which assumptions are invalid in the lab setup before treating the error as a component fault.