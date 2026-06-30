function test_socratic_student_level_contract()
%TEST_SOCRATIC_STUDENT_LEVEL_CONTRACT Verify CLI Socratic output drives level-aware feedback.

repoMatlabRoot = fileparts(fileparts(mfilename("fullpath")));
addpath(repoMatlabRoot);

oldCommand = string(getenv("CITT_AGENT_COMMAND"));
scriptPath = string(tempname) + ".sh";
cleanup = onCleanup(@() restoreEnv(oldCommand, scriptPath));

fid = fopen(scriptPath, "w");
assert(fid > 0);
fprintf(fid, "#!/bin/sh\n");
fprintf(fid, "printf '%%s\\n' '{""label"":""partial"",""is_reasonable"":false,""student_level"":""novice"",""misconception"":""missing reference node"",""next_hint"":""Name the node and reference.""}'\n");
fclose(fid);
fileattrib(scriptPath, "+x");

setenv("CITT_AGENT_COMMAND", char(scriptPath));

step = struct( ...
    "id", "s1", ...
    "focus_id", "fp_vout", ...
    "title", "Output node", ...
    "student_question", "What should happen at Vout relative to electrical reference?", ...
    "reveal_hint", "Look for the Vout probe and its reference node.", ...
    "common_mistake", "Treating every nearby node as the same reference.", ...
    "concept", "Measured output node");
plan = struct("steps", step);

turn = feval('citt.runSocraticTurn', plan, 1, "idk", struct("Action", "hint", "HintLevel", 0));
assert(turn.student_level == "novice");
assert(contains(turn.message, "Level: novice"));
assert(contains(turn.message, "Name the node and reference."));
end

function restoreEnv(oldCommand, scriptPath)
setenv("CITT_AGENT_COMMAND", char(oldCommand));
if exist(scriptPath, "file") == 2
    delete(scriptPath);
end
end
