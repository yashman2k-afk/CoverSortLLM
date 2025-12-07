import json
import os
def append_block_to_total_vectors(block, loop_it, total_file="total_vectors.json"):# to save all test vectors along with reset case with each sequence if there
    if not block:
        return 0

    # Detect signals
    reset_signal = "reset" if "reset" in block[0] else "rst" if "rst" in block[0] else None
    clk_signal   = "clock" if "clock" in block[0] else "clk" if "clk" in block[0] else None

    # Create a generic reset vector if the reset signal exists
    reset_vector = {k: "0" for k in block[0]} if block else {}
    if reset_signal in reset_vector:
        reset_vector[reset_signal] = "1"
    if clk_signal in reset_vector:
        reset_vector[clk_signal] = "1"

    # Determine mode: overwrite or append
    mode = "w" if loop_it == 1 else "r+"

    with open(total_file, mode) as f:
        if loop_it == 1:
            f.write("[\n")
        else:
            content = f.read().strip()
            if content.endswith("]"):
                content = content[:-1].rstrip()
                if content.endswith(","):
                    content = content[:-1]
            f.seek(0)
            f.truncate()
            if content:
                f.write(content)
                f.write(",\n")
            else:
                f.write("[\n")

        # Insert reset vector if detected
        if reset_signal:
            f.write(json.dumps(reset_vector) + ",\n")

        # Append new block
        for i, item in enumerate(block):
            f.write(json.dumps(item))
            if i < len(block) - 1:
                f.write(",\n")
        f.write("\n]")
    return len(block)

def copy_json_file_exact(src_filename="input_vectors_1.json", dest_filename="output.json"):
    with open(src_filename, "r") as f:
        data = json.load(f)

    # Check if any item has "clk"
    has_clk = any("clk" in item for item in data)

    if has_clk:
        # Run expansion if clk exists
        output_data = expand_clk_to_0_and_1_str(src_filename)    
    else:
        # Otherwise, copy directly
        output_data = data
    
    with open(dest_filename, "w") as f:
        f.write("[\n")
        for i, item in enumerate(output_data):
            line = json.dumps(item)
            f.write(f"{line}" + (",\n" if i < len(output_data) - 1 else "\n"))
        f.write("]")



def expand_clk_to_0_and_1_str(input_file):

    with open(input_file, "r") as f:
        input_vectors = json.load(f)

    expanded = []
    for vec in input_vectors:
        vec_clk_0 = {k: str(v) for k, v in vec.items()}
        vec_clk_0["clk"] = "0"
        expanded.append(vec_clk_0)

        vec_clk_1 = {k: str(v) for k, v in vec.items()}
        vec_clk_1["clk"] = "1"
        expanded.append(vec_clk_1)

    return expanded


# def update_json_sequence(input_file="input_vectors.json", output_file="output.json"):

#     expanding = expand_clk_to_0_and_1_str(input_file)
#     def toggle_bitstring(value):
#         # Toggle each bit character ('0' ↔ '1')
#         return ''.join('1' if c == '0' else '0' for c in value)

#     # Load existing sequence
#     # with open(input_file, "r") as f:
#     #     data = json.load(f)

#     # Validate last entry
#     last_entry = expanding[-1]
#     if "clk" not in last_entry:
#         raise ValueError("Last entry must have a 'clk' signal.")

#     # Step 1: Add clk=0 version if last was clk=1
#     if last_entry["clk"] == "0":
#         low_clk = {"clk": "1"}
#         for k, v in last_entry.items():
#             if k != "clk":
#                 low_clk[k] = v
#         expanding.append(low_clk)

#     # Step 2: Use the latest clk=1 entry to toggle from
#     last_high_clk = next((d for d in reversed(expanding) if d["clk"] == "0"), None)
#     if not last_high_clk:
#         raise ValueError("No clk=0 entry found to base toggling on.")

#     # Step 3: Toggle all non-clk signals
#     toggled_signals = {k: toggle_bitstring(v) for k, v in last_high_clk.items() if k != "clk"}

#     # Step 4: Add clk=1, clk=0, clk=1 sequence with toggled signals
#     toggled_sequence = [
#        # {"clk": "1", **toggled_signals},
#         {"clk": "0", **toggled_signals},
#         {"clk": "1", **toggled_signals},  # uncomment if 3-tuple is needed
#     ]
#     expanding.extend(toggled_sequence)

