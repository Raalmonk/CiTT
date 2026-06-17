# Tutor 100-Case QA

Generated locally from supported `CircuitProblem` families. This exercises the lesson planner as if Gemini were producing step-by-step tutor moves, then scores the returned lesson for visual grounding, graph lens, reveal timing, and source-of-truth safety.

## Summary

- Cases: 100
- Solved PASS: 100
- Average tutor score: 9.8/10
- Minimum tutor score: 8/10

## Family Scores

- bme:bme_anti_aliasing_low_pass: 10/10 across 1 cases
- bme:bme_anti_aliasing_low_pass:value_variant: 10/10 across 1 cases
- bme:bme_ecg_front_end: 10/10 across 1 cases
- bme:bme_ecg_front_end:value_variant: 10/10 across 1 cases
- bme:bme_emg_band_pass_chain: 10/10 across 1 cases
- bme:bme_emg_band_pass_chain:value_variant: 10/10 across 1 cases
- bme:bme_instrumentation_amplifier: 10/10 across 1 cases
- bme:bme_instrumentation_amplifier:value_variant: 10/10 across 1 cases
- bme:bme_photodiode_tia: 10/10 across 1 cases
- bme:bme_photodiode_tia:value_variant: 10/10 across 1 cases
- bridge: 10/10 across 20 cases
- current_divider: 10/10 across 15 cases
- generic_dc: 10/10 across 10 cases
- rc_low_pass_ac: 10/10 across 15 cases
- rc_transient: 8/10 across 10 cases
- voltage_divider: 10/10 across 20 cases

## Gemini-Role Sample Decompositions

### 001. qa_voltage_divider_01 (voltage_divider)

- Expected lens: divider
- Score: 10/10
- Steps: divider_reference, divider_series_path, divider_output, verification_boundary
- Self-eval: no blocking QA issues

### 021. qa_current_divider_01 (current_divider)

- Expected lens: current_divider
- Score: 10/10
- Steps: current_divider_source, current_divider_parallel_branches, current_divider_requested_values, verification_boundary
- Self-eval: no blocking QA issues

### 036. qa_bridge_01 (bridge)

- Expected lens: coupled_nodes
- Score: 10/10
- Steps: dc_sources_and_ground, dc_coupled_node_map, dc_target_kcl_neighborhood, dc_requested_answer, verification_boundary
- Self-eval: no blocking QA issues

### 056. qa_generic_dc_01 (generic_dc)

- Expected lens: node_relationships
- Score: 10/10
- Steps: dc_sources_and_ground, dc_node_relationships, dc_target_neighborhood, dc_requested_answer, verification_boundary
- Self-eval: no blocking QA issues

### 066. qa_rc_low_pass_01 (rc_low_pass_ac)

- Expected lens: ac_low_pass
- Score: 10/10
- Steps: ac_source_frequency, ac_low_pass_pole, ac_output_phasor, verification_boundary
- Self-eval: no blocking QA issues

### 081. qa_rc_transient_01 (rc_transient)

- Expected lens: rc_transient
- Score: 8/10
- Steps: rc_initial_condition, rc_final_value, rc_time_constant, rc_exponential_motion, verification_boundary
- Self-eval: early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage

### 091. bme_anti_aliasing_low_pass (bme:bme_anti_aliasing_low_pass)

- Expected lens: ac_low_pass
- Score: 10/10
- Steps: ac_source_frequency, ac_low_pass_pole, ac_output_phasor, bme_context_boundary, verification_boundary
- Self-eval: no blocking QA issues

## Weakest Cases

- 081 `qa_rc_transient_01` [rc_transient], score 8: early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 082 `qa_rc_transient_02` [rc_transient], score 8: early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 083 `qa_rc_transient_03` [rc_transient], score 8: early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 084 `qa_rc_transient_04` [rc_transient], score 8: early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 085 `qa_rc_transient_05` [rc_transient], score 8: early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 086 `qa_rc_transient_06` [rc_transient], score 8: early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 087 `qa_rc_transient_07` [rc_transient], score 8: early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 088 `qa_rc_transient_08` [rc_transient], score 8: early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 089 `qa_rc_transient_09` [rc_transient], score 8: early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 090 `qa_rc_transient_10` [rc_transient], score 8: early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 091 `bme_anti_aliasing_low_pass` [bme:bme_anti_aliasing_low_pass], score 10: no issues
- 092 `bme_anti_aliasing_low_pass_higher_cutoff` [bme:bme_anti_aliasing_low_pass:value_variant], score 10: no issues

