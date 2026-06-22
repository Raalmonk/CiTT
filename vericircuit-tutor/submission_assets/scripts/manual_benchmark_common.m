function result = manual_benchmark_common(action, benchmarkNumber)
%MANUAL_BENCHMARK_COMMON Checkpointed live evidence workflow.
%
% This helper intentionally does not generate final reports and does not use
% the local Simscape fallback. It prepares one benchmark at a time, then
% stops for manual Simscape layout cleanup.

arguments
    action (1, 1) string {mustBeMember(action, ["prepare", "continue"])}
    benchmarkNumber (1, 1) double {mustBeInteger, mustBePositive}
end

paths = workflowPaths();
ensureFolders(paths);
ensureOfflineDraft(paths);

switch action
    case "prepare"
        result = prepareBenchmark(paths, benchmarkNumber);
    case "continue"
        result = continueBenchmark(paths, benchmarkNumber);
end
end

function paths = workflowPaths()
scriptDir = string(fileparts(mfilename("fullpath")));
paths.assetsRoot = string(fileparts(scriptDir));
paths.vericircuitRoot = string(fileparts(paths.assetsRoot));
paths.matlabRoot = string(fullfile(paths.vericircuitRoot, "matlab"));
paths.checkpointDir = string(fullfile(paths.assetsRoot, "manual_checkpoints"));
paths.runLogPath = string(fullfile(paths.assetsRoot, "benchmark_run_log.md"));
addpath(char(paths.matlabRoot));
end

function ensureFolders(paths)
if exist(paths.checkpointDir, "dir") ~= 7
    mkdir(paths.checkpointDir);
end
end

function ensureOfflineDraft(paths)
reportPath = string(fullfile(paths.assetsRoot, "bmes_evidence_report.md"));
draftPath = string(fullfile(paths.assetsRoot, "bmes_evidence_report_OFFLINE_DRAFT.md"));
pdfPath = string(fullfile(paths.assetsRoot, "bmes_evidence_report.pdf"));
pdfDraftPath = string(fullfile(paths.assetsRoot, "bmes_evidence_report_OFFLINE_DRAFT.pdf"));

if exist(reportPath, "file") == 2 && exist(draftPath, "file") ~= 2
    movefile(reportPath, draftPath);
end
if exist(pdfPath, "file") == 2 && exist(pdfDraftPath, "file") ~= 2
    movefile(pdfPath, pdfDraftPath);
end
if exist(draftPath, "file") == 2
    text = string(fileread(draftPath));
    warningText = "OFFLINE DRAFT — NOT FINAL SUBMISSION EVIDENCE." + newline + ...
        "This draft was generated without live manual Simscape arrangement and should not be treated as final functional proof.";
    if ~startsWith(text, warningText)
        writeText(draftPath, warningText + newline + newline + text);
    end
end
end

function result = prepareBenchmark(paths, benchmarkNumber)
bench = benchmarkInfo(paths, benchmarkNumber);
ensurePreparePrerequisite(paths, benchmarkNumber);
ensureFoldersForBenchmark(bench);

appendRunLog(paths, "Prepare benchmark " + benchmarkNumber + ": " + bench.title);

problemText = readProblemText(bench);
writeText(bench.problemLivePath, problemText);
if exist(bench.inputImagePath, "file") ~= 2
    createInputPanel(bench.inputImagePath, bench.title, problemText);
end

parseStatus = "codex_parser";
parseSummary = "";
try
    parseResult = feval('citt.parseCircuitWithGemini', bench.inputImagePath, problemText, struct( ...
        "OutputPath", bench.specPath, ...
        "ParserBackend", "codex"));
    parseSummary = "Codex parser produced a live CiTT circuit spec.";
catch parseError
    spec = fixedBenchmarkSpec(benchmarkNumber);
    spec.parser_note = "Fixed benchmark spec used because live parser failed: " + string(parseError.message);
    writeJson(bench.specPath, spec);
    parseStatus = "fixed_test_spec_due_to_parse_failure";
    parseSummary = "Live parser failed; wrote fixed benchmark spec. Error: " + string(parseError.message);
end
writeText(bench.parseLogPath, joinLines([
    "# Parse Log"
    ""
    "- Status: " + parseStatus
    "- Spec: `" + bench.specPath + "`"
    ""
    parseSummary
]));

