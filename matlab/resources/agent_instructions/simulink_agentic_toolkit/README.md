# Repo-local Simulink Agentic Toolkit instructions

This directory is a CiTT-local copy of the Simulink Agentic Toolkit agent-facing instructions and tool metadata.

Source captured from:

```text
/Users/Raalm/.matlab/agentic-toolkits/simulink
```

Captured files:

- `AGENTS.md` agent instructions
- `CITT_AGENTS.md` CiTT-specific build addendum
- `LICENSE.upstream.md`
- `VERSION.upstream`
- `tools/tools.json`
- `tools/registry.json`

CiTT build tasks should embed the local `AGENTS.md` content and may point to these repo-local references. External agents must not read arbitrary files under user home skill directories while executing a CiTT build task.
