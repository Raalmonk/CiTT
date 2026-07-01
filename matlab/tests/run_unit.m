function results = run_unit()
%RUN_UNIT Run CiTT tests that do not require Simulink or external agents.

testRoot = fileparts(mfilename("fullpath"));
addpath(testRoot);
addpath(fileparts(testRoot));
testFiles = {
    "test_real_config"
    "test_agent_task_generation"
    "test_cli_only_contract"
    "test_text_prompt_build_readiness"
    "test_socratic_student_level_contract"
    "test_socratic_verbose_cli_output"
    "test_tutor_turn_planner_contract"
    "test_teaching_plan_contract"
    "test_lab_delta"
    "test_evidence_pack_export"
    "test_competition_feature_pack"
    "test_satk_teaching_evidence_layer"
    "test_tutor_command_dispatch"
    "test_html_app_surface_contract"
    "test_snapshot_crop_contract"
};

results = run_named_tests(testFiles, "unit");
end