setenv("CITT_USE_LOCAL_SIMSCAPE_FALLBACK", "0");
setenv("CITT_LOCAL_SIMSCAPE_FALLBACK", "0");

taskResult = feval('citt.buildAgentTask', bench.specPath, struct("TaskPath", bench.taskPath));
writeJson(bench.taskResultPath, taskResult);

try
    agentResult = feval('citt.runAgentTask', bench.taskPath, struct( ...
        "SpecPath", bench.specPath, ...
        "Async", false, ...
        "UseLocalFallback", false));
catch agentError
    writeBlockerCheckpoint(paths, bench, "SATK agent threw an error before producing a model: " + string(agentError.message));
    rethrow(agentError);
end
writeJson(bench.agentResultPath, agentResult);

if ~isfield(agentResult, "success") || ~logical(agentResult.success)
    detail = string(agentResult.summary);
    if isfield(agentResult, "stderr") && strlength(string(agentResult.stderr)) > 0
        detail = detail + newline + string(agentResult.stderr);
    end
    writeBlockerCheckpoint(paths, bench, detail);
    error("CiTT:BenchmarkPrepareFailed", "Benchmark %d did not produce a live SATK model. See %s.", benchmarkNumber, bench.blockerPath);
end

sourceModel = string(agentResult.produced_model_path);
if strlength(sourceModel) == 0
    config = feval('citt.loadConfig');
    sourceModel = string(config.GeneratedModelPath);
end
if exist(sourceModel, "file") ~= 4 && exist(sourceModel, "file") ~= 2
    writeBlockerCheckpoint(paths, bench, "Agent reported success but model was not found: " + sourceModel);
    error("CiTT:GeneratedModelMissing", "Generated model not found: %s", sourceModel);
end

copyLiveArtifact(sourceModel, bench.modelPath);
copyOptionalArtifact(agentResult, "produced_focus_map_path", bench.focusMapPath);
copyOptionalArtifact(agentResult, "produced_probe_map_path", bench.probeMapPath);
copyOptionalArtifact(agentResult, "agent_report_path", bench.agentReportPath);

try
    open_system(char(bench.modelPath));
catch openError
    writeBlockerCheckpoint(paths, bench, "Model was generated but could not be opened: " + string(openError.message));
    rethrow(openError);
end

readyText = readyCheckpointText(bench, parseStatus);
writeText(bench.readyPath, readyText);
appendRunLog(paths, "Benchmark " + benchmarkNumber + " READY_FOR_MANUAL_ARRANGEMENT: " + bench.modelPath);

fprintf("\nMANUAL SIMSCAPE ARRANGEMENT REQUIRED\n\n");
fprintf("Benchmark %d is ready: %s\n", benchmarkNumber, bench.title);
fprintf("Model path: %s\n\n", bench.modelPath);
fprintf("%s\n", manualInstructions(bench));
fprintf("\nAfter saving the arranged model, tell Codex: continue benchmark %d\n\n", benchmarkNumber);

result = struct();
result.ready = true;
result.benchmark = benchmarkNumber;
result.model_path = bench.modelPath;
result.ready_checkpoint = bench.readyPath;
end

function result = continueBenchmark(paths, benchmarkNumber)
bench = benchmarkInfo(paths, benchmarkNumber);
if exist(bench.readyPath, "file") ~= 2
    error("CiTT:ReadyCheckpointMissing", ...
        "Benchmark %d is not ready. Run prepare_benchmark_%02d.m first.", benchmarkNumber, benchmarkNumber);
end
if exist(bench.modelPath, "file") ~= 4 && exist(bench.modelPath, "file") ~= 2
    error("CiTT:ModelMissing", "Manual model file is missing: %s", bench.modelPath);
end

appendRunLog(paths, "Continue benchmark " + benchmarkNumber + ": capturing live arranged model evidence.");

try
    open_system(char(bench.modelPath));
catch openError
    error("CiTT:ModelOpenFailed", "Could not open arranged model: %s", openError.message);
end

snapshotPath = string(fullfile(bench.dir, "model_screenshot_live.png"));
snapshotStatus = "not captured";
try
    captured = feval('citt.captureModelSnapshot', bench.modelPath, struct("OutputPath", snapshotPath));
    snapshotStatus = "captured: " + string(captured.image_path);
