function bundle = loadOfflineBundle(labId)
%LOADOFFLINEBUNDLE Load CiTT bundled JSON artifacts without an API server.

if nargin < 1 || strlength(string(labId)) == 0
    labId = "rc_antialias_adc";
end

root = fileparts(fileparts(mfilename("fullpath")));
exampleDir = fullfile(root, "examples", char(labId));
bundle = struct();
bundle.manifest = jsondecode(fileread(fullfile(exampleDir, "manifest.json")));
bundle.lab_plan = jsondecode(fileread(fullfile(exampleDir, "lab_plan.json")));
bundle.artifact_index = jsondecode(fileread(fullfile(exampleDir, "artifact_index.json")));
bundle.lab_delta_example = jsondecode(fileread(fullfile(exampleDir, "lab_delta_example.json")));
end
