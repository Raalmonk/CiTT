# Limitations

- CiTT depends on MATLAB, Simulink, Simscape, preferably Simscape Electrical, Gemini configuration, and SATK/MCP-compatible agent tooling.
- Gemini or another parser can misread circuit diagrams or prompts.
- Agentic model generation can produce incomplete or incorrect models.
- Students may overtrust generated simulations if assumptions and limitations are not reviewed.
- Simscape models may omit nonidealities that matter in real hardware or biology.
- Benchmark 2 retains symbolic V_c and R_e; numeric simulation requires assigning missing values.
- Benchmark 3 uses educational scaled parameters. It is an educational benchmark model, not a patient model.
- Benchmark 3 produced non-settling, saturation, and algebraic-loop warnings; these are reported as educational limitation evidence.
- Full Lab Delta CSV comparison remains pending because no external lab CSV was supplied.
- LLM-only baselines are non-exhaustive and manually provided; they should be treated as comparison artifacts.
- Current writing package is a CVPR-style systems draft for course/design-competition review, not a real CVPR submission.
