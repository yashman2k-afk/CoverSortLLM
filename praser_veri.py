##### this code is there to get signal_info.txt and fuzzer (tb_maker see rfuzz_harness.cpp) #######
##### its function is imported in maker.py file #####
#### it user design file ######

from __future__ import absolute_import
from __future__ import print_function
import os
from optparse import OptionParser
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer

def strip_module_body(verilog_file, output_file):
    with open(verilog_file, "r") as f:
        lines = f.readlines()

    new_lines = []
    inside_module = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("module"):
            inside_module = True
            new_lines.append(line)  # keep module declaration
            continue
        if inside_module:
            # keep only input/output/reg/wire declarations
            if any(stripped.startswith(kw) for kw in ["input", "output", "reg", "wire",");"]):
                new_lines.append(line)
            elif stripped.startswith("endmodule"):
                new_lines.append(line)
                inside_module = False
    # write stripped version
    with open(output_file, "w") as f:
        f.writelines(new_lines)
    print(f"✅ Stripped module saved to {output_file}")


def flatten_signal(name, width):
    if width == 1:
        return [name]
    else:
        return [f"{name}[{i}]" for i in range(width)]

def strip_top(name):
    return name.split('.', 1)[-1]

def fuzzer_and_signal_list_maker():
    optparser = OptionParser()
    optparser.add_option("-t", "--top", dest="topmodule", default="top_1", help="Top module name")
    (options, args) = optparser.parse_args()

    # filelist = ["top_1.v"]
    # Example usage before analyzer
    strip_module_body("top_1.v", "top_1_stripped.v")
    filelist = ["top_1_stripped.v"]
    top_module = options.topmodule

    print(f"🔍 Parsing Verilog file: {filelist[0]} with top module: {top_module}")

    for f in filelist:
        if not os.path.exists(f):
            raise IOError("File not found: " + f)

    analyzer = VerilogDataflowAnalyzer(filelist, top_module)
    analyzer.generate()

    terms = analyzer.getTerms()

    signals = {
        'input': [], 'output': [], 'reg': [], 'wire': []
    }
    flat_signals = {
        'input': [], 'output': [], 'reg': [], 'wire': []
    }

    for tk, tv in sorted(terms.items(), key=lambda x: str(x[0])):
        name = strip_top(str(tv.name))
        term_types = [t.lower() for t in tv.termtype]
        if tv.msb is not None and tv.lsb is not None:
            width = abs(int(tv.msb.value) - int(tv.lsb.value)) + 1
        else:
            width = 1

        if 'input' in term_types:
            signals['input'].append((name, width))
            flat_signals['input'].extend(flatten_signal(name, width))
        elif 'output' in term_types:
            signals['output'].append((name, width))
            flat_signals['output'].extend(flatten_signal(name, width))
        elif 'reg' in term_types:
            signals['reg'].append((name, width))
            flat_signals['reg'].extend(flatten_signal(name, width))
        elif 'wire' in term_types:
            signals['wire'].append((name, width))
            flat_signals['wire'].extend(flatten_signal(name, width))

    # ✅ Save signal info
    with open("signal_info.txt", "w") as f:
        for category in signals:
            for name, width in signals[category]:
                f.write(f"{category} {name} {width}\n")

    # ✅ Save flattened signals
    with open("flattened_signals.txt", "w") as f:
        for category in flat_signals:
            for bitname in flat_signals[category]:
                f.write(f"{category} {bitname}\n")

    # ✅ Generate rfuzz-harness.cpp
    with open("rfuzz-harness.cpp", "w") as f:
        f.write('#include <vector>\n')
        f.write('#include <string>\n')
        f.write('#include <memory>\n')
        f.write('#include <verilated.h>\n')
        f.write('#include "Vtop_1.h"\n\n')
        f.write("int fuzz_poke(std::vector<bool>& bitstream, Vtop_1* top_1) {\n")
        f.write("    int bit_count = 0;\n")
        for name, width in signals['input']:
            if width == 1:
                f.write(f"    top_1->{name} = bitstream[bit_count++];\n")
            else:
                f.write(f"    top_1->{name} = 0;\n")
                for i in range(width):
                    f.write(f"    top_1->{name} |= (bitstream[bit_count++] << {i});\n")
        f.write("    return bit_count;\n")
        f.write("}\n")

    print("✅ signal_info.txt, flattened_signals.txt and rfuzz-harness.cpp saved!")
    os.remove("top_1_stripped.v")

if __name__ == "__main__":
    fuzzer_and_signal_list_maker()
