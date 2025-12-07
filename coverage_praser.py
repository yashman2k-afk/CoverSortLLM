##### this code is there to get uncovered signals from annotated coverage #######
##### its function is imported in maker.py file #####
#### here uncovered signals are sorted such that reg->wire->outputs->inputs ######

import re
import json
import os


# Helper functions (keep these at the top)
def parse_annotated_coverage(filename):
    uncovered_signals = {}
    with open(filename, 'r') as file:
        for line in file:
            if line.strip().startswith('-'):
                match = re.search(r'comment=([a-zA-Z0-9_\[\]]+)', line)
                if match:
                    signal = match.group(1)
                    uncovered_signals[signal] = 0
    return uncovered_signals

##functional
def parse_uncovered_lines_with_comments(annotated_sv_path):
    """
    Extract uncovered functional coverage lines (removing Verilator prefix like %000000)
    along with the immediately preceding comment line (starting with //).
    Returns a list of dictionaries: {"line": <cover property>, "comment": <comment text>}
    """
    results = []
    last_comment = None

    if not os.path.exists(annotated_sv_path):
        print(f"❌ File not found: {annotated_sv_path}")
        return results

    with open(annotated_sv_path, 'r') as f:
        for line in f:
            stripped = line.strip()

            # Store the most recent comment
            if stripped.startswith("//"):
                last_comment = stripped[2:].strip()

            # Match Verilator-style annotated line like %000000
            elif re.match(r'%[01]{6,}\s', stripped):
                # Clean line: remove prefix like %000000
                clean_line = re.sub(r'^%[01]{6,}\s*', '', stripped)
                results.append({
                    "line": clean_line,
                    "comment": last_comment if last_comment else ""
                })
                last_comment = None  # reset for next block

    return results