catch captureError
    snapshotStatus = "capture failed: " + string(captureError.message);
end

checkPath = string(fullfile(bench.dir, "model_check_live.md"));
checkStatus = "not run";
try
    checkResult = feval('citt.runModelCheck', bench.modelPath);
    checkStatus = string(checkResult.summary);
    if isfield(checkResult, "markdown_path") && strlength(string(checkResult.markdown_path)) > 0
        copyLiveArtifact(string(checkResult.markdown_path), checkPath);
    else
        writeText(checkPath, checkStatus);
    end
catch checkError
    checkStatus = "check failed: " + string(checkError.message);
    writeText(checkPath, checkStatus);
end

comparisonPath = string(fullfile(bench.dir, "comparison_live.md"));
writeText(comparisonPath, joinLines([
    "# Live Comparison Notes"
    ""
    "- Model screenshot: " + snapshotStatus
    "- Model check: " + checkStatus
    "- Manual arrangement checkpoint was required before this file was written."
    "- Offline panels in this folder are not final evidence."
]));

doneText = joinLines([
    "# Benchmark " + benchmarkNumber + " SCREENSHOTS_DONE"
    ""
    "- Benchmark: " + bench.title
    "- Model: `" + bench.modelPath + "`"
    "- Screenshot: `" + snapshotPath + "`"
    "- Model check notes: `" + checkPath + "`"
    "- Comparison notes: `" + comparisonPath + "`"
    "- Timestamp: " + string(datetime("now", "Format", "yyyy-MM-dd HH:mm:ss z"))
]);
writeText(bench.donePath, doneText);
appendRunLog(paths, "Benchmark " + benchmarkNumber + " SCREENSHOTS_DONE: " + snapshotPath);

fprintf("\nBenchmark %d screenshots/check notes are done.\n", benchmarkNumber);
if benchmarkNumber < 3
    fprintf("Proceeding to prepare benchmark %d.\n", benchmarkNumber + 1);
    result = prepareBenchmark(paths, benchmarkNumber + 1);
else
    fprintf("All benchmark manual checkpoints are complete. Final report can now be generated separately.\n");
    result = struct("done", true, "benchmark", benchmarkNumber, "done_checkpoint", bench.donePath);
end
end

function ensurePreparePrerequisite(paths, benchmarkNumber)
if benchmarkNumber <= 1
    return
end
previous = benchmarkInfo(paths, benchmarkNumber - 1);
if exist(previous.donePath, "file") ~= 2
    error("CiTT:ManualCheckpointMissing", ...
        "Do not prepare benchmark %d yet. Finish benchmark %d manual arrangement and run continue_benchmark_%02d.m first.", ...
        benchmarkNumber, benchmarkNumber - 1, benchmarkNumber - 1);
end
end

function ensureFoldersForBenchmark(bench)
if exist(bench.dir, "dir") ~= 7
    mkdir(bench.dir);
end
end

function bench = benchmarkInfo(paths, n)
switch n
    case 1
        slug = "benchmark_01_textbook_rc";
        title = "Textbook RC Anti-Aliasing Filter Before an ADC";
    case 2
        slug = "benchmark_02_tevc_equilibrium";
        title = "Two-Electrode Voltage Clamp Equivalent Circuit";
    case 3
        slug = "benchmark_03_mixed_signal_simscape";
        title = "Closed-Loop Neural Clamp With Nonideal Amplifier, ADC, and Digital Control Logic";
    otherwise
        error("CiTT:UnknownBenchmark", "Unknown benchmark number: %d", n);
end

