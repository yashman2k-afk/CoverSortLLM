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

# 📄 Generated Files

After running the tool, several important files and folders are created:

- **logs/**  
  Contains all runtime logs and debug information.

- **rfuzz_harness.cpp** and **rfuzz_harness.h**  
  Auto-generated C++ harness files (used as Driver in testbench) for Verilator simulation and coverage feedback integration.

- **Coverage Output Files**
  - `uncovered_lines.json` — generated when `coverage_type` is set to `line` or `functional`.
  - `uncovered_signals.json` — lists uncovered functional coverage points or signals.

- **LLM Interaction Files**
  - `gpt_input.txt` — prompt sent to the LLM.
  - `gpt_feedback.txt` — LLM feedback received during iterative refinement.
  - `input_vectors.json` — test vectors generated for the current iteration.
  - `total_vectors.json` — cumulative test vectors across all iterations.
  - `output.json` — final summarized output of the run.

- **cov_total/**  
  Directory containing all final coverage-related files, including:
  - `annotated-coverage`
  - Additional Verilator coverage reports
  - Merged coverage summaries

These files are essential for understanding coverage progress, LLM decisions, and simulation results.


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


 
