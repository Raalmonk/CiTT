function checks = defineTeachingModelChecks()
%DEFINETEACHINGMODELCHECKS Return CiTT teaching-model check definitions.

checks = [
    item("CITT_CHECK_001", "Simscape physical network exists")
    item("CITT_CHECK_002", "Solver Configuration exists")
    item("CITT_CHECK_003", "Electrical Reference exists")
    item("CITT_CHECK_004", "Every requested output has a probe map entry")
    item("CITT_CHECK_005", "Every focus map block_path exists in the model")
    item("CITT_CHECK_006", "Every probe map block_path exists in the model")
    item("CITT_CHECK_007", "Every teaching focus has a measurable evidence path")
    item("CITT_CHECK_008", "Generated model has a signal-level test interface if model_test is required")
];
end

function value = item(id, title)
value = struct("id", string(id), "title", string(title), "auto_fix", false);
end
