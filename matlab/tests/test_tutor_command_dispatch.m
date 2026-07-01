function test_tutor_command_dispatch()
%TEST_TUTOR_COMMAND_DISPATCH Verify natural tutor submissions route safely.

addpath(fileparts(fileparts(mfilename("fullpath"))));

emptyState = struct("ModelPath", "", "TeachingPlan", []);

pipeline = feval('citt.dispatchTutorCommand', "Build a 1 kOhm 1 uF RC low-pass lesson", emptyState);
assert(pipeline.action == "run_pipeline");
assert(isfield(pipeline.payload, "prompt"));
assert(contains(pipeline.assistant_preview, "teaching evidence"));

tests = feval('citt.dispatchTutorCommand', "/test", emptyState);
assert(tests.action == "run_model_tests");

review = feval('citt.dispatchTutorCommand', "/review", emptyState);
assert(review.action == "teaching_review");

trace = feval('citt.dispatchTutorCommand', "/trace", emptyState);
assert(trace.action == "learning_traceability");

scenarios = feval('citt.dispatchTutorCommand', "/scenarios", emptyState);
assert(scenarios.action == "simulation_scenarios");

evidence = feval('citt.dispatchTutorCommand', "export evidence", emptyState);
assert(evidence.action == "export_evidence");

measure = feval('citt.dispatchTutorCommand', "measure Vout after the capacitor", emptyState);
assert(measure.action == "run_command");
assert(measure.payload.command == "measure Vout after the capacitor");
assert(measure.payload.probeAsk == "Vout after the capacitor");

teachingState = emptyState;
teachingState.TeachingPlan = struct("steps", struct("step_id", "s1"));
answer = feval('citt.dispatchTutorCommand', "The capacitor voltage cannot jump instantly.", teachingState);
assert(answer.action == "next_hint");
assert(answer.payload.studentAnswer == "The capacitor voltage cannot jump instantly.");
end
