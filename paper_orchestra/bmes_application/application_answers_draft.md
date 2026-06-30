# Executive Summary (500 words max)

CiTT is a MATLAB-native, Simscape-grounded AI tutor for biomedical circuit and instrumentation learning. It was developed by a single undergraduate student to address a problem that has become urgent in engineering education: students increasingly use large language models for help, but text-only tutoring can give confident explanations without executable engineering evidence. In biomedical engineering, that is risky because small mistakes in units, signs, node labels, saturation, sampling, or feedback assumptions can completely change the interpretation of a circuit.

Biomedical engineering depends heavily on electrical and computer engineering concepts, including electrophysiology, biosignal acquisition, instrumentation amplifiers, filters, ADCs, sensors, imaging hardware, and feedback systems. Many curricula, including the author's BME coursework, require circuits and instrumentation training because medical-device design and physiological measurement both depend on those foundations. CiTT targets that learning gap by turning prompts or circuit images into structured circuit specifications, then using a MATLAB/Simulink/Simscape workflow to produce inspectable models, focus maps, probe maps, guided teaching, and exportable evidence.

The key design principle is that the LLM/agent layer helps communicate, interpret circuit inputs, and orchestrate tools, but the engineering authority comes from visible artifacts: Simulink/Simscape models, generated plots, simulation metrics, model checks, assumptions, and limitations. The current prototype combines an agent-assisted circuit interpretation path, agentic Simulink/Simscape model generation, Socratic tutoring, model highlight/zoom, natural-language probes, and evidence export in a MATLAB toolbox package.

The release candidate has live evidence for three benchmarks. Benchmark 1 demonstrates an RC anti-aliasing filter with cutoff, attenuation, probe, and Bode evidence. Benchmark 2 demonstrates a two-electrode voltage clamp equivalent circuit with symbolic-value caveats, focus maps, probes, and feedback teaching. Benchmark 3 demonstrates a closed-loop mixed-signal neural clamp using educational scaled parameters, including ADC/digital behavior, saturation/current-limit behavior, non-settling evidence, simulation plots, and metrics JSON.

CiTT is positioned for the Electrical / Computer Science / AI track as educational software for biomedical engineering courses and labs. It is not patient-facing, does not diagnose or treat disease, and does not certify medical-device safety. Its near-term value is classroom utility: helping students and instructors move from paper circuits and AI explanations to reviewable executable models. Its novelty is the integrated authority structure: LLM communication plus model-grounded evidence, not text-only answers.

# Problem Description (125 words max)

Biomedical engineering students must connect circuit theory to physiological measurement systems: electrodes, filters, amplifiers, ADCs, feedback loops, and signal chains. These topics are hard because students must track units, signs, node references, assumptions, saturation, and nonideal behavior while also learning biological context. General-purpose AI tutors can explain concepts fluently, but they may hide mistakes or unsupported assumptions. A student may receive a polished answer without knowing whether the circuit was simulated, whether the units were checked, or whether the stated behavior follows from an executable model. Instructors also need evidence they can inspect. The problem is not AI assistance itself; it is ungrounded authority in engineering tutoring.

# Project Objective (125 words max)

CiTT's objective is to provide a MATLAB-centered AI tutor that grounds biomedical circuit learning in executable model evidence. The prototype should accept a circuit prompt or image, produce a structured circuit specification, build or open an inspectable Simulink/Simscape model, connect teaching steps to focus/highlight maps, answer natural-language probe questions through known model targets, and export reviewer-ready evidence. The educational goal is to help students learn assumptions, limitations, units, feedback, transient behavior, and experimental reasoning while keeping the instructor able to audit the generated artifacts.

# Final Design Documentation (250 words max)

The final prototype is packaged as a MATLAB toolbox and source archive. The main learning surface is the `citt` MATLAB app. The workflow has six components: agent-assisted circuit interpretation, structured circuit specification, agentic Simulink/Simscape model generation, model check and artifact storage, Socratic teaching with focus/highlight maps, natural-language probes, and evidence export. Circuit interpretation, Socratic classification, and model-building orchestration all use the user-selected CLI route.

