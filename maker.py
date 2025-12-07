import subprocess
import re
import shutil
import subprocess
import sys
import os
import json
import copy

from JSON_update import update_json_sequence, generate_basic_vectors, copy_json_file_exact
from coverage_praser import extract_and_sort_uncovered_signals, extract_uncovered_lines_from_sv, extract_uncovered_lines
from prompt4cover import get_modified_verilog_from_gpt, get_test_vector_from_gpt  # Add this near your other imports
from praser_veri import fuzzer_and_signal_list_maker
from prompt_gen_stimu import extract_always_blocks, generate_prompt1_from_uncovered_signals, generate_prompt_for_functional_coverage, generate_prompt_for_line_coverage


#########################################################
#these are to compare if same design is running for differt type coverage
def normalize_block(block):
    # Strip comments and whitespace for fair comparison
    block = re.sub(r'//.*?\n', '', block)
    block = re.sub(r'/\*.*?\*/', '', block, flags=re.DOTALL)
    block = re.sub(r'\s+', '', block)
    return block

def compare_always_blocks_v2():
    # Read both files
    with open('top.sv') as f: code1 = f.read()
    # if os.path.exists('top_1.sv'):
    #     alt_path = 'top_1.sv'
    if os.path.exists('top_1.v'):
        alt_path = 'top_1.v'
    else:
        print("❌ nor top_1.v exists.")
        return 0
    
    with open(alt_path) as f: code2 = f.read()

    # Extract blocks using your function
    blocks1 = extract_always_blocks(code1)
    blocks2 = extract_always_blocks(code2)

    # Normalize and compare
    norm1 = set(normalize_block(b) for b in blocks1)
    norm2 = set(normalize_block(b) for b in blocks2)

    return int(norm1 == norm2)
##########################################################################

def build_system_msg(coverage_type, example_vector_str):
    if coverage_type == 'toggle':
        # example_vector_str = generate_prompt1_from_uncovered_signals()
        coverage_desc = "specific toggle coverage issue"
    elif coverage_type == 'line':
        # example_vector_str = generate_prompt_for_line_coverage()
        coverage_desc = "line coverage problem"
    else:
        # example_vector_str = generate_prompt_for_functional_coverage()
        coverage_desc = "property coverage problem"

    # Build dynamic parts
    extra_rules = []
    notes = []

    if "clk" in example_vector_str:
        extra_rules.append("- Represent input values at **posedge clk**")
        extra_rules.append("- Include `clk: 1` (no toggling)")

    if "reset" in example_vector_str or "rst" in example_vector_str:
        notes.append("- no need of reset test vector")

    # Always add the "no extra comments..." note
    notes.append("- only give binary values and follow the width convention, see example")
    # notes.append("- no extra comments or explanations just return JSON test vector sequence")
    notes.append("- just return JSON test vector sequence")
    # notes.append("- no extra comments or explanations can just include an **inline comment after each JSON object** to describe the transition that will occur on that step.")
    # notes.append("**Strictly follow any input transitions provided in # Design description in the user messages to generate test vectors.**")
    # notes.append("***STRICTLY refer ""# Design description"" before giving test vectors")
    # Join rules and notes
    each_vector_part = ""
    if extra_rules:
        each_vector_part = "Each vector should:\n" + "\n".join(extra_rules) + "\n"

    notes_part = ""
    if notes:
        notes_part = "Note:\n" + "\n".join(notes) + "\n"

    system_msg = f"""You are a Verilog test vector generation assistant. Generate a JSON test vector sequence to solve the {coverage_desc}.
{each_vector_part}{notes_part}
Example format of the vector:
{example_vector_str}
"""
    return system_msg