bench = struct();
bench.number = n;
bench.slug = string(slug);
bench.title = string(title);
bench.dir = string(fullfile(paths.assetsRoot, slug));
bench.problemPath = string(fullfile(bench.dir, "problem_statement.md"));
bench.problemLivePath = string(fullfile(bench.dir, "problem_statement_live.md"));
bench.inputImagePath = string(fullfile(bench.dir, "input_schematic.png"));
bench.specPath = string(fullfile(bench.dir, "citt_spec_live.json"));
bench.parseLogPath = string(fullfile(bench.dir, "parse_log_live.md"));
bench.taskPath = string(fullfile(bench.dir, "citt_agent_task_live.md"));
bench.taskResultPath = string(fullfile(bench.dir, "citt_agent_task_result_live.json"));
bench.agentResultPath = string(fullfile(bench.dir, "citt_agent_result_live.json"));
bench.modelPath = string(fullfile(bench.dir, slug + "_live_model.slx"));
bench.focusMapPath = string(fullfile(bench.dir, "focus_map_live.json"));
bench.probeMapPath = string(fullfile(bench.dir, "probe_map_live.json"));
bench.agentReportPath = string(fullfile(bench.dir, "citt_agent_report_live.md"));
bench.readyPath = string(fullfile(paths.checkpointDir, sprintf("benchmark_%02d_READY_FOR_MANUAL_ARRANGEMENT.md", n)));
bench.donePath = string(fullfile(paths.checkpointDir, sprintf("benchmark_%02d_SCREENSHOTS_DONE.md", n)));
bench.blockerPath = string(fullfile(paths.checkpointDir, sprintf("benchmark_%02d_BLOCKED.md", n)));
end

function text = readProblemText(bench)
if exist(bench.problemPath, "file") == 2
    text = string(fileread(bench.problemPath));
else
    text = "# " + bench.title + newline + newline + defaultProblemText(bench.number);
end
text = text + newline + newline + ...
    "Live correction-pass instruction: build a Simscape-first model with SATK/Codex, open it visibly, then stop before screenshots so a human can manually arrange and save the Simulink diagram.";
end

function text = defaultProblemText(n)
switch n
    case 1
        text = "Build a first-order RC low-pass filter before a 500 Hz ADC. Use R = 39.8 kOhm and C = 100 nF. Probe input, filtered output, and sampled output. Explain cutoff, 60 Hz attenuation, Nyquist attenuation, and a 100 uF unit mistake.";
    case 2
        text = "Build a simplified two-electrode voltage clamp equilibrium circuit with command voltage, finite gain differential amplifier, electrode resistance, membrane resistance, output resistance, feedback, Vm probe, amplifier output probe, and clamp current probe.";
    otherwise
        text = "Build a closed-loop neural clamp with membrane capacitance/leakage, electrode resistance, finite gain amplifier, rail and current limits, ADC quantization, digital comparator/state logic, DAC command path, Vm and saturation probes.";
end
end

function spec = fixedBenchmarkSpec(n)
switch n
    case 1
        spec = fixedBenchmark01Spec();
    case 2
        spec = fixedBenchmark02Spec();
    case 3
        spec = fixedBenchmark03Spec();
    otherwise
        error("CiTT:UnknownBenchmark", "Unknown benchmark number: %d", n);
end
end

function spec = fixedBenchmark01Spec()
spec = baseSpec("Textbook RC Anti-Aliasing Filter Before an ADC", ...
    ["vin_node", "vout_node", "adc_sample_node", "gnd"], "gnd", ...
    "time_domain_and_frequency_response_for_first_order_rc_filter");
