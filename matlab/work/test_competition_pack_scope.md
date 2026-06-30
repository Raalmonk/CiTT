# CiTT Regulatory / Scope Guardrail

Created: 29-Jun-2026 18:00:49

- Potential regulatory category: educational design-training tool with patient-connected-topic warnings
- Patient-connected trigger detected: true

## Boundaries

- This model is educational and proposal-facing.
- This is not clinical diagnosis.
- This is not medical-device verification.
- Generated model behavior depends on explicit assumptions, component values, and solver configuration.

## Standards / Reviews To Consider

- isolation/leakage-current review
- EMC review
- front-end safety review
- institutional lab safety policy

## Risks

| Risk | Trigger | Mitigation | Severity |
| --- | --- | --- | --- |
| Student mistakes simulation for certified device behavior | Any generated model or performance table | Display educational boundary and assumptions in every export. | Medium |
| Generated circuit omits patient isolation or leakage-current constraints | Spec contains biomedical/patient-connected terms | Warn that patient-connected hardware needs separate isolation, leakage, and EMC analysis. | High |
| LLM parse error becomes hidden design assumption | Selected CLI structured spec drives model generation | Expose parsed spec, assumptions, ambiguities, and model-check status in Evidence Pack. | Medium |