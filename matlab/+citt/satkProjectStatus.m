function status = satkProjectStatus()
%SATKPROJECTSTATUS Inspect the CiTT SATK project policy artifacts.

config = feval('citt.loadConfig');
reusePath = string(fullfile(config.SatkDir, "reuse-libraries.json"));
policyPath = string(fullfile(config.SatkDir, "block-policy.json"));
kgPath = string(fullfile(config.SatkDir, "library-kg", "index.md"));

status = struct();
status.project_root = string(config.SatkProjectRoot);
status.satk_dir = string(config.SatkDir);
status.reuse_libraries_path = reusePath;
status.block_policy_path = policyPath;
status.library_kg_path = kgPath;
status.satk_dir_exists = exist(config.SatkDir, "dir") == 7;
status.reuse_libraries_exists = exist(reusePath, "file") == 2;
status.block_policy_exists = exist(policyPath, "file") == 2;
status.library_kg_exists = exist(kgPath, "file") == 2;
status.confirmed_none = false;
status.ready = false;
status.messages = strings(0, 1);

if status.reuse_libraries_exists
    try
        data = jsondecode(fileread(reusePath));
        status.confirmed_none = logicalField(data, "confirmedNone") || logicalField(data, "confirmed_none");
    catch readError
        status.messages(end + 1) = "Could not parse reuse-libraries.json: " + string(readError.message);
    end
end

status.ready = status.reuse_libraries_exists && status.confirmed_none;
if status.ready
    status.messages(end + 1) = "SATK library gate is satisfied with confirmedNone=true.";
elseif ~status.reuse_libraries_exists
    status.messages(end + 1) = "SATK reuse-libraries.json has not been created for this project.";
else
    status.messages(end + 1) = "SATK reuse-libraries.json exists but confirmedNone=true was not detected.";
end
end

function tf = logicalField(data, fieldName)
tf = false;
if ~isstruct(data) || ~isfield(data, fieldName)
    return
end
raw = data.(char(fieldName));
if islogical(raw)
    tf = raw;
elseif isnumeric(raw)
    tf = raw ~= 0;
elseif isstring(raw) || ischar(raw)
    tf = any(lower(string(raw)) == ["true", "1", "yes"]);
end
end