spec.components = [
    component("VIN", "composite_voltage_source", "ECG-like input with 5 Hz component, 60 Hz interference, and optional high-frequency noise", struct("ecg_hz", 5, "interference_hz", 60), "V", ["p", "n"])
    component("R1", "resistor", "39.8 kOhm series resistor", 39.8e3, "ohm", ["p", "n"])
    component("C1", "capacitor", "100 nF shunt capacitor", 100e-9, "F", ["p", "n"])
    component("ADC1", "sample_and_hold_adc", "500 Hz ADC sampler", struct("sample_rate_hz", 500), "Hz", ["in", "out", "ref"])
    component("PROBE_VOUT", "voltage_probe", "Filtered output voltage probe", [], "V", ["p", "n"])
    component("PROBE_ADC", "signal_probe", "ADC sampled output probe", [], "count", ["in"])
];
spec.connections = [
    connection("VIN.p", "vin_node", "input source positive")
    connection("VIN.n", "gnd", "input source reference")
    connection("R1.p", "vin_node", "R1 input")
    connection("R1.n", "vout_node", "R1 output")
    connection("C1.p", "vout_node", "capacitor at filtered output")
    connection("C1.n", "gnd", "capacitor reference")
    connection("ADC1.in", "vout_node", "ADC samples filtered output")
    connection("ADC1.ref", "gnd", "ADC reference")
    connection("ADC1.out", "adc_sample_node", "sampled output")
    connection("PROBE_VOUT.p", "vout_node", "probe filtered output")
    connection("PROBE_VOUT.n", "gnd", "probe reference")
    connection("PROBE_ADC.in", "adc_sample_node", "probe sampled output")
];
spec.sources = {struct("id", "VIN", "type", "multi_sine_voltage", "description", "5 Hz ECG-like plus 60 Hz interference")};
spec.requested_outputs = ["Cutoff frequency", "60 Hz attenuation", "Nyquist attenuation", "Vout probe", "ADC sampled output", "100 uF lab delta"];
spec.suggested_simscape_blocks = ["Voltage Source", "Resistor", "Capacitor", "Voltage Sensor", "Electrical Reference", "Solver Configuration", "Zero-Order Hold", "Quantizer", "Scope"];
spec.focus_points = [
    focus("cutoff_frequency", "Cutoff frequency", "R and C set fc = 1/(2*pi*R*C).", ["R1", "C1"], ["vout_node"], "How do R and C determine the -3 dB point?")
    focus("vout_probe_node", "Filtered output node", "The useful analog output is between R1 and C1.", ["R1", "C1", "PROBE_VOUT"], ["vout_node"], "Where should the student measure filtered voltage?")
    focus("nyquist_warning", "Nyquist warning", "The 500 Hz ADC has a 250 Hz Nyquist limit, while one RC pole only rolls off 20 dB/decade.", ["ADC1", "C1"], ["adc_sample_node"], "Why is a single pole helpful but not enough proof of alias rejection?")
    focus("unit_mistake_delta", "100 uF unit mistake", "Changing 100 nF to 100 uF moves the cutoff by 1000x.", ["C1"], ["vout_node"], "What happens if the capacitor unit is entered incorrectly?")
];
end

function spec = fixedBenchmark02Spec()
spec = baseSpec("Two-Electrode Voltage Clamp Equivalent Circuit", ...
    ["vc_node", "amp_out_node", "electrode_node", "vm_node", "body_ref"], "body_ref", ...
    "dc_operating_point_feedback_loop");
spec.components = [
    component("VC", "dc_voltage_source", "Command voltage source", 0.05, "V", ["p", "n"])
    component("A_DIFF", "finite_gain_differential_amplifier", "Finite gain differential amplifier A = 100", 100, "V/V", ["vp", "vn", "out", "ref"])
    component("RO", "resistor", "10 ohm output/electrode resistance", 10, "ohm", ["p", "n"])
    component("RE", "resistor", "Voltage electrode resistance", 1000, "ohm", ["p", "n"])
    component("RM", "resistor", "10 ohm membrane resistance", 10, "ohm", ["p", "n"])
    component("PROBE_VM", "voltage_probe", "Membrane voltage probe", [], "V", ["p", "n"])
    component("PROBE_IO", "current_probe", "Clamp current probe", [], "A", ["p", "n"])
];
spec.connections = [
    connection("VC.p", "vc_node", "command voltage")
    connection("VC.n", "body_ref", "command reference")
    connection("A_DIFF.vp", "vc_node", "noninverting command input")
    connection("A_DIFF.vn", "vm_node", "feedback from membrane voltage")
    connection("A_DIFF.ref", "body_ref", "amplifier reference")
    connection("A_DIFF.out", "amp_out_node", "amplifier output")
    connection("RO.p", "amp_out_node", "output resistance input")
    connection("RO.n", "electrode_node", "output resistance output")
    connection("RE.p", "electrode_node", "recording electrode")
    connection("RE.n", "vm_node", "membrane node")
    connection("RM.p", "vm_node", "membrane resistance")
    connection("RM.n", "body_ref", "membrane reference")
    connection("PROBE_VM.p", "vm_node", "probe Vm")
    connection("PROBE_VM.n", "body_ref", "probe reference")
    connection("PROBE_IO.p", "RO.p", "current through output path")
    connection("PROBE_IO.n", "RO.n", "current through output path")
];
spec.sources = {struct("id", "VC", "type", "dc_command_voltage")};
spec.requested_outputs = ["Vm", "amplifier output", "clamp current", "feedback loop highlight", "finite gain tracking error"];
spec.assumptions = ["Equilibrium model only; membrane capacitance and ion-channel dynamics are intentionally omitted."];
spec.suggested_simscape_blocks = ["Controlled Voltage Source", "Resistor", "Voltage Sensor", "Current Sensor", "Electrical Reference", "Solver Configuration"];
spec.focus_points = [
    focus("feedback_loop", "Voltage clamp feedback loop", "The amplifier compares Vc and Vm, then drives current through output/electrode resistance.", ["VC", "A_DIFF", "RO", "RE", "RM"], ["vc_node", "vm_node"], "How does the feedback path push Vm toward Vc?")
    focus("tracking_error", "Finite gain tracking error", "A finite amplifier gain means Vc and Vm do not become exactly equal.", ["A_DIFF", "RM", "RO"], ["vm_node"], "Why does finite gain leave a residual error?")
    focus("clamp_current", "Clamp current path", "Clamp current flows through the output path and membrane load.", ["PROBE_IO", "RO", "RM"], ["electrode_node", "vm_node"], "Where is the current that controls Vm actually flowing?")
];
end