#     # Step 5: Write to output with pretty spacing
#     with open(output_file, "w") as f:
#         f.write("[\n")
#         for i, item in enumerate(expanding):
#             line = json.dumps(item)
#             f.write(f"{line}" + (",\n" if i < len(expanding) - 1 else "\n"))
#         f.write("]")

def update_json_sequence(input_file="input_vectors.json", output_file="output.json"):
    # Load the existing vectors
    with open(input_file, "r") as f:
        seq = json.load(f)

    # Helper: flip only '0' <-> '1' characters, leave others as-is
    def toggle_bitstring(s):
        if not isinstance(s, str):
            return s
        return ''.join('1' if c == '0' else '0' if c == '1' else c for c in s)

    # Detect if any entry has a clk key
    clk_present = any(isinstance(e, dict) and ("clk" in e) for e in seq)

    if not clk_present:
        # --- NO CLK: append toggled copy of the LAST entry only ---
        if not seq:
            raise ValueError("input_vectors.json is empty.")
        last = seq[-1]
        toggled = {k: toggle_bitstring(v) for k, v in last.items()}
        seq.append(toggled)
    else:
        # --- WITH CLK: keep your original expansion behavior ---
        expanding = expand_clk_to_0_and_1_str(input_file)
        last = expanding[-1]

        # Ensure we end on clk=1
        if last.get("clk") == "0":
            copy = dict(last)
            copy["clk"] = "1"
            expanding.append(copy)

        # Find last clk=0 entry to base toggling on
        base = next((d for d in reversed(expanding) if d.get("clk") == "0"), None)
        if base is None:
            raise ValueError("No clk=0 entry found to base toggling on.")

        # Toggle all non-clk signals
        toggled_signals = {k: toggle_bitstring(v) for k, v in base.items() if k != "clk"}

        # Append clk=0 then clk=1 with toggled signals
        expanding.extend([
            {"clk": "0", **toggled_signals},
            {"clk": "1", **toggled_signals},
        ])
        seq = expanding

    # Write pretty JSON
    with open(output_file, "w") as f:
        f.write("[\n")
        for i, item in enumerate(seq):
            line = json.dumps(item)
            f.write(f"{line}" + (",\n" if i < len(seq) - 1 else "\n"))
        f.write("]")



# basic testcase maker


import json

def generate_basic_vectors(signal_info_file="signal_info.txt", output_file="output.json"):
    # Step 1: Parse signal_info.txt to get input signals
    input_signals = {}
    with open(signal_info_file, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 3 and parts[0] == "input":
                name, width = parts[1], int(parts[2])
                input_signals[name] = width

    # Step 2: Generate base values for all inputs (all zeros initially)
    base_values = {
        name: "0" * width
        for name, width in input_signals.items()
    }

    # Step 3: Build sequences for clk and rst if present
    clk_seq = None
    rst_seq = None

    if "clk" in input_signals:
        clk_seq = ["0", "1", "0", "1"]  # simple toggle

    
    if "rst" in input_signals or "reset" in input_signals:
        rst_signal = "rst" if "rst" in input_signals else "reset"
        rst_seq = ["1", "1", "0", "0"]  # typical reset pattern
    else:
        rst_signal = None


    # Step 4: Determine how many cycles to generate
    seq_length = max(len(s) for s in [clk_seq, rst_seq] if s is not None) if (clk_seq or rst_seq) else 4

    # Step 5: Create vectors
    vectors = []
    for i in range(seq_length):
        vec = base_values.copy()
        if clk_seq:
            vec["clk"] = clk_seq[i % len(clk_seq)]
        if rst_seq:
            vec[rst_signal] = rst_seq[i % len(rst_seq)]
        vectors.append(vec)

    # # Step 6: Write to output file
    # with open(output_file, "w") as f:
    #     json.dump(vectors, f, indent=2)


    # Step 4: Overwrite output.json with new vectors
    with open(output_file, "w") as f:
        f.write("[\n")
        for i, item in enumerate(vectors):
            line = json.dumps(item)
            f.write(f"{line}" + (",\n" if i < len(vectors) - 1 else "\n"))
        f.write("]")



if __name__ == "__main__":
    copy_json_file_exact()
    
  