def modify_makefile(coverage_type):
    with open('Makefile', 'r') as file:
        content = file.read()

    if coverage_type == 'toggle':
        new_flag = 'VERILATOR_FLAGS += --coverage-toggle'
        # Ensure top_1.v is used
        content = re.sub(r'top_1\.sv', 'top_1.v', content)
        content = re.sub(
            r'(\$\(VERILATOR_COVERAGE\)[^\n]*)--annotate[^\n]*--annotate-min \d+',
            r'$(VERILATOR_COVERAGE) --annotate cov_total/annotated --annotate-points cov_total/coverage.dat.total --annotate-min 2',
            content
        )
    elif coverage_type == 'line':
        new_flag = 'VERILATOR_FLAGS += --coverage-line'
        # Ensure top_1.v is used
        content = re.sub(r'top_1\.sv', 'top_1.v', content)
        content = re.sub(
            r'(\$\(VERILATOR_COVERAGE\)[^\n]*)--annotate[^\n]*(--annotate-points [^\s]+ )?--annotate-min \d+',
            r'$(VERILATOR_COVERAGE) --annotate cov_total/annotated cov_total/coverage.dat.total --annotate-min 1',
            content
        )
    elif coverage_type == 'functional':
        new_flag = 'VERILATOR_FLAGS += --coverage-user'
        # Ensure top_1.sv is used
        content = re.sub(r'top_1\.v', 'top_1.sv', content)
        content = re.sub(
            r'(\$\(VERILATOR_COVERAGE\)[^\n]*)--annotate[^\n]*(--annotate-points [^\s]+ )?--annotate-min \d+',
            r'$(VERILATOR_COVERAGE) --annotate cov_total/annotated cov_total/coverage.dat.total --annotate-min 1',
            content
        )
    else:
        print("Invalid coverage type. Please specify 'toggle', 'line', or 'functional'.")
        return False

    # Replace any existing coverage flag
    content = re.sub(r'VERILATOR_FLAGS \+= --coverage-(user|toggle|line)', new_flag, content)

    with open('Makefile', 'w') as file:
        file.write(content)

    return True



def create_copy_file(coverage_source = None):
    try:
        with open('top.sv', 'r') as source_file:
            content = source_file.read()
        
        # Find the position of 'endmodule'
        endmodule_index = content.rfind('endmodule')
        
        if endmodule_index != -1:
            # Insert a new line after 'endmodule'
            modified_content = content[:endmodule_index + len('endmodule')] + '\n' + content[endmodule_index + len('endmodule'):]
        else:
            modified_content = content
        if(coverage_source == 'user_defined'):
            with open('top_1.sv', 'w') as dest_file:
                dest_file.write(modified_content)
        
            print("File 'top_1.sv' created successfully.")

            # write cleaned Verilog version without 'cover property' lines
            cleaned_lines = []
            for line in modified_content.splitlines():
                if 'cover property' in line:
                    cleaned_lines.append('// ' + line)  # comment it out
                else:
                    cleaned_lines.append(line)

            cleaned_content = '\n'.join(cleaned_lines)

            with open('top_1.v', 'w') as clean_file:
                clean_file.write(cleaned_content)
            print("✅ File 'top_1.v' created (cover properties commented out).")
        else:
            with open('top_1.v', 'w') as dest_file:
                dest_file.write(modified_content)
        
            print("File 'top_1.v' created successfully.")
    
    except FileNotFoundError:
        print("File 'top.sv' not found.")
    except Exception as e:
        print(f"Error creating file: {e}")

def run_makefile():
    try:
        subprocess.run(['make'], check=True)
        print("Makefile executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing Makefile: {e}")

def get_coverage_from_cpp():
    try:
        result = subprocess.run(["./get_cov"], capture_output=True, text=True)
        output = result.stdout.strip()
        covered, total = map(int, output.split())
        return covered, total
    except Exception as e:
        print(f"⚠️ Failed to get coverage: {e}")
        return 0, 0
    
def is_coverage_complete(coverage_type):  #if coverage is 100% then file inside ../annotated will not be created
    if coverage_type == 'functional':
        return os.path.exists("logs/coverage.dat") and not os.path.exists("cov_total/annotated/top_1.sv")
    else:
        return os.path.exists("logs/coverage.dat") and not os.path.exists("cov_total/annotated/top_1.v")

def archive_and_cleanup_annotated():
    os.makedirs('cov_total/annotated_old', exist_ok=True)

    if os.path.exists('cov_total/annotated/top_1.v'):
        os.replace('cov_total/annotated/top_1.v', 'cov_total/annotated_old/top_1.v')

    if os.path.exists('cov_total/annotated/top_1.sv'):
        os.replace('cov_total/annotated/top_1.sv', 'cov_total/annotated_old/top_1.sv')

    if os.path.isdir('cov_total/annotated'):
        try:
            os.rmdir('cov_total/annotated')
        except OSError:
            pass  # directory not empty

