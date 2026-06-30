function result = ensureSatkProjectPreset(options)
%ENSURESATKPROJECTPRESET Ensure SATK library gates are satisfied for CiTT.

if nargin < 1 || isempty(options)
    options = struct();
end

config = feval('citt.loadConfig');
projectRoot = string(config.SatkProjectRoot);

result = struct();
result.success = false;
result.project_root = projectRoot;
result.satk_dir = string(config.SatkDir);
result.mode = "confirmed_no_custom_libraries";
result.reuse_libraries_path = string(fullfile(result.satk_dir, "reuse-libraries.json"));
result.messages = strings(0, 1);

if exist(result.satk_dir, "dir") ~= 7
    mkdir(result.satk_dir);
end

try
    library.LibraryConfig.save(projectRoot, [], struct("confirmedNone", true));
    result.messages(end + 1) = "Saved SATK library config with confirmedNone=true via library.LibraryConfig.save.";
catch apiError
    result.messages(end + 1) = "SATK library API unavailable: " + string(apiError.message);
    result.messages(end + 1) = "Manual fallback is not preferred; run satk_initialize and retry.";
    if optionFlag(options, "AllowMissingApi", false)
        result.status = "api_unavailable";
        return
    end
    error("CiTT:SatkLibraryApiMissing", ...
        "Could not create SATK library preset through SATK API. Run satk_initialize first. Details: %s", ...
        apiError.message);
end

result.success = exist(result.reuse_libraries_path, "file") == 2;
if result.success
    result.status = "ready";
else
    result.status = "missing_reuse_libraries_json";
    result.messages(end + 1) = "SATK API returned without creating .satk/reuse-libraries.json.";
end
end

function value = optionFlag(options, fieldName, defaultValue)
value = logical(defaultValue);
if isstruct(options) && isfield(options, fieldName)
    value = logical(options.(fieldName));
end
end