The design uses built-in MATLAB, Simulink, Simscape, and Simscape Electrical capabilities where possible. Standards and risk thinking are applied as educational controls rather than regulated-device claims. Relevant future standards for a clinical or regulated extension would include software lifecycle, risk-management, cybersecurity, and verification practices; the current prototype instead uses scope guardrails, assumptions/limitations reporting, model checks, focus/probe maps, human review, and evidence traceability.

Known risks include an LLM/agent backend misreading a circuit, an agent building an incomplete model, students overtrusting generated simulations, missing nonideal physical effects, dependency on MATLAB/SATK/MCP and configured agent tooling, and ambiguous benchmark inputs. Mitigations include structured specs, visible Simscape diagrams, explicit caveats, saved artifacts, simulation warnings, benchmark comparison files, and an educational-only boundary. The live evidence package is stored at `submission_assets/live_gui_evidence/`; the release package is stored at `release/`.

# Prototype Uploaded Files

Recommended upload bundle:

- `release/CiTT_BMES_2026.mltbx`
- `release/CiTT_BMES_2026_Source.zip`
- `release/CiTT_Release_Notes.md`
- `release/CiTT_Reproducibility_Checklist.md`
- `release/install_and_smoke_test.md`
- `release/example_repro/verification_summary.md`
- `release/example_repro/installed_gui_smoke.png`
- `submission_assets/live_gui_evidence/bmes_live_evidence_report.md`
- `submission_assets/live_gui_evidence/README.md`
- `submission_assets/live_gui_evidence/run_log.md`
- `submission_assets/live_gui_evidence/benchmark_01_textbook_rc/`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/`
- `paper_orchestra/bmes_application/application_answers_draft.md`
- `paper_orchestra/paper/main.tex`

Optional upload if the portal permits multiple figures: selected screenshots from `paper_orchestra/paper/figures/`, especially the app UI, RC model/Bode/probe images, TEVC model/feedback/probe images, and mixed-signal model/timeline/ADC/fault plots.

Video link: add a final narrated walkthrough if one is recorded.

# Functional Proof (250 words max)

Functional proof is stored in `submission_assets/live_gui_evidence/` and reproduced again from the installed toolbox under `release/example_repro/`.

Benchmark 1, an RC anti-aliasing filter, shows the app parsing the task, opening a Simscape model, teaching the cutoff equation, highlighting the signal path, answering a natural-language probe, and producing Bode evidence. The evidence includes `R = 39.8 kOhm`, `C = 100 nF`, `fc = 39.9887 Hz`, `60 Hz attenuation = -5.1205 dB`, and a documented 100 uF unit-mistake comparison.

Benchmark 2, a two-electrode voltage clamp equivalent circuit, shows a Simscape-first model with command source, buffer path, finite-gain amplifier, membrane branch, probes, electrical reference, solver configuration, focus map, and probe map. Numeric values remain symbolic where the benchmark did not supply `V_c` and `R_e`.

Benchmark 3, a mixed-signal neural clamp with educational scaled parameters, shows generated model screenshots, command/ADC/feedback highlights, teaching/probe evidence, simulation plots, metrics JSON, and exported evidence. The run exposed saturation/current-limit behavior and non-settling in the 60 ms window, which is useful limitation evidence. Full external Lab Delta CSV comparison is not claimed because no real external CSV was supplied.

# Prior Art / Patentability (250 words max)

Current alternatives include general LLM tutoring, static circuit calculators, SPICE-style circuit simulation, and manual MATLAB/Simulink/Simscape modeling. Each is useful, but each leaves a gap for biomedical circuit education. General LLMs can explain ideas and solve simple textbook arithmetic, but they do not inherently produce inspectable Simscape artifacts, focus maps, probe maps, or simulation evidence. Traditional simulators provide numerical modeling, but students must already know how to translate a biomedical circuit problem into the simulator. Manual Simulink/Simscape work is powerful but can be slow for beginners and is not automatically connected to Socratic tutoring or submission-ready evidence.

CiTT's differentiation is the integrated workflow: natural-language or image input, structured circuit representation, MATLAB/Simulink/Simscape artifact generation, focus-linked teaching, natural-language probes, and evidence export. The potential protectable concept is not "using AI for tutoring" broadly; it is the model-grounded educational pipeline and evidence authority structure for biomedical circuits. Patentability and freedom-to-operate would require legal review, especially because CiTT depends on existing platforms such as MATLAB, Simulink, Simscape, and agentic tooling.

# Anticipated Regulatory Pathway (125 words max)

The current CiTT prototype is educational software and design-assistance software for engineering coursework. It is not patient-facing, does not acquire live patient data, does not diagnose, monitor, treat, or control patient care, and does not certify medical-device safety. In its current intended use, it should not require a 510(k), De Novo, or PMA pathway. The submission should describe clear educational labeling, human review, and scope guardrails. If a future version were marketed for patient-connected testing, clinical decision support, or regulated medical-device verification, the intended use would change and a separate regulatory, quality-system, cybersecurity, risk-management, and software-validation assessment would be required.

# Estimated Manufacturing Costs (250 words max)

CiTT is software, so the current prototype has no custom hardware bill of materials, manufacturing tooling, sterilization, inventory, or physical assembly cost. Prototype costs are primarily undergraduate development time, MATLAB/Simulink/Simscape access through an academic environment, LLM/agent backend usage, documentation, and testing.

Deployment costs would depend on the institution. In a course that already has MATLAB, Simulink, Simscape, and Simscape Electrical access, the incremental cost is mainly toolbox installation, API configuration, instructor setup, support, and optional lab-computer maintenance. Distribution can use the `.mltbx` package or source zip. A realistic educational commercialization path would include academic licensing, curated course benchmark packs, setup support, instructor onboarding, maintenance, privacy/security review, and possibly LMS integration.

Major future cost drivers are quality assurance, compatibility across MATLAB releases, benchmark expansion, user-support materials, classroom pilots, and institutional IT review. Because the product leverages existing campus modeling infrastructure, the economic plan is software deployment rather than new laboratory hardware.

# Potential Market and Impact (250 words max)

The initial market is biomedical engineering, electrical engineering, neural engineering, and instrumentation courses that already teach circuits, signals, sensors, feedback, and model-based design. The buyer or adopter is likely a university department, instructor, lab coordinator, or educational program; the primary end users are students, teaching assistants, and instructors. Many BME curricula, including the author's coursework, require circuits or instrumentation because biomedical devices depend on electrical measurement and control.

CiTT's impact is educational. Students can compare AI reasoning against visible Simscape models, plots, probes, and warnings. Instructors can inspect assumptions, artifacts, and limitations rather than grading only fluent prose. The system encourages students to ask "what was modeled, what was measured, and what was omitted?" which is central to engineering judgment.

Near-term success can be measured by classroom pilots: fewer unit/sign/node-reference mistakes, faster transition from circuit prompt to inspectable model, instructor-rated usefulness of focus/probe evidence, student ability to explain limitations, and number of cases where CiTT flags ambiguity instead of inventing unsupported results.

# References / Acknowledgements

Primary prototype evidence: `submission_assets/live_gui_evidence/` and `release/`.

Technical platforms: MATLAB, Simulink, Simscape, Simscape Electrical, Simulink Agentic Toolkit / MATLAB agentic tooling, and a configured local agent CLI.

Acknowledgements: The project concept was inspired by biomedical circuits/instrumentation coursework and by Professor Pak Wong's classroom exploration of agent-based teaching. The author also acknowledges MathWorks documentation, agent-tooling documentation, and the BMES/Medtronic competition context.