def sort_uncovered_by_signal_priority(uncovered_lines, signals_info_path):
    """
    Sort uncovered lines based on the signal types they reference.
    Priority: output > reg > wire > input
    Tie-breaker: higher numeric value in the line gets higher priority.
    """
    PRIORITY = {"output": 4, "reg": 3, "wire": 2, "input": 1}

    # --- Parse signals_info.txt ---
    signal_types = {}
    with open(signals_info_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                sig_type, sig_name = parts[0], parts[1]
                signal_types[sig_name] = sig_type

    # --- Helper: compute signal-based priority ---
    def get_line_score(line):
        score = 0
        for sig, sig_type in signal_types.items():
            if re.search(rf'\b{sig}\b', line):
                score = max(score, PRIORITY.get(sig_type, 0))
        return score

    # --- Helper: extract max numeric value ---
    def get_max_numeric_value(line):
        nums = []
        # Match numbers like 4'd9, 3'b010, 12, etc.
        for match in re.findall(r"(\d+)'[bdhBDH]([0-9a-fA-F]+)|\b\d+\b", line):
            if isinstance(match, tuple):
                base_prefix, digits = match[0], match[1]
                if base_prefix:
                    base_char = line[line.index(base_prefix) + len(base_prefix) + 1].lower()
                    base = {'b': 2, 'd': 10, 'h': 16}.get(base_char, 10)
                    try:
                        nums.append(int(digits, base))
                    except ValueError:
                        pass
            else:
                try:
                    nums.append(int(match))
                except ValueError:
                    pass
        return max(nums) if nums else -1

    # --- Attach both scores ---
    for item in uncovered_lines:
        line = item["line"]
        item["priority_score"] = get_line_score(line)
        item["value_score"] = get_max_numeric_value(line)

    # --- Sort by (priority, numeric value) ---
    uncovered_lines.sort(
        key=lambda x: (x["priority_score"], x["value_score"]),
        reverse=True
    )

    return uncovered_lines




def extract_uncovered_lines_from_sv(
    annotated_sv_path="cov_total/annotated/top_1.sv",
    output_json_path="uncovered_lines.json"
):
    uncovered_lines = parse_uncovered_lines_with_comments(annotated_sv_path)
    sorted_lines = sort_uncovered_by_signal_priority(uncovered_lines, signals_info_path="signal_info.txt")

    with open(output_json_path, 'w') as f:
        json.dump(sorted_lines, f, indent=2)

    print(f"✅ Uncovered functional coverage lines saved to {output_json_path}")


###line
def extract_localparams(annotated_path):
    """
    Extracts all localparam definitions from a Verilog file and returns a map:
    { "NAME": numeric_value }
    Handles multi-line, comma-separated localparams and binary/hex/oct/decimal.
    """
    localparam_map = {}

    # Helper to parse numeric values
    def parse_value(val_str):
        val_str = val_str.strip()
        # Decimal without base
        if re.match(r'^\d+$', val_str):
            return int(val_str, 10)
        # Sized constant e.g. 4'b1010, 8'hFF, 6'o77, 12'd255
        m = re.match(r"(\d+)?'([bdhoBDHO])([0-9a-fA-FxXzZ_]+)", val_str)
        if m:
            _, base_char, digits = m.groups()
            base_char = base_char.lower()
            digits = digits.replace("_", "")
            if base_char == 'b':
                return int(digits, 2)
            elif base_char == 'd':
                return int(digits, 10)
            elif base_char == 'h':
                return int(digits, 16)
            elif base_char == 'o':
                return int(digits, 8)
        # Fallback: auto-detect base
        try:
            return int(val_str, 0)
        except ValueError:
            return None

    # Read the file and join lines if localparam continues with commas
    with open(annotated_path, 'r') as f:
        buffer = ""
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "localparam" in line or buffer:
                buffer += " " + line
                if ";" in line:  # end of statement
                    # Remove 'localparam' keyword
                    buffer_clean = buffer.replace("localparam", "").rstrip(";")
                    # Split by commas
                    parts = buffer_clean.split(",")
                    for part in parts:
                        m = re.match(r'\s*(\w+)\s*=\s*(.+)\s*', part)
                        if m:
                            name, val_str = m.groups()
                            value = parse_value(val_str)
                            if value is not None:
                                localparam_map[name] = value
                    buffer = ""  # reset buffer

    return localparam_map

def fix_if_coverage(file_in, file_out="cov_total/annotated/new_anno.v"):
    with open(file_in, "r") as f:
        lines = f.readlines()

    new_lines = []
    inside_if_block = False
    if_line_index = None
    if_block_has_covered = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # --- SINGLE-LINE if…else CHECK ---
        single_line_match = re.match(r'^\s*%0+\s*if.*;\s*$', line)
        if single_line_match:
            # Look ahead for a separate else line
            if i + 1 < len(lines) and re.match(r'^\s*%0+\s*else', lines[i + 1]):
                # Only update if both if and else are uncovered
                if re.match(r'^\s*%0+', line) and re.match(r'^\s*%0+', lines[i + 1]):
                    # Replace leading %0+ with 000001
                    new_lines.append(re.sub(r'^(\s*)%0+', r' 000001', line))
                    i += 1
                    new_lines.append(lines[i])  # append the else line as-is
                    i += 1
                    continue
            # If not both uncovered, append as-is
            new_lines.append(line)
            i += 1
            continue

        # --- MULTI-LINE begin…end CHECK (existing logic) ---
        if re.search(r'^\s*%0+\s*if', line):
            inside_if_block = True
            if_line_index = len(new_lines)
            if_block_has_covered = False
            new_lines.append(line)
            i += 1
            continue

        if inside_if_block:
            # Detect end of block
            if re.search(r'\bend\b', line) or re.search(r'end else begin', line):
                if if_block_has_covered:
                    new_lines[if_line_index] = re.sub(r'^(\s*)%0+', r' 000001', new_lines[if_line_index])
                inside_if_block = False
                if_line_index = None
                if_block_has_covered = False
            # Check if current line is covered
            elif re.search(r'^\s*0+[1-9]', line):
                if_block_has_covered = True

        new_lines.append(line)
        i += 1

    with open(file_out, "w") as f:
        f.writelines(new_lines)

def extract_uncovered_lines(
    annotated_path="cov_total/annotated/top_1.v",
    output_json_path="uncovered_lines.json"
):
    fix_if_coverage(annotated_path)  ##done to remove %000 on if, else, else if if inside thouse branch any line is covered.
    sorted_lines = sort_uncovered_lines("cov_total/annotated/new_anno.v")

    with open(output_json_path, 'w') as f:
        json.dump(sorted_lines, f, indent=2)

    print(f"✅ Uncovered functional coverage lines saved to {output_json_path}")


def load_signal_type_map(signal_info_path="signals_info.txt"):
    signal_type_map = {}
    with open(signal_info_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                direction = parts[0]  # 'input' or 'output'
                name = parts[1]
                signal_type_map[name] = direction
    return signal_type_map

def parse_uncovered_lines_from_annotated(annotated_file_path):  ##extracts all uncovered lines and inside if, elseif and case expressions it takes all signals used
    uncovered_lines = []                                        
    
    signal_regex = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b')
    verilog_keywords = {
    'always', 'assign', 'begin', 'case', 'default', 'else', 'end',
    'for', 'if', 'input', 'module', 'negedge', 'output', 'posedge',
    'reg', 'wire', 'while', 'endmodule'
    }

    # Regex to match literals like 4'b0, 8'd255, etc.
    literal_regex = re.compile(r"\b\d+'[bdhoBDHO][0-9a-fA-FxXzZ_]+\b(?!:)")

    with open(annotated_file_path, 'r') as f:
        for idx, line in enumerate(f, 1):
            cov_prefix = line[:7]
            code_text  = line[7:].rstrip('\n').strip()
            if cov_prefix.startswith('%'):
                code_no_comments = code_text.split('//')[0]
                
                code_no_literals = literal_regex.sub("", code_no_comments)
                
                tokens = signal_regex.findall(code_no_literals)
                # print(tokens)
                signals = [
                    token for token in tokens
                    if token not in verilog_keywords and not token.isdigit()
                ]
                uncovered_lines.append({
                    'line_num': idx,
                    'text': code_text,
                    'signals': list(dict.fromkeys(signals)),
                })
    return uncovered_lines


def compute_nesting_depth(annotated_path, target_line_num):
    """
    Calculates Verilog block depth up to the (inclusive) given line number in the annotated file.
    """
    depth = 0
    with open(annotated_path, 'r') as f:
        for idx, line in enumerate(f, 1):  # Line numbers start at 1
            code_text = line[7:].rstrip('\n').strip() if len(line) > 7 else line.strip()  # skip coverage prefix
            # Count every 'begin' that starts a block (standalone or inline)
            if re.search(r'\bbegin\b', code_text):
                depth += 1
            # Count 'end' (standalone or inline) as closing a block
            if re.match(r'^\s*end\b', code_text):
                depth = max(depth - 1, 0)
            if idx == target_line_num:
                break
    return depth

def sort_uncovered_lines(annotated_path):
    signal_type_map = load_signal_type_map("signal_info.txt")
    uncovered_lines = parse_uncovered_lines_from_annotated(annotated_path)
    localparam_map = extract_localparams(annotated_path)

    control_keywords = ['if', 'else if', 'case', 'else']

    def get_line_type(text):
        text = text.strip()
        # Match keywords
        for kw in control_keywords:
            if text.startswith(kw) or text.startswith(f"end {kw}"):
                return kw
        # Match case items like S0:, S1:, default:, 3'b001: etc.
        if re.match(r"^\s*[^:\s]+:", text):
            return "case_item"
        return 'other'

    def signal_priority(signal):
        t = signal_type_map.get(signal, '')
        if t == 'input': return 4
        if t == 'reg': return 3
        if t == 'wire': return 2
        if t == 'output': return 1
        return 0

    def total_signal_score(signals):                         ##basically if depth of two lines are same then we are sorting them by 
        return sum(signal_priority(sig) for sig in signals)  ##considering most of the signals in the expression used in the line in the order input>reg>wire>output
        
    
    # Annotate each line
    for idx, line in enumerate(uncovered_lines):
        line_type = get_line_type(line['text'])
        nesting_depth = compute_nesting_depth(annotated_path, line['line_num'])
        signal_score = total_signal_score(line['signals'])
    
        # Find case value if present
        case_value = -1
        if line_type == "case_item":
            label = line['signals'][0] if line['signals'] else None
            # print("label",label)
            if label in localparam_map:
                case_value = localparam_map[label]
            # else:
            #     case_value = label 
        line.update({
            'line_type': line_type,
            'depth': nesting_depth,
            'signal_score': signal_score,
            'case_value': case_value,
            'index': idx,                    # Index, it is used if say two lines have same preferece like both signal score and depth are same. index some kind of key assigned by "sorted" function to break the tie and keep same preference lines sorted based on index number 
            'original_line_num': line['line_num'],  
        })

    def sort_key(line):
        # Highest priority: case items
        if line['line_type'] == "case_item":
            priority = -1
        # Next: control keywords
        elif line['line_type'] in control_keywords:
            priority = 0
        else:
            priority = 1
        return (
            priority,                    # 1. Control keyword vs others
            -line['case_value'],         # 2. for FSMs if "high state case statement"            
            -line['depth'],              # 2. Nesting depth
            -line['signal_score'],       # 3. Signal score (higher is better)
            line['original_line_num'],   # 4. Line number in file
            line['index']                # 5. Tie-breaker: stable original order
        )

    sorted_lines = sorted(uncovered_lines, key=sort_key)
    return sorted_lines

####toggle
def base_name(signal):
    return signal.split('[')[0]

def get_signal_category_priority(signal_name, signal_info_path):
    reg_names = set()
    wire_names = set()
    output_names = set()
    input_names = set()

    with open(signal_info_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 3:
                category, name, _ = parts
                if category == "reg":
                    reg_names.add(name)
                elif category == "wire":
                    wire_names.add(name)
                elif category == "output":
                    output_names.add(name)
                elif category == "input":
                    input_names.add(name)

    if signal_name in reg_names:
        return "reg"
    elif signal_name in wire_names:
        return "wire"
    elif signal_name in output_names:
        return "output"
    elif signal_name in input_names:
        return "input"
    else:
        return None

# ✅ New: Function to extract and save uncovered signals
def extract_and_sort_uncovered_signals(
    annotated_file_path="cov_total/annotated/top_1.v",
    signal_info_path="signal_info.txt",
    output_json_path="uncovered_signals.json"
):
    if not os.path.exists(annotated_file_path) and os.path.exists("logs/coverage.dat"):
            print("✅ 100 percent coverage acheived")
    else:
        uncovered = parse_annotated_coverage(annotated_file_path)

        CATEGORY_PRIORITY = {
            "output": 0,
            "reg": 1,
            "wire": 2,
            "input": 3,
            None: 4
        }

        sorted_keys = sorted(
            uncovered.keys(),
            key=lambda s: CATEGORY_PRIORITY.get(get_signal_category_priority(base_name(s), signal_info_path), 4)
        )

        sorted_uncovered = {k: uncovered[k] for k in sorted_keys}

        with open(output_json_path, 'w') as outfile:
            json.dump(sorted_uncovered, outfile, indent=2)

        print(f"✅ Uncovered signals saved to {output_json_path}")

if __name__ == "__main__":
    extract_uncovered_lines_from_sv()
   
