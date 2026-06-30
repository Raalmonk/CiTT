# CiTT Parameter Sweep / Tolerance Analysis

Created: 29-Jun-2026 18:00:47

- Nominal cutoff: 40.8089597671527 Hz
- Worst-case cutoff range: [32.388063307264 53.6959996936219] Hz
- Most sensitive parameter: capacitor tolerance
- Suggested design change: Use tighter capacitor tolerance, recalibrate cutoff, or move nominal cutoff away from the requirement edge.

| Case | R tol % | C tol % | Cutoff min Hz | Cutoff max Hz | Pass rate | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R1_C10 | 1 | 10 | 36.73 | 45.8 | 67% | FAIL |
| R1_C20 | 1 | 20 | 33.67 | 51.53 | 33% | FAIL |
| R5_C10 | 5 | 10 | 35.33 | 47.73 | 67% | FAIL |
| R5_C20 | 5 | 20 | 32.39 | 53.7 | 33% | FAIL |