def compare_first_and_update(loop_it,count_y, current_file, previous_file):
    
    if not hasattr(compare_first_and_update, "prev_count_y"):
        compare_first_and_update.prev_count_y = 0
    with open(current_file, "r") as f:
        current_data = json.load(f)
    count_y = 0 if len(current_data) == 1 else count_y  #done if last element is there
    try:
        with open(previous_file, "r") as f:
            previous_data = json.load(f)
    except FileNotFoundError:
        previous_data = []

    mismatch_index =-1
    count = 0
    
    if(count_y>=1):#to stop and check after count_x=2
            cury = copy.deepcopy(current_data[0:count_y])
            prevy = copy.deepcopy(previous_data[0:count_y])
             # Remove index keys
            for entry in cury:
                entry.pop("index", None)
            for entry in prevy:
                entry.pop("index", None)

            # Compare element-wise
            for i in range(count_y):
                if cury[i] != prevy[i]:
                    mismatch_index = i
                    count_y = i
                    print("count_y", count_y)
                    break  # stop when first mismatch found
    
    if loop_it != 1 and current_data and previous_data and count_y == compare_first_and_update.prev_count_y:
        # make shallow copies without "index"
        cur = copy.deepcopy(current_data[count_y])
        prev = copy.deepcopy(previous_data[count_y])
        cur.pop("index", None)
        prev.pop("index", None)
        
        if cur == prev:
            count = count+1

    print("count_y,prev_count",count_y,compare_first_and_update.prev_count_y)      

    print("current_data", current_data[count_y])
    print("prev_data", previous_data[count_y])
        
    with open(previous_file, "w") as f:
        json.dump(current_data, f, indent=4)
    
    compare_first_and_update.prev_count_y = count_y

    print("mismatch_index", mismatch_index)
    print("count", count)

    return mismatch_index,count