function spec = fixedBenchmark03Spec()
spec = baseSpec("Closed-Loop Neural Clamp With Nonideal Amplifier, ADC, and Digital Control Logic", ...
    ["vc_cmd", "amp_out", "electrode", "vm", "adc_code", "control_state", "body_ref"], "body_ref", ...
    "mixed_signal_time_domain_simscape_transient");
spec.components = [
    component("VC_STEP", "step_voltage_source", "Command voltage step", struct("initial", -0.07, "final", -0.04, "step_time", 0.01), "V,s", ["p", "n"])
    component("AMP", "limited_finite_gain_amplifier", "Finite gain amplifier with rails/current limit", struct("gain", 500, "rail_pos", 3.3, "rail_neg", 0, "current_limit", 0.01), "mixed", ["vp", "vn", "out", "ref"])
    component("RE", "resistor", "Electrode series resistance", 1000, "ohm", ["p", "n"])
    component("CM", "capacitor", "Membrane capacitance", 1e-6, "F", ["p", "n"])
    component("RM", "resistor", "Membrane leakage resistance", 100e3, "ohm", ["p", "n"])
    component("ADC", "quantizing_adc", "ADC sampling and quantization of Vm", struct("sample_rate_hz", 10000, "bits", 12), "mixed", ["in", "out", "ref"])
    component("CTRL", "digital_comparator_state_logic", "Digital comparator or finite-state control logic", [], "", ["in", "out"])
    component("DAC", "dac_command_update", "DAC command update path", [], "V", ["in", "out", "ref"])
    component("PROBE_VM", "voltage_probe", "Membrane voltage probe", [], "V", ["p", "n"])
    component("PROBE_SAT", "signal_probe", "Saturation flag probe", [], "", ["in"])
];
spec.connections = [
    connection("VC_STEP.p", "vc_cmd", "command step")
    connection("VC_STEP.n", "body_ref", "command reference")
    connection("AMP.vp", "vc_cmd", "command input")
    connection("AMP.vn", "vm", "Vm feedback")
    connection("AMP.ref", "body_ref", "amplifier reference")
    connection("AMP.out", "amp_out", "limited amplifier output")
    connection("RE.p", "amp_out", "electrode drive")
    connection("RE.n", "electrode", "electrode node")
    connection("CM.p", "vm", "membrane capacitance")
    connection("CM.n", "body_ref", "membrane reference")
    connection("RM.p", "vm", "membrane leakage")
    connection("RM.n", "body_ref", "membrane reference")
    connection("electrode", "vm", "simplified electrode-to-membrane interface")
    connection("ADC.in", "vm", "sample Vm")
    connection("ADC.ref", "body_ref", "ADC reference")
    connection("ADC.out", "adc_code", "ADC code")
    connection("CTRL.in", "adc_code", "digital control input")
    connection("CTRL.out", "control_state", "control state")
    connection("DAC.in", "control_state", "DAC command input")
    connection("DAC.out", "vc_cmd", "DAC update")
    connection("DAC.ref", "body_ref", "DAC reference")
    connection("PROBE_VM.p", "vm", "probe membrane voltage")
    connection("PROBE_VM.n", "body_ref", "probe reference")
    connection("PROBE_SAT.in", "control_state", "probe digital state and saturation flags")
];
spec.sources = {struct("id", "VC_STEP", "type", "command_step")};
spec.requested_outputs = ["Vm(t)", "clamp current", "amplifier output", "ADC code sequence", "digital control state", "saturation flags", "settling time", "overshoot"];
spec.assumptions = ["Simplified nonlinear membrane current is optional; leakage plus capacitance is acceptable for the live benchmark."];
spec.suggested_simscape_blocks = ["Controlled Voltage Source", "Resistor", "Capacitor", "Voltage Sensor", "Current Sensor", "Saturation", "Quantizer", "Zero-Order Hold", "Stateflow Chart", "Electrical Reference", "Solver Configuration"];
spec.focus_points = [
    focus("physical_membrane", "Physical membrane dynamics", "The membrane RC network creates transient behavior that is hard to solve reliably by text alone.", ["CM", "RM", "RE"], ["vm"], "Why does the membrane voltage settle over time instead of changing instantly?")
    focus("mixed_signal_loop", "Mixed-signal loop", "ADC, digital logic, DAC, and amplifier limits close the loop around the physical membrane.", ["ADC", "CTRL", "DAC", "AMP"], ["adc_code", "control_state", "vc_cmd"], "Where does the continuous circuit become digital and then become analog again?")
    focus("saturation_limits", "Nonideal limits", "Rail and current limits can dominate the transient and change settling behavior.", ["AMP", "PROBE_SAT"], ["amp_out", "control_state"], "How can saturation make a simple closed-form answer wrong?")
];
end

