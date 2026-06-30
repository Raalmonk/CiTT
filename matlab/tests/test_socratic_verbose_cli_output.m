function test_socratic_verbose_cli_output()
%TEST_SOCRATIC_VERBOSE_CLI_OUTPUT Accept selected CLI logs before final JSON.

repoMatlabRoot = fileparts(fileparts(mfilename("fullpath")));
addpath(repoMatlabRoot);

oldCommand = string(getenv("CITT_AGENT_COMMAND"));
scriptPath = string(tempname) + ".sh";
cleanup = onCleanup(@() restoreEnv(oldCommand, scriptPath));

fid = fopen(scriptPath, "w");
assert(fid > 0);
fprintf(fid, "#!/bin/sh\n");
fprintf(fid, "printf '%%s\\n' 'codex session started'\n");
fprintf(fid, "printf '%%s\\n' '{""id"":""step_01"",""title"":""Teaching step"",""student_question"":""Where is Vout?""}'\n");
fprintf(fid, "printf '%%s\\n' 'codex'\n");
fprintf(fid, "printf '%%s\\n' '{""label"":""uncertain_source_equals_output"",""is_reasonable"":false,""student_level"":""novice"",""misconception"":""Treats Vout as the source voltage."",""next_hint"":""Point to n_vout and name its reference.""}'\n");
fprintf(fid, "printf '%%s\\n' 'tokens used: 1234'\n");
fclose(fid);
fileattrib(scriptPath, "+x");

setenv("CITT_AGENT_COMMAND", char(scriptPath));

step = struct( ...
    "id", "s1", ...
    "focus_id", "fp_vout", ...
    "title", "Output node", ...
    "student_question", "Why is Vout measured at the RC junction?", ...
    "reveal_hint", "Find the node shared by the resistor and capacitor.", ...
    "common_mistake", "Treating the source and output node as identical.", ...
    "concept", "Measured output node");
plan = struct("steps", step);

turn = feval('citt.runSocraticTurn', plan, 1, "I don't know", struct("Action", "hint", "HintLevel", 0));
assert(turn.student_level == "novice");
assert(turn.classification == "uncertain_source_equals_output");
assert(contains(turn.message, "Point to n_vout"));
end

function restoreEnv(oldCommand, scriptPath)
setenv("CITT_AGENT_COMMAND", char(oldCommand));
if exist(scriptPath, "file") == 2
    delete(scriptPath);
end
end
