# CiTT MATLAB Examples

This folder is intentionally small. The MATLAB plugin is not centered on canned labs.

Use it for tiny local fixtures only. The main flow is:

```matlab
addpath("matlab")
citt
```

Then select a circuit image or enter a prompt, parse with the selected CLI, generate the SATK agent task, and build the Simscape/Simulink model through the configured agent workflow.
