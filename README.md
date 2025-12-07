# CoverSortLLM
A framework to improve coverage of single module designs by intelligent test vector generation using LLM.
# Prequisites:
-CoverSort LLM will only work in linux environments hence install linux or WSL.
-Install python3, cpp, verilator tool in linux.
-Install pyverilog, json and libraries required for openai, sonar, deepseek, claude to work.
# To start:
- extract the CoverSortLLM.zip file and change path to that folder in linux.
- put the desired design from 'dut' folder into 'top.sv' file and remember the module name should be 'top_1' only.
- set parameters related to design in maker.py code like design file path, description path, fsm.
- Use 'python3 maker.py' command in terminal to start the process.
# Files generated which are important:
- logs, rfuzz_harness.cpp and rfuzz_harness.h
- uncovered_lines.json(if coverage_type == line or functional ) and uncovered_signals.json
- gpt_input.txt, gpt_feedback.txt, input_vectors.json, total_vectors.json, output.json.
- cov_total folder which contains the files related to overall coverage like 'annotated-coverage' etc.

 