function spec = baseSpec(circuitType, nodes, groundNode, likelyAnalysis)
spec = struct();
spec.circuit_type = circuitType;
spec.components = struct([]);
spec.connections = struct([]);
spec.nodes = nodes;
spec.ground_node = groundNode;
spec.sources = {};
spec.requested_outputs = strings(0, 1);
spec.assumptions = strings(0, 1);
spec.ambiguities = strings(0, 1);
spec.unsupported_or_unclear_regions = strings(0, 1);
spec.suggested_simscape_blocks = strings(0, 1);
spec.likely_analysis = likelyAnalysis;
spec.focus_points = struct([]);
end

function item = component(id, type, label, value, unit, terminals)
item = struct();
item.id = string(id);
item.type = string(type);
item.label = string(label);
item.value = value;
item.unit = string(unit);
item.terminals = terminals;
item.confidence = 0.9;
end

function item = connection(from, to, label)
item = struct();
item.from = string(from);
item.to = string(to);
item.label = string(label);
item.confidence = 0.9;
end

function item = focus(id, label, reason, relatedComponents, relatedNodes, teachingQuestion)
item = struct();
item.id = string(id);
item.label = string(label);
item.reason = string(reason);
item.related_components = relatedComponents;
item.related_nodes = relatedNodes;
item.teaching_question = string(teachingQuestion);
end

function text = readyCheckpointText(bench, parseStatus)
text = joinLines([
    "# Benchmark " + bench.number + " READY_FOR_MANUAL_ARRANGEMENT"
    ""
    "- Benchmark: " + bench.title
    "- Parse status: " + parseStatus
    "- Model path: `" + bench.modelPath + "`"
    "- Spec path: `" + bench.specPath + "`"
    "- Agent task: `" + bench.taskPath + "`"
    "- Focus map: `" + bench.focusMapPath + "`"
    "- Probe map: `" + bench.probeMapPath + "`"
    "- Timestamp: " + string(datetime("now", "Format", "yyyy-MM-dd HH:mm:ss z"))
    ""
    "## Manual Instructions"
    ""
    manualInstructions(bench)
    ""
    "After saving the arranged model, tell Codex exactly:"
    ""
    "`continue benchmark " + bench.number + "`"
]);
end

