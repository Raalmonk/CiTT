# CiTT Requirement Check

Created: 01-Jul-2026 03:56:25

| Requirement | Result | Status | Evidence |
| --- | --- | --- | --- |
| Cutoff frequency near target | fc=39.8 Hz, target 40 Hz +/- 10% | PASS | spec + Lab Delta/simulation metrics |
| Sampling frequency satisfies Nyquist | fs=500 Hz, 2*fmax=300 Hz | PASS | spec + simulation metrics |
| Output saturation / clipping absent | none detected | PASS | simulation summary |
| 60 Hz interference attenuation checked | -14.2 dB from simulation | WARN | Lab Delta/simulation metrics |
| Input impedance above threshold | metric not available | NOT_EVALUATED | spec + simulation metrics |
| ADC quantization step below threshold | metric not available | NOT_EVALUATED | spec + simulation metrics |
| Model check has no update errors | model update/check succeeded | PASS | model_check report |
| Focus map available for teaching highlights | artifact exists | PASS | /Users/Raalm/Documents/GitHub/CiTT/matlab/work/test_competition_pack_focus.json |
| Probe map available for guided measurements | artifact exists | PASS | /Users/Raalm/Documents/GitHub/CiTT/matlab/work/test_competition_pack_probe.json |