## Improvement Backlog

- Add explicit student_prompt and hint_ladder fields to TutorStep so Socratic behavior is first-class instead of implied by prose.
- Add reveal_policy per step; the current schema can show verified values, but it cannot encode when the UI should reveal them.
- Use OptCPV artifact bboxes to split overly broad focus regions before playback on dense circuits.
- Promote AnalysisView KCL terms into lesson steps for generic DC and bridge cases, so node equations can be rendered branch-by-branch.
- Gate requested values until after the target reference and sign convention have been discussed.

## Full Case Index

- 001 `qa_voltage_divider_01` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 002 `qa_voltage_divider_02` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 003 `qa_voltage_divider_03` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 004 `qa_voltage_divider_04` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 005 `qa_voltage_divider_05` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 006 `qa_voltage_divider_06` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 007 `qa_voltage_divider_07` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 008 `qa_voltage_divider_08` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 009 `qa_voltage_divider_09` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 010 `qa_voltage_divider_10` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 011 `qa_voltage_divider_11` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 012 `qa_voltage_divider_12` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 013 `qa_voltage_divider_13` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 014 `qa_voltage_divider_14` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 015 `qa_voltage_divider_15` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 016 `qa_voltage_divider_16` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 017 `qa_voltage_divider_17` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 018 `qa_voltage_divider_18` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 019 `qa_voltage_divider_19` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 020 `qa_voltage_divider_20` [voltage_divider] score=10 steps=4 lens=divider issues=ok
- 021 `qa_current_divider_01` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 022 `qa_current_divider_02` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 023 `qa_current_divider_03` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 024 `qa_current_divider_04` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 025 `qa_current_divider_05` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 026 `qa_current_divider_06` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 027 `qa_current_divider_07` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 028 `qa_current_divider_08` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 029 `qa_current_divider_09` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 030 `qa_current_divider_10` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 031 `qa_current_divider_11` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 032 `qa_current_divider_12` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 033 `qa_current_divider_13` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 034 `qa_current_divider_14` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 035 `qa_current_divider_15` [current_divider] score=10 steps=4 lens=current_divider issues=ok
- 036 `qa_bridge_01` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 037 `qa_bridge_02` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 038 `qa_bridge_03` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 039 `qa_bridge_04` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 040 `qa_bridge_05` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 041 `qa_bridge_06` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 042 `qa_bridge_07` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 043 `qa_bridge_08` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 044 `qa_bridge_09` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 045 `qa_bridge_10` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 046 `qa_bridge_11` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 047 `qa_bridge_12` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 048 `qa_bridge_13` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 049 `qa_bridge_14` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 050 `qa_bridge_15` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 051 `qa_bridge_16` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 052 `qa_bridge_17` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 053 `qa_bridge_18` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 054 `qa_bridge_19` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 055 `qa_bridge_20` [bridge] score=10 steps=5 lens=coupled_nodes issues=ok
- 056 `qa_generic_dc_01` [generic_dc] score=10 steps=5 lens=node_relationships issues=ok
- 057 `qa_generic_dc_02` [generic_dc] score=10 steps=5 lens=node_relationships issues=ok
- 058 `qa_generic_dc_03` [generic_dc] score=10 steps=5 lens=node_relationships issues=ok
- 059 `qa_generic_dc_04` [generic_dc] score=10 steps=5 lens=node_relationships issues=ok
- 060 `qa_generic_dc_05` [generic_dc] score=10 steps=5 lens=node_relationships issues=ok
- 061 `qa_generic_dc_06` [generic_dc] score=10 steps=5 lens=node_relationships issues=ok
- 062 `qa_generic_dc_07` [generic_dc] score=10 steps=5 lens=node_relationships issues=ok
- 063 `qa_generic_dc_08` [generic_dc] score=10 steps=5 lens=node_relationships issues=ok
- 064 `qa_generic_dc_09` [generic_dc] score=10 steps=5 lens=node_relationships issues=ok
- 065 `qa_generic_dc_10` [generic_dc] score=10 steps=5 lens=node_relationships issues=ok
- 066 `qa_rc_low_pass_01` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 067 `qa_rc_low_pass_02` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 068 `qa_rc_low_pass_03` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 069 `qa_rc_low_pass_04` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 070 `qa_rc_low_pass_05` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 071 `qa_rc_low_pass_06` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 072 `qa_rc_low_pass_07` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 073 `qa_rc_low_pass_08` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 074 `qa_rc_low_pass_09` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 075 `qa_rc_low_pass_10` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 076 `qa_rc_low_pass_11` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 077 `qa_rc_low_pass_12` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 078 `qa_rc_low_pass_13` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 079 `qa_rc_low_pass_14` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 080 `qa_rc_low_pass_15` [rc_low_pass_ac] score=10 steps=4 lens=ac_low_pass issues=ok
- 081 `qa_rc_transient_01` [rc_transient] score=8 steps=5 lens=rc_transient issues=early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 082 `qa_rc_transient_02` [rc_transient] score=8 steps=5 lens=rc_transient issues=early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 083 `qa_rc_transient_03` [rc_transient] score=8 steps=5 lens=rc_transient issues=early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 084 `qa_rc_transient_04` [rc_transient] score=8 steps=5 lens=rc_transient issues=early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 085 `qa_rc_transient_05` [rc_transient] score=8 steps=5 lens=rc_transient issues=early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 086 `qa_rc_transient_06` [rc_transient] score=8 steps=5 lens=rc_transient issues=early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 087 `qa_rc_transient_07` [rc_transient] score=8 steps=5 lens=rc_transient issues=early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 088 `qa_rc_transient_08` [rc_transient] score=8 steps=5 lens=rc_transient issues=early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 089 `qa_rc_transient_09` [rc_transient] score=8 steps=5 lens=rc_transient issues=early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 090 `qa_rc_transient_10` [rc_transient] score=8 steps=5 lens=rc_transient issues=early answer reveal: rc_initial_condition: initial_capacitor_voltage; rc_final_value: final_capacitor_voltage
- 091 `bme_anti_aliasing_low_pass` [bme:bme_anti_aliasing_low_pass] score=10 steps=5 lens=ac_low_pass issues=ok
- 092 `bme_anti_aliasing_low_pass_higher_cutoff` [bme:bme_anti_aliasing_low_pass:value_variant] score=10 steps=5 lens=ac_low_pass issues=ok
- 093 `bme_ecg_front_end` [bme:bme_ecg_front_end] score=10 steps=5 lens=differential_amp issues=ok
- 094 `bme_ecg_front_end_larger_differential_signal` [bme:bme_ecg_front_end:value_variant] score=10 steps=5 lens=differential_amp issues=ok
- 095 `bme_emg_band_pass_chain` [bme:bme_emg_band_pass_chain] score=10 steps=4 lens=ac_low_pass issues=ok
- 096 `bme_emg_band_pass_chain_higher_high_pass_corner` [bme:bme_emg_band_pass_chain:value_variant] score=10 steps=4 lens=ac_low_pass issues=ok
- 097 `bme_instrumentation_amplifier` [bme:bme_instrumentation_amplifier] score=10 steps=6 lens=bme issues=ok
- 098 `bme_instrumentation_amplifier_rg_gets_smaller` [bme:bme_instrumentation_amplifier:value_variant] score=10 steps=6 lens=bme issues=ok
- 099 `bme_photodiode_tia` [bme:bme_photodiode_tia] score=10 steps=5 lens=transimpedance issues=ok
- 100 `bme_photodiode_tia_photocurrent_doubles` [bme:bme_photodiode_tia:value_variant] score=10 steps=5 lens=transimpedance issues=ok
