# CoverSortLLM
A framework to improve coverage of single module designs by intelligent test vector generation using LLM. Below figure shows the architechture:

![Block Diagram](Framework_5.png)

# 🛠️ Prerequisites

- **Linux Environment Required**  
  CoverSortLLM works only on Linux-based systems. You can use either a native Linux installation or **WSL (Windows Subsystem for Linux)** on Windows.

- **Install Required Tools**
  - `python3`
  - `g++` / `cpp` compiler
  - `verilator`

- **Install Required Python Libraries**
  - `pyverilog`
  - `json`
  - Libraries for LLM integrations such as:
    - `openai`
    - `anthropic` (Claude)
    - `sonar`
    - `deepseek`
# ▶️ Getting Started

- **Extract the `CoverSortLLM.zip` file**  
  Unzip the project and navigate to the extracted directory in your Linux environment.

- **Select the DUT (Design Under Test)**  
  Copy the desired design from the `dut/` folder into the `top.sv` file.  
  **Important:** The module name inside `top.sv` must be **`top_1`**.

- **Configure Parameters in `maker.py`**  
  Update design-related settings such as:
  - Design file path  
  - Description file path  
  - FSM parameter (set to 1 for large design set with fsm logics)

- **Run the Tool**  
  Start the process with:
  ```bash
  python3 maker.py

# Files generated which are important:
- logs, rfuzz_harness.cpp and rfuzz_harness.h
- uncovered_lines.json(if coverage_type == line or functional ) and uncovered_signals.json
- gpt_input.txt, gpt_feedback.txt, input_vectors.json, total_vectors.json, output.json.
- cov_total folder which contains the files related to overall coverage like 'annotated-coverage' etc.

# 📁Folder Description
## `dut/`

This directory includes all Design Under Test (DUT) files used in our experiments.  
The designs are grouped by complexity:

| Category | Files |
|---------|-------|
| **Small** | `s01.sv` – `s07.sv` |
| **Medium** | `m01.sv` – `m07.sv` |
| **Large** | `b01.sv` – `b07.sv` |

Each file contains a standalone SystemVerilog module representing a combinational or sequential logic block of varying complexity.


 