if __name__ == "__main__":
    coverage_type = input("Enter coverage type (toggle/line/functional): ").lower()
    
    if coverage_type in ['toggle', 'line']:
        create_copy_file()
    
    if modify_makefile(coverage_type):
        if coverage_type == 'functional':
            coverage_source = input("Enter coverage source (user_defined/llm_defined): ").lower()
            if coverage_source == 'user_defined':
                if os.path.exists("cov_total"):             ###delete cov_total directory if doing with new design code
                   shutil.rmtree("cov_total") 
                n= compare_always_blocks_v2()               ## set this to 1 if design is same and already some coverage is computed and new coverage is being calcuted 
                create_copy_file(coverage_source)
                fuzzer_and_signal_list_maker()
                # if n==0:
                #     generate_basic_vectors()
                # else :b=1 #here after wards will make two new functions one to to collect all test cases in one json file and 
                # #             #another to send that json file to testbench
                generate_basic_vectors()
                run_makefile()
                loop_it = 1
                count_x =0
                bdex = -1
                count_inc =0
                fsm=1 #change to 0 for non fsm
                json_count =1                           
                while True:
                    print(f"\n🔁 Framework Iteration {loop_it} starting...")
                    extract_uncovered_lines_from_sv()
                    print("loop=",loop_it)
                    idex,count_inc = compare_first_and_update(loop_it,count_x,"uncovered_lines.json", "prev_lines.json")
                    count_x += count_inc
                    bdex =idex
                    if idex !=-1:
                        count_x=idex
                    print("count_x=",count_x)
                    example_vector_str= generate_prompt_for_functional_coverage(fsm,count_x,bdex,design_description_path="dut-description-gpt/b01.des")
                    system_msg = build_system_msg(coverage_type,example_vector_str)
                    print(system_msg)
                    json_count= get_test_vector_from_gpt(loop_it,system_msg,count_x,bdex,f"input_vectors_{json_count}.json")
                    for i in range(1, json_count+1):
                        archive_and_cleanup_annotated()         ## This will just re arrange the files which helps to terminate loop
                        output_file = f"input_vectors_{i}.json"
                        copy_json_file_exact(output_file)   ## this will just copy test vectors to output.json. Done to avoid confusion- 
                        run_makefile()
                    if is_coverage_complete(coverage_type):
                        print("✅ 100 percent coverage acheived")
                        break
                    if loop_it:
                        response = input("⚠️ Reached 1 iterations. Do you want to continue? (y/n): ").strip().lower()
                        if response != 'y':
                            print("🛑 Stopping loop by user decision.")
                            break

                    loop_it += 1

            elif coverage_source == 'llm_defined':
                if os.path.exists("cov_total"):             ###delete cov_total directory if doing with new design code
                   shutil.rmtree("cov_total") 
                n= compare_always_blocks_v2()
                create_copy_file(coverage_source)
                fuzzer_and_signal_list_maker()
                # if n==0:
                #     generate_basic_vectors()
                # else :b=1 #here after wards will make two new functions one to to collect all test cases in one json file and 
                # #             #another to send that json file to testbench
                generate_basic_vectors()
                run_makefile()
                loop_it = 1
                count_x =0
                bdex = -1
                count_inc =0
                fsm=1 #change to 0 for non fsm
                json_count =1                           
                while True:
                    print(f"\n🔁 Framework Iteration {loop_it} starting...")
                    extract_uncovered_lines_from_sv()
                    print("loop=",loop_it)
                    idex,count_inc = compare_first_and_update(loop_it,count_x,"uncovered_lines.json", "prev_lines.json")
                    count_x += count_inc
                    bdex =idex
                    if idex !=-1:
                        count_x=idex
                    print("count_x=",count_x)
                    example_vector_str= generate_prompt_for_functional_coverage(fsm,count_x,bdex,design_description_path="dut-description-gpt/b01.des")
                    system_msg = build_system_msg(coverage_type,example_vector_str)
                    print(system_msg)
                    json_count= get_test_vector_from_gpt(loop_it,system_msg,count_x,bdex,f"input_vectors_{json_count}.json")
                    for i in range(1, json_count+1):
                        archive_and_cleanup_annotated()         ## This will just re arrange the files which helps to terminate loop
                        output_file = f"input_vectors_{i}.json"
                        copy_json_file_exact(output_file)   ## this will just copy test vectors to output.json. Done to avoid confusion- 
                        run_makefile()
                    if is_coverage_complete(coverage_type):
                        print("✅ 100 percent coverage acheived")
                        break
                    if loop_it:
                        response = input("⚠️ Reached 1 iterations. Do you want to continue? (y/n): ").strip().lower()
                        if response != 'y':
                            print("🛑 Stopping loop by user decision.")
                            break

                    loop_it += 1
            else:
                print("Invalid coverage source. Please specify 'user_defined' or 'llm_defined'.")

                
        elif coverage_type == 'line':
            if os.path.exists("cov_total"):             ###delete cov_total directory if doing with new design code
                    shutil.rmtree("cov_total")  
            n= compare_always_blocks_v2()  
            fuzzer_and_signal_list_maker()              ## signals info extraction from design and makes fuzzer 
            # if n==0:
            #     generate_basic_vectors()                ## Generate some basic testcase to get coverage data
            # else :b=1 #here after wards will make two new functions one to to collect all test cases in one json file and 
                #             #another to send that json file to testbench             
            generate_basic_vectors() 
            run_makefile()
            loop_it = 1
            count_x =0
            bdex = -1
            count_inc =0
            fsm=0 #change to 0 for non fsm and for fsm to 1
            json_count =1                                 
            while True:
                # print(f"\n🔁 Framework Iteration {loop_it} starting...")
                extract_uncovered_lines()
                print("loop=",loop_it)
                # count_y =count_y+1 if count_x==1 else count_y
                idex,count_inc = compare_first_and_update(loop_it,count_x,"uncovered_lines.json", "prev_lines.json")
                count_x += count_inc
                bdex =idex
                if idex !=-1:
                    count_x=idex
                print("count_x=",count_x)
                example_vector_str= generate_prompt_for_line_coverage(fsm,count_x,bdex,design_description_path="dut-description-gpt/b05.des")
                system_msg = build_system_msg(coverage_type,example_vector_str)
                print(system_msg)
                json_count = get_test_vector_from_gpt(loop_it,system_msg,count_x,bdex,f"input_vectors_{json_count}.json") #count_2 is for to send correct test sequence to role:assistant 
                
                for i in range(1, json_count+1):
                    archive_and_cleanup_annotated()         ## This will just re arrange the files which helps to terminate loop
                    output_file = f"input_vectors_{i}.json"
                    copy_json_file_exact(output_file)   ## this will just copy test vectors to output.json. Done to avoid confusion- 
                    run_makefile()                                    ## -regard less of coverage type or basic vectors    
                
                

                if is_coverage_complete():
                    print("✅ 100 percent coverage acheived")
                    break
                if loop_it:
                    response = input("⚠️ Reached 1 iterations. Do you want to continue? (y/n): ").strip().lower()
                    if response != 'y':
                        print("🛑 Stopping loop by user decision.")
                        break

                loop_it += 1

        else:#for toggle   
           
            if os.path.exists("cov_total"):             ###delete cov_total directory if doing with new design code
                    shutil.rmtree("cov_total")  
            n= compare_always_blocks_v2()  
            fuzzer_and_signal_list_maker()              ## signals info extraction from design and makes fuzzer 
            # if n==0:
            #     generate_basic_vectors()                ## Generate some basic testcase to get coverage data
            # else :b=1 #here after wards will make two new functions one to to collect all test cases in one json file and 
                #             #another to send that json file to testbench
                         ## signals info extraction from design and makes fuzzer 
            generate_basic_vectors()                    ## Generate some basic testcase to get coverage data
            run_makefile()                              ## Initial sim -> uses the "output.json" data
            loop_it = 1                                 ##             -> makes annotated --points "useful for toggle coverage"
            count_x =0
            bdex = -1
            count_inc =0
            fsm=1 #change to 0 for non fsm
            json_count =1
            while True:
                print(f"\n🔁 Framework Iteration {loop_it} starting...")
            
                extract_and_sort_uncovered_signals()    ## Extract data from annotated coverage which help to make prompt 
                print("loop=",loop_it)
                # count_y =count_y+1 if count_x==1 else count_y
                idex,count_inc = compare_first_and_update(loop_it,count_x,"uncovered_lines.json", "prev_lines.json")
                count_x += count_inc
                bdex =idex
                if idex !=-1:
                    count_x=idex
                print("count_x=",count_x)
                example_vector_str=generate_prompt1_from_uncovered_signals(fsm,count_x,bdex,design_description_path="dut-description-gpt/b05.des")
                                                        ## prompt is made using:
            #                                           ##     (i) uncovered_signals.json -> here "output" type signal is considered first
            #                                           ##    (ii) signals_info.txt 
            #                                           ##   (iii) design file -> here whole design is not sent to prompt instead a snippet related to uncovered signal is sent
            #                                           ##    (iv) dut-description-gpt/mxx.des
                system_msg = build_system_msg(coverage_type,example_vector_str)
                print(system_msg)
                json_count = get_test_vector_from_gpt(loop_it,system_msg,count_x,bdex,f"input_vectors_{json_count}.json") #count_2 is for to send correct test sequence to role:assistant 
                
                for i in range(1, json_count+1):
                    archive_and_cleanup_annotated()         ## This will just re arrange the files which helps to terminate loop
                    output_file = f"input_vectors_{i}.json"
                    copy_json_file_exact(output_file)   ## this will just copy test vectors to output.json. Done to avoid confusion- 
                    run_makefile()  
                # get_test_vector_from_gpt(coverage_type)              ## prompt is sent to gpt and extract the testcase in vector format into "input_vectors.json"
                # archive_and_cleanup_annotated()         ## This will just re arrange the files which helps to terminate loop
                # update_json_sequence()                  ## This will just add a new toggled vector present in "input_vectors.json" to ensure 0->1 and 1->0 toggling 
                # run_makefile()                          ## new sim -> uses the "output.json" data
            # coverage.dat.total is merge should be seen.
                if is_coverage_complete(coverage_type):
                    print("✅ 100 percent coverage acheived")
                    break
                if loop_it:
                    response = input("⚠️ Reached 1 iterations. Do you want to continue? (y/n): ").strip().lower()
                    if response != 'y':
                        print("🛑 Stopping loop by user decision.")
                        break

                loop_it += 1



#for later use
            # if os.path.exists("cov_total/annotated//top_1.v"):
            #     covered, total = get_coverage_from_cpp()
            #     print(f"📊 Current Coverage: {covered}/{total} ({(covered/total)*100:.2f}%)")            
            #     if covered == total:
            #             print("✅ 100% coverage achieved!")
                

