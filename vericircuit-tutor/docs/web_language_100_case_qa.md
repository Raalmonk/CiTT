# Web-Sourced Human-Language 100-Case QA

These cases are source-backed paraphrases: each prompt is written in our own words, with a public source URL recording the worksheet or article pattern it was based on. The benchmark tests natural-language circuit generation intent, not copied textbook wording.

## Summary

- Cases: 100
- Expected-IR solver/lesson average score: 9.8/10
- Expected-IR minimum score: 8/10
- Live parser mode: not run
- Live parser cases run: 0
- Live parser cases passed: 0

To run the live human-language parser path, set `GEMINI_API_KEY` or `GOOGLE_API_KEY` and run:

```bash
python backend/scripts/run_web_language_100_case_qa.py --parser-mode gemini_strict --markdown docs/web_language_100_case_qa.md
```

## Source Families

- [All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/): Worksheet includes voltage divider calculation/design prompts.
- [All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/): Worksheet asks students to draw, construct, and mathematically analyze current-divider circuits.
- [All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/): Worksheet covers two-divider/bridge midpoint voltages and differential bridge readings.
- [All About Circuits: Kirchhoff's Laws Worksheet](https://www.allaboutcircuits.com/worksheets/kirchhoffs-laws/): Worksheet emphasizes meter readings, signed voltages, and KCL/KVL reasoning in DC networks.
- [All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/): Worksheet includes AC impedance and frequency-domain circuit exercises.
- [All About Circuits: Time Constant Calculations Worksheet](https://www.allaboutcircuits.com/worksheets/time-constant-calculations/): Worksheet covers RC time constants and transient calculations.
- [All About Circuits: Inverting and Noninverting OpAmp Voltage Amplifier Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/inverting-and-noninverting-opamp-voltage-amplifier-circuits/): Worksheet asks students to draw schematics and analyze ideal op-amp voltage amplifier values.
- [Electronics Tutorials: Instrumentation Amplifier](https://www.electronics-tutorials.ws/opamp/instrumentation-amplifier.html): Article explains instrumentation amplifier topology and worked examples.
- [RP Photonics: Photodiode Amplifiers](https://www.rp-photonics.com/photodiode_amplifiers.html): Article describes photodiode transimpedance amplifiers converting photocurrent into voltage.

## Sample Natural-Language Inputs

### 001. qa_voltage_divider_01

- Source: [All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/)
- Expected lens: divider
- Prompt: Generate a circuit model from this description, not just a numeric answer: a 6.5 V DC source has its positive terminal at vin_1 and negative terminal at ground 0. Rtop1 = 1.25 kOhm connects vin_1 to sense_1, and Rbot1 = 1.9 kOhm connects sense_1 to 0. Create the Circuit IR/schematic focus and request voltage across Rbot1 from sense_1 to 0.
- Expected path steps: divider_reference, divider_series_path, divider_output, verification_boundary

### 002. qa_voltage_divider_02

- Source: [All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/)
- Expected lens: divider
- Prompt: Generate a circuit model from this description, not just a numeric answer: a 8 V DC source has its positive terminal at vin_2 and negative terminal at ground 0. Rtop2 = 1.5 kOhm connects vin_2 to sense_2, and Rbot2 = 2.3 kOhm connects sense_2 to 0. Create the Circuit IR/schematic focus and request current through Rtop2 from vin_2 to sense_2.
- Expected path steps: divider_reference, divider_series_path, divider_output, verification_boundary

### 003. qa_voltage_divider_03

- Source: [All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/)
- Expected lens: divider
- Prompt: Generate a circuit model from this description, not just a numeric answer: a 9.5 V DC source has its positive terminal at vin_3 and negative terminal at ground gnd. Rtop3 = 1.75 kOhm connects vin_3 to sense_3, and Rbot3 = 2.7 kOhm connects sense_3 to gnd. Create the Circuit IR/schematic focus and request signed power for Rbot3.
- Expected path steps: divider_reference, divider_series_path, divider_output, verification_boundary

### 004. qa_voltage_divider_04

- Source: [All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/)
- Expected lens: divider
- Prompt: Generate a circuit model from this description, not just a numeric answer: a 11 V DC source has its positive terminal at vin_4 and negative terminal at ground 0. Rtop4 = 2 kOhm connects vin_4 to sense_4, and Rbot4 = 3.1 kOhm connects sense_4 to 0. Create the Circuit IR/schematic focus and request node voltage at sense_4 relative to 0.
- Expected path steps: divider_reference, divider_series_path, divider_output, verification_boundary

### 005. qa_voltage_divider_05

- Source: [All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/)
- Expected lens: divider
- Prompt: Generate a circuit model from this description, not just a numeric answer: a 5 V DC source has its positive terminal at vin_5 and negative terminal at ground 0. Rtop5 = 2.25 kOhm connects vin_5 to sense_5, and Rbot5 = 3.5 kOhm connects sense_5 to 0. Create the Circuit IR/schematic focus and request voltage across Rbot5 from sense_5 to 0.
- Expected path steps: divider_reference, divider_series_path, divider_output, verification_boundary

### 006. qa_voltage_divider_06

- Source: [All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/)
- Expected lens: divider
- Prompt: Generate a circuit model from this description, not just a numeric answer: a 6.5 V DC source has its positive terminal at vin_6 and negative terminal at ground gnd. Rtop6 = 2.5 kOhm connects vin_6 to sense_6, and Rbot6 = 1.5 kOhm connects sense_6 to gnd. Create the Circuit IR/schematic focus and request current through Rtop6 from vin_6 to sense_6.
- Expected path steps: divider_reference, divider_series_path, divider_output, verification_boundary

### 007. qa_voltage_divider_07

- Source: [All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/)
- Expected lens: divider
- Prompt: Generate a circuit model from this description, not just a numeric answer: a 8 V DC source has its positive terminal at vin_7 and negative terminal at ground 0. Rtop7 = 1 kOhm connects vin_7 to sense_7, and Rbot7 = 1.9 kOhm connects sense_7 to 0. Create the Circuit IR/schematic focus and request signed power for Rbot7.
- Expected path steps: divider_reference, divider_series_path, divider_output, verification_boundary

### 008. qa_voltage_divider_08

- Source: [All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/)
- Expected lens: divider
- Prompt: Generate a circuit model from this description, not just a numeric answer: a 9.5 V DC source has its positive terminal at vin_8 and negative terminal at ground 0. Rtop8 = 1.25 kOhm connects vin_8 to sense_8, and Rbot8 = 2.3 kOhm connects sense_8 to 0. Create the Circuit IR/schematic focus and request node voltage at sense_8 relative to 0.
- Expected path steps: divider_reference, divider_series_path, divider_output, verification_boundary

## Full 100-Case Index

- 001 `qa_voltage_divider_01` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 002 `qa_voltage_divider_02` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 003 `qa_voltage_divider_03` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 004 `qa_voltage_divider_04` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 005 `qa_voltage_divider_05` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 006 `qa_voltage_divider_06` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 007 `qa_voltage_divider_07` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 008 `qa_voltage_divider_08` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 009 `qa_voltage_divider_09` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 010 `qa_voltage_divider_10` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 011 `qa_voltage_divider_11` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 012 `qa_voltage_divider_12` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 013 `qa_voltage_divider_13` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 014 `qa_voltage_divider_14` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 015 `qa_voltage_divider_15` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 016 `qa_voltage_divider_16` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 017 `qa_voltage_divider_17` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 018 `qa_voltage_divider_18` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 019 `qa_voltage_divider_19` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 020 `qa_voltage_divider_20` [voltage_divider] source=[All About Circuits: Voltage Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/voltage-divider-circuits/) expected_score=10 parser=not_run
- 021 `qa_current_divider_01` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 022 `qa_current_divider_02` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 023 `qa_current_divider_03` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 024 `qa_current_divider_04` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 025 `qa_current_divider_05` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 026 `qa_current_divider_06` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 027 `qa_current_divider_07` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 028 `qa_current_divider_08` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 029 `qa_current_divider_09` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 030 `qa_current_divider_10` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 031 `qa_current_divider_11` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 032 `qa_current_divider_12` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 033 `qa_current_divider_13` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 034 `qa_current_divider_14` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 035 `qa_current_divider_15` [current_divider] source=[All About Circuits: Current Divider Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/current-divider-circuits/) expected_score=10 parser=not_run
- 036 `qa_bridge_01` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 037 `qa_bridge_02` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 038 `qa_bridge_03` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 039 `qa_bridge_04` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 040 `qa_bridge_05` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 041 `qa_bridge_06` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 042 `qa_bridge_07` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 043 `qa_bridge_08` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 044 `qa_bridge_09` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 045 `qa_bridge_10` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 046 `qa_bridge_11` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 047 `qa_bridge_12` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 048 `qa_bridge_13` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 049 `qa_bridge_14` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 050 `qa_bridge_15` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 051 `qa_bridge_16` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 052 `qa_bridge_17` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 053 `qa_bridge_18` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 054 `qa_bridge_19` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 055 `qa_bridge_20` [bridge] source=[All About Circuits: DC Bridge Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/dc-bridge-circuits/) expected_score=10 parser=not_run
- 056 `qa_generic_dc_01` [generic_dc] source=[All About Circuits: Kirchhoff's Laws Worksheet](https://www.allaboutcircuits.com/worksheets/kirchhoffs-laws/) expected_score=10 parser=not_run
- 057 `qa_generic_dc_02` [generic_dc] source=[All About Circuits: Kirchhoff's Laws Worksheet](https://www.allaboutcircuits.com/worksheets/kirchhoffs-laws/) expected_score=10 parser=not_run
- 058 `qa_generic_dc_03` [generic_dc] source=[All About Circuits: Kirchhoff's Laws Worksheet](https://www.allaboutcircuits.com/worksheets/kirchhoffs-laws/) expected_score=10 parser=not_run
- 059 `qa_generic_dc_04` [generic_dc] source=[All About Circuits: Kirchhoff's Laws Worksheet](https://www.allaboutcircuits.com/worksheets/kirchhoffs-laws/) expected_score=10 parser=not_run
- 060 `qa_generic_dc_05` [generic_dc] source=[All About Circuits: Kirchhoff's Laws Worksheet](https://www.allaboutcircuits.com/worksheets/kirchhoffs-laws/) expected_score=10 parser=not_run
- 061 `qa_generic_dc_06` [generic_dc] source=[All About Circuits: Kirchhoff's Laws Worksheet](https://www.allaboutcircuits.com/worksheets/kirchhoffs-laws/) expected_score=10 parser=not_run
- 062 `qa_generic_dc_07` [generic_dc] source=[All About Circuits: Kirchhoff's Laws Worksheet](https://www.allaboutcircuits.com/worksheets/kirchhoffs-laws/) expected_score=10 parser=not_run
- 063 `qa_generic_dc_08` [generic_dc] source=[All About Circuits: Kirchhoff's Laws Worksheet](https://www.allaboutcircuits.com/worksheets/kirchhoffs-laws/) expected_score=10 parser=not_run
- 064 `qa_generic_dc_09` [generic_dc] source=[All About Circuits: Kirchhoff's Laws Worksheet](https://www.allaboutcircuits.com/worksheets/kirchhoffs-laws/) expected_score=10 parser=not_run
- 065 `qa_generic_dc_10` [generic_dc] source=[All About Circuits: Kirchhoff's Laws Worksheet](https://www.allaboutcircuits.com/worksheets/kirchhoffs-laws/) expected_score=10 parser=not_run
- 066 `qa_rc_low_pass_01` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 067 `qa_rc_low_pass_02` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 068 `qa_rc_low_pass_03` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 069 `qa_rc_low_pass_04` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 070 `qa_rc_low_pass_05` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 071 `qa_rc_low_pass_06` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 072 `qa_rc_low_pass_07` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 073 `qa_rc_low_pass_08` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 074 `qa_rc_low_pass_09` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 075 `qa_rc_low_pass_10` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 076 `qa_rc_low_pass_11` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 077 `qa_rc_low_pass_12` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 078 `qa_rc_low_pass_13` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 079 `qa_rc_low_pass_14` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 080 `qa_rc_low_pass_15` [rc_low_pass_ac] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 081 `qa_rc_transient_01` [rc_transient] source=[All About Circuits: Time Constant Calculations Worksheet](https://www.allaboutcircuits.com/worksheets/time-constant-calculations/) expected_score=8 parser=not_run
- 082 `qa_rc_transient_02` [rc_transient] source=[All About Circuits: Time Constant Calculations Worksheet](https://www.allaboutcircuits.com/worksheets/time-constant-calculations/) expected_score=8 parser=not_run
- 083 `qa_rc_transient_03` [rc_transient] source=[All About Circuits: Time Constant Calculations Worksheet](https://www.allaboutcircuits.com/worksheets/time-constant-calculations/) expected_score=8 parser=not_run
- 084 `qa_rc_transient_04` [rc_transient] source=[All About Circuits: Time Constant Calculations Worksheet](https://www.allaboutcircuits.com/worksheets/time-constant-calculations/) expected_score=8 parser=not_run
- 085 `qa_rc_transient_05` [rc_transient] source=[All About Circuits: Time Constant Calculations Worksheet](https://www.allaboutcircuits.com/worksheets/time-constant-calculations/) expected_score=8 parser=not_run
- 086 `qa_rc_transient_06` [rc_transient] source=[All About Circuits: Time Constant Calculations Worksheet](https://www.allaboutcircuits.com/worksheets/time-constant-calculations/) expected_score=8 parser=not_run
- 087 `qa_rc_transient_07` [rc_transient] source=[All About Circuits: Time Constant Calculations Worksheet](https://www.allaboutcircuits.com/worksheets/time-constant-calculations/) expected_score=8 parser=not_run
- 088 `qa_rc_transient_08` [rc_transient] source=[All About Circuits: Time Constant Calculations Worksheet](https://www.allaboutcircuits.com/worksheets/time-constant-calculations/) expected_score=8 parser=not_run
- 089 `qa_rc_transient_09` [rc_transient] source=[All About Circuits: Time Constant Calculations Worksheet](https://www.allaboutcircuits.com/worksheets/time-constant-calculations/) expected_score=8 parser=not_run
- 090 `qa_rc_transient_10` [rc_transient] source=[All About Circuits: Time Constant Calculations Worksheet](https://www.allaboutcircuits.com/worksheets/time-constant-calculations/) expected_score=8 parser=not_run
- 091 `bme_anti_aliasing_low_pass` [bme:bme_anti_aliasing_low_pass] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 092 `bme_anti_aliasing_low_pass_higher_cutoff` [bme:bme_anti_aliasing_low_pass:value_variant] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 093 `bme_ecg_front_end` [bme:bme_ecg_front_end] source=[All About Circuits: Inverting and Noninverting OpAmp Voltage Amplifier Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/inverting-and-noninverting-opamp-voltage-amplifier-circuits/) expected_score=10 parser=not_run
- 094 `bme_ecg_front_end_larger_differential_signal` [bme:bme_ecg_front_end:value_variant] source=[All About Circuits: Inverting and Noninverting OpAmp Voltage Amplifier Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/inverting-and-noninverting-opamp-voltage-amplifier-circuits/) expected_score=10 parser=not_run
- 095 `bme_emg_band_pass_chain` [bme:bme_emg_band_pass_chain] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 096 `bme_emg_band_pass_chain_higher_high_pass_corner` [bme:bme_emg_band_pass_chain:value_variant] source=[All About Circuits: Series and Parallel AC Circuits Worksheet](https://www.allaboutcircuits.com/worksheets/series-and-parallel-ac-circuits/) expected_score=10 parser=not_run
- 097 `bme_instrumentation_amplifier` [bme:bme_instrumentation_amplifier] source=[Electronics Tutorials: Instrumentation Amplifier](https://www.electronics-tutorials.ws/opamp/instrumentation-amplifier.html) expected_score=10 parser=not_run
- 098 `bme_instrumentation_amplifier_rg_gets_smaller` [bme:bme_instrumentation_amplifier:value_variant] source=[Electronics Tutorials: Instrumentation Amplifier](https://www.electronics-tutorials.ws/opamp/instrumentation-amplifier.html) expected_score=10 parser=not_run
- 099 `bme_photodiode_tia` [bme:bme_photodiode_tia] source=[RP Photonics: Photodiode Amplifiers](https://www.rp-photonics.com/photodiode_amplifiers.html) expected_score=10 parser=not_run
- 100 `bme_photodiode_tia_photocurrent_doubles` [bme:bme_photodiode_tia:value_variant] source=[RP Photonics: Photodiode Amplifiers](https://www.rp-photonics.com/photodiode_amplifiers.html) expected_score=10 parser=not_run