function text = manualInstructions(bench)
switch bench.number
    case 1
        bullets = [
            "- Arrange the analog chain left-to-right: input source -> R1 -> Vout node -> ADC/sample path."
            "- Put C1, Electrical Reference, and Solver Configuration where their physical role is visually obvious."
            "- Keep voltage sensors/probes close to the Vout and ADC output paths without crossing the main RC line."
            "- Make the cutoff-frequency teaching focus easy to screenshot: R1 and C1 should be visible together."
            "- Save the model after cleaning the wiring."
        ];
    case 2
        bullets = [
            "- Arrange the feedback loop so command, amplifier, output resistance, membrane/electrode path, and Vm feedback form a visible loop."
            "- Put Vm, amplifier output, and clamp-current probes beside the signals they measure."
            "- Keep biological omissions out of the diagram; this benchmark is equilibrium-only."
            "- Save the model after cleaning the wiring."
        ];
    otherwise
        bullets = [
            "- Arrange the physical membrane/electrode path separately from the ADC/digital/DAC path."
            "- Make the continuous-to-digital-to-analog loop visually obvious."
            "- Keep saturation/current-limit flags and probes close to the amplifier/control blocks."
            "- Save the model after cleaning the wiring."
        ];
end
text = joinLines([
    "MANUAL SIMSCAPE ARRANGEMENT REQUIRED"
    ""
    "Please manually clean up the generated Simulink/Simscape diagram before any screenshots are accepted as evidence."
    bullets
]);
end

function writeBlockerCheckpoint(paths, bench, detail)
text = joinLines([
    "# Benchmark " + bench.number + " BLOCKED"
    ""
    "- Benchmark: " + bench.title
    "- Model target: `" + bench.modelPath + "`"
    "- Timestamp: " + string(datetime("now", "Format", "yyyy-MM-dd HH:mm:ss z"))
    ""
    "## Blocking Detail"
    ""
    string(detail)
]);
writeText(bench.blockerPath, text);
appendRunLog(paths, "Benchmark " + bench.number + " BLOCKED: " + string(detail));
end

function createInputPanel(path, title, problemText)
figureHandle = figure("Visible", "off", "Color", "w", "Position", [100 100 1400 900]);
axis off;
wrapped = wrapText(problemText, 120);
text(0.04, 0.94, title, "Units", "normalized", "FontWeight", "bold", "FontSize", 22, "Color", [0.05 0.12 0.09]);
text(0.04, 0.86, wrapped, "Units", "normalized", "FontName", "Menlo", "FontSize", 13, "Color", [0.15 0.21 0.18], "VerticalAlignment", "top");
exportgraphics(figureHandle, char(path), "Resolution", 180);
close(figureHandle);
end

function text = wrapText(text, width)
words = split(strrep(string(text), newline, " "));
lines = strings(0, 1);
current = "";
for i = 1:numel(words)
    word = strtrim(words(i));
    if strlength(word) == 0
        continue
    end
    if strlength(current) + strlength(word) + 1 > width
        lines(end + 1) = current; %#ok<AGROW>
        current = word;
    else
        if strlength(current) == 0
            current = word;
        else
            current = current + " " + word;
        end
    end
end
if strlength(current) > 0
    lines(end + 1) = current;
end
text = strjoin(lines, newline);
end

function copyOptionalArtifact(result, fieldName, targetPath)
if isfield(result, fieldName)
    sourcePath = string(result.(fieldName));
    if strlength(sourcePath) > 0 && exist(sourcePath, "file") == 2
        copyLiveArtifact(sourcePath, targetPath);
    end
end
end

function copyLiveArtifact(sourcePath, targetPath)
sourcePath = string(sourcePath);
targetPath = string(targetPath);
if strlength(sourcePath) == 0 || exist(sourcePath, "file") == 0
    return
end
targetDir = string(fileparts(targetPath));
if exist(targetDir, "dir") ~= 7
    mkdir(targetDir);
end
copyfile(char(sourcePath), char(targetPath), "f");
end

function appendRunLog(paths, line)
timestamp = string(datetime("now", "Format", "yyyy-MM-dd HH:mm:ss z"));
entry = "- " + timestamp + " -- " + string(line) + newline;
if exist(paths.runLogPath, "file") == 2
    previous = string(fileread(paths.runLogPath));
else
    previous = "# Benchmark Run Log" + newline + newline;
end
writeText(paths.runLogPath, previous + entry);
end

function text = joinLines(lines)
text = strjoin(string(lines), newline);
end

function writeJson(path, value)
writeText(path, string(feval('citt.util.jsonEncode', value)));
end

function writeText(path, text)
fid = fopen(char(string(path)), "w");
if fid < 0
    error("CiTT:WriteFailed", "Could not write %s.", string(path));
end
cleanup = onCleanup(@() fclose(fid));
fprintf(fid, "%s", char(string(text)));
end
