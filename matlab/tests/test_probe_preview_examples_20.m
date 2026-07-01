function test_probe_preview_examples_20()
%TEST_PROBE_PREVIEW_EXAMPLES_20 Exercise natural probe commands across domains.

config = feval('citt.loadConfig');
modelName = "citt_test_probe_preview_20";
modelPath = fullfile(config.WorkDir, modelName + ".slx");
probePath = fullfile(config.WorkDir, "test_probe_preview_examples_20.json");

cleanupArtifacts(modelName, modelPath, probePath);
cleanup = onCleanup(@() cleanupArtifacts(modelName, modelPath, probePath));

new_system(modelName);
probeEntries = createProbeModel(modelName);
save_system(modelName, modelPath);
writeJson(probePath, probeEntries);

state = feval('citt.appState');
state.ModelPath = string(modelPath);
state.SpecPath = "";
state.ProbeMapPath = string(probePath);

examples = [
    example("measure concentration signal", "PR_CONCENTRATION")
    example("probe analyte concentration C(t)", "PR_CONCENTRATION")
    example("测量 浓度", "PR_CONCENTRATION")
    example("scope lagged concentration after membrane", "PR_LAGGED_CONCENTRATION")
    example("measure membrane lag concentration", "PR_LAGGED_CONCENTRATION")
    example("测量 膜 后 滞后 浓度", "PR_LAGGED_CONCENTRATION")
    example("measure sensor current", "PR_SENSOR_CURRENT")
    example("probe faradaic current output", "PR_SENSOR_CURRENT")
    example("测量 传感器 电流", "PR_SENSOR_CURRENT")
    example("measure TIA output voltage", "PR_TIA_OUTPUT")
    example("probe transimpedance amplifier output", "PR_TIA_OUTPUT")
    example("测量 跨阻 放大 输出 电压", "PR_TIA_OUTPUT")
    example("measure ADC code", "PR_ADC_CODE")
    example("probe digital converter code", "PR_ADC_CODE")
    example("测量 ADC 数字 代码", "PR_ADC_CODE")
    example("measure settling error", "PR_SETTLING_ERROR")
    example("probe final settling error voltage", "PR_SETTLING_ERROR")
    example("测量 稳定 误差", "PR_SETTLING_ERROR")
    example("scope lagged concentration", "PR_LAGGED_CONCENTRATION")
    example("观察 PK 浓度", "PR_CONCENTRATION")
];

assert(numel(examples) == 20, "This regression must keep exactly 20 student examples.");

for i = 1:numel(examples)
    started = tic;
    result = feval('citt.runNaturalCommand', examples(i).phrase, state);
    elapsed = toc(started);

    assert(result.action == "measure", "Example %d did not route to measure.", i);
    assert(result.success, "Example %d failed: %s", i, examples(i).phrase);
    assert(elapsed < 5, "Example %d took too long and may have run simulation.", i);
    assert(isfield(result.details, "target_id"), "Example %d did not return a target id.", i);
    assert(string(result.details.target_id) == examples(i).expected, ...
        "Example %d routed '%s' to %s, expected %s.", ...
        i, examples(i).phrase, string(result.details.target_id), examples(i).expected);
    assert(isfield(result.details, "measurement"), "Example %d has no measurement summary.", i);
    assert(~result.details.measurement.success, "Example %d should stay preview-only.", i);
    assert(contains(result.details.measurement.message, "Preview-only measurement target matched"), ...
        "Example %d did not explain preview-only measurement.", i);
    assert(strlength(string(result.details.measurement.block_path)) > 0, ...
        "Example %d did not expose the matched block path.", i);
end
end

function probes = createProbeModel(modelName)
blocks = [
    block("PR_CONCENTRATION", "PK concentration C(t)", "concentration", "mg/L", "concentration_signal")
    block("PR_LAGGED_CONCENTRATION", "membrane lagged concentration", "lagged concentration after membrane", "mg/L", "lagged_concentration")
    block("PR_SENSOR_CURRENT", "sensor current output", "faradaic sensor current", "A", "sensor_current")
    block("PR_TIA_OUTPUT", "TIA output voltage", "transimpedance amplifier output voltage", "V", "tia_output_voltage")
    block("PR_ADC_CODE", "ADC output code", "ADC digital code after quantizer", "count", "ADC1_12_bit_quantizer")
    block("PR_SETTLING_ERROR", "settling error voltage", "settling error", "V", "settling_error")
];

probes = repmat(struct( ...
    "probe_id", "", ...
    "focus_id", "", ...
    "label", "", ...
    "target_type", "Simulink signal", ...
    "model_paths", {{}}, ...
    "block_paths", {{}}, ...
    "quantity", "", ...
    "unit", "", ...
    "suggested_sensor_or_logging", "Use the existing local signal for preview.", ...
    "instructions", "Preview only; do not run simulation."), numel(blocks), 1);

for i = 1:numel(blocks)
    sourcePath = char(modelName + "/" + blocks(i).blockName);
    sinkName = "sink_" + string(i);
    sinkPath = char(modelName + "/" + sinkName);
    add_block("simulink/Sources/Constant", sourcePath, "Value", num2str(i));
    add_block("simulink/Sinks/Terminator", sinkPath);
    add_line(modelName, blocks(i).blockName + "/1", sinkName + "/1");

    probes(i).probe_id = char(blocks(i).probeId);
    probes(i).focus_id = char("FP_" + erase(blocks(i).probeId, "PR_"));
    probes(i).label = char(blocks(i).label);
    probes(i).model_paths = {char(modelName)};
    probes(i).block_paths = {sourcePath};
    probes(i).quantity = char(blocks(i).quantity);
    probes(i).unit = char(blocks(i).unit);
    if blocks(i).probeId == "PR_SENSOR_CURRENT"
        probes(i).suggested_sensor_or_logging = "Current Sensor plus PS-Simulink Converter and To Workspace";
    end
end
end

function value = block(probeId, label, quantity, unit, blockName)
value = struct( ...
    "probeId", string(probeId), ...
    "label", string(label), ...
    "quantity", string(quantity), ...
    "unit", string(unit), ...
    "blockName", string(blockName));
end

function value = example(phrase, expected)
value = struct("phrase", string(phrase), "expected", string(expected));
end

function writeJson(path, value)
fid = fopen(path, "w");
assert(fid > 0, "Could not write probe example JSON.");
cleaner = onCleanup(@() fclose(fid));
fprintf(fid, "%s", jsonencode(value, "PrettyPrint", true));
clear cleaner
end

function cleanupArtifacts(modelName, modelPath, probePath)
if bdIsLoaded(modelName)
    close_system(modelName, 0);
end
if exist(modelPath, "file") == 2
    delete(modelPath);
end
if exist(probePath, "file") == 2
    delete(probePath);
end
end
