##### this code is there to send prompts to llm #######
##### its function is imported in maker.py ######

import requests
import openai
import json
import re

PERPLEXITY_API_KEY = " "  # Replace with your actual API key
OPENAI_API_KEY = " "
CLAUDE_API_KEY = " "
DEEPSEEK_API_KEY = " "
from JSON_update import append_block_to_total_vectors

#✅ Function to generate Verilator-compatible Verilog with functional coverage
def get_modified_verilog_from_gpt():
    # Read Verilog code
    with open("top.sv", "r") as file:
        verilog_code = file.read()

    # Read design description
    with open("dut-description-gpt/m04.des", "r") as desc_file:
        design_description = desc_file.read()

    # Read functional description
    with open("dut_funtional_description/m04_functional.txt", "r") as desc_file:
        functional_description = desc_file.read()

    # Build the final prompt string
    prompt = f"""
    Design Description:
    {design_description}

    Add Verilator-compatible functional coverage to the following Verilog module:
    {verilog_code}

    {functional_description}
    """

    # Define API request parameters
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'Authorization': f'Bearer {PERPLEXITY_API_KEY}'
    }

    data = {
        "model": "sonar",
        "stream": False,
        "max_tokens": 1800,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": "Be precise and return only the modified Verilog code."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]
        start_index = content.find("module")
        end_index = content.rfind("endmodule") + len("endmodule")

        if start_index != -1 and end_index != -1:
            modified_verilog = content[start_index:end_index] + "\n"
            with open("top_1.sv", "w") as file:   # .sv is used because system verilog constructs are used
                file.write(modified_verilog)
            print("✅ Modified Verilog file saved as 'top_1.sv'")  
            
                     
        else:
            print("⚠️ Verilog code not found in the API response")

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error occurred: {errh}")
    except requests.exceptions.RequestException as err:
        print(f"Something went wrong: {err}")

def remove_json_comments(text: str):
    """
    Extract all JSON arrays from text, remove comments (// and /* */),
    and return each JSON array as a separate JSON string.
    """
    json_matches = re.findall(r"\[.*?(?:\]|\Z)", text, flags=re.DOTALL)
    json_strings = []

    for jm in json_matches:
        # Remove comments
        jm = re.sub(r"//.*", "", jm)
        jm = re.sub(r"/\*.*?\*/", "", jm, flags=re.DOTALL)
        jm = jm.strip()
        json_strings.append(jm)

    return json_strings

def safe_json_loads(json_str):
    """
    Safely loads JSON by trimming trailing garbage.
    Repairs missing closing brackets and removes incomplete items.
    """
    json_str = json_str.strip()

    # Try to ensure it starts with [ for arrays
    if not json_str.startswith("["):
        return None

    # Attempt auto-close of array if missing ]
    if not json_str.endswith("]"):
        json_str = re.sub(r",\s*$", "", json_str)
        json_str = json_str.rstrip() + "]"

    # Attempt loading progressively shorter strings
    while json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Trim to the last complete item if possible
            cut = json_str[:e.pos].rstrip()
            # Remove trailing commas or partial object starts
            cut = re.sub(r",\s*(\]?)$", r"\1", cut)
            # Remove trailing incomplete object like {"clk":"1",
            cut = re.sub(r"\{[^\{\}]*$", "", cut)
            # Add closing bracket if array seems open
            if cut.count("[") > cut.count("]"):
                cut += "]"
            json_str = cut
    return None

def extract_all_json_blocks(content: str):
    """Extract all valid JSON list blocks ([ ... ]) from LLM response."""
    json_blocks = []
    pattern = re.compile(r"\[.*", re.DOTALL)
    for match in pattern.finditer(content):
        # print("match",match.group(0))
        json_list  = remove_json_comments(match.group(0))
        # print("json_list ",json_list)
        for json_str in json_list:
            parsed = safe_json_loads(json_str)
            # print("parsed",parsed)
            if parsed and isinstance(parsed, list):         ## to remove unvalid json like [2] [2:0] extra
                # Keep only lists that contain dict elements
                if any(isinstance(x, dict) for x in parsed):
                    json_blocks.append(parsed)

        print("json_blocks", json_blocks)
        
    return json_blocks

def is_prefix_or_suffix(shorter, longer):
    """Return True if `shorter` list is a prefix or suffix of `longer` list."""
    if len(shorter) >= len(longer):
        return False
    
    prefix_match = all(shorter[i] == longer[i] for i in range(len(shorter)))
    suffix_match = all(shorter[i] == longer[i + len(longer) - len(shorter)] for i in range(len(shorter)))
    
    return prefix_match or suffix_match

# # ✅ Function to send toggle coverage prompt and get sequence
def get_test_vector_from_gpt(loop_it,system_msg,count,idx,output_file):
# def get_test_vector_from_gpt():

    # generate_prompt1_from_uncovered_signals(design_description_path=design_description_path) ## makes gpt_input.txt
    prompt_file="gpt_input.txt"
    with open(prompt_file, "r") as f:
        prompt = f.read()
    
    with open(output_file, "r") as f:
        vectors = json.load(f)
    
    if not hasattr(get_test_vector_from_gpt, "prev_count"):
        get_test_vector_from_gpt.prev_count = 0
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": prompt}
    ]
    # If duplicate case, add assistant’s prior output to context
    # print("get_test_vector_from_gpt.prev_count",count != get_test_vector_from_gpt.prev_count)
    if count != get_test_vector_from_gpt.prev_count and idx==-1:
        user_input = input("Enter your message for the LLM: ")
        messages.append(
        {"role": "assistant", "content":
         "This was the assistant’s last output, don’t repeat it.\n\n"
         f"{json.dumps(vectors, indent=4)}"
        }
    )
        messages.append(
            # {"role": "user", "content": "Don't repeat this case again as it did not trigger the branch. Generate a new set of vectors by strictly refering the ""# Design Description"" so that it is able to solve the line coverage problem."}
            {"role": "user", "content": user_input}
        )
    get_test_vector_from_gpt.prev_count =count
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'Authorization': f'Bearer {PERPLEXITY_API_KEY}'
    }
    
    # # system_msg = build_system_msg(coverage_type)
    # print("system=", system_msg)
    data = {
        "model": "sonar",
        "stream": False,
        "max_tokens": 1024,
        "temperature": 0.0,
        "messages": messages
    }
    json_count = 0
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        # content = """  """ #this can be used to test without llm just by giving response
        print("Raw LLM response:\n", content)
        json_blocks = extract_all_json_blocks(content)
        if not json_blocks:
            print("⚠️ No valid JSON blocks found in LLM response.")
            json_count =1
        else:
            # Sort by length (shortest first)
            json_blocks.sort(key=len)

            final_blocks = []
            skipped = []
            for i, block in enumerate(json_blocks):
                redundant = any(is_prefix_or_suffix(block, other) for other in json_blocks if len(other) > len(block))
                if redundant:
                    skipped.append(block)
                else:
                    final_blocks.append(block)

            # Save only non-redundant blocks
            for i, block in enumerate(final_blocks, start=1):
                output_file = f"input_vectors_{i}.json"
                with open(output_file, "w") as f:
                    f.write("[\n")
                    for i, item in enumerate(block):
                        line = " " + json.dumps(item)
                        if i < len(block) - 1:
                            line += ","
                        f.write(line + "\n")
                    f.write("]")
                l=append_block_to_total_vectors(block,loop_it)
                print(f"✅ Saved non-redundant JSON block {i} ({len(block)} vectors) → {output_file}")
                json_count = len(final_blocks)
            print("Inside function json_count =", json_count)
            print(f"\n📦 Total Test JSON sequences saved: {len(final_blocks)}")
            print(f"🚫 Skipped redundant sequences: {len(skipped)}")

    except requests.exceptions.RequestException as err:
        print(f"❌ Error calling API: {err}")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
    return json_count

#### OPENAI ######################
# def get_test_vector_from_gpt(loop_it, system_msg, count, idx, output_file):

#     prompt_file = "gpt_input.txt"
#     with open(prompt_file, "r") as f:
#         prompt = f.read()

#     with open(output_file, "r") as f:
#         vectors = json.load(f)

#     if not hasattr(get_test_vector_from_gpt, "prev_count"):
#         get_test_vector_from_gpt.prev_count = 0

#     messages = [
#         {"role": "system", "content": system_msg},
#         {"role": "user", "content": prompt}
#     ]

#     # Duplicate case → show previous output + ask user
#     if count != get_test_vector_from_gpt.prev_count and idx == -1:
#         user_input = input("Enter your message for the LLM: ")

#         messages.append({
#             "role": "assistant",
#             "content":
#                 "This was the assistant’s last output, don’t repeat it.\n\n"
#                 f"{json.dumps(vectors, indent=4)}"
#         })

#         messages.append({
#             "role": "user",
#             "content": user_input
#         })

#     get_test_vector_from_gpt.prev_count = count

#     # -------------------------------
#     # OPENAI API VERSION STARTS HERE
#     # -------------------------------
#     url = "https://api.openai.com/v1/chat/completions"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {OPENAI_API_KEY}"
#     }

#     data = {
#         "model": "gpt-4.1",   # or gpt-4.1-mini / gpt-5 / gpt-5.1 etc.
#         "messages": messages,
#         "max_tokens": 1024,
#         "temperature": 0.0,
#         "stream": False
#     }

#     json_count = 0
#     try:
#         response = requests.post(url, headers=headers, data=json.dumps(data))
#         response.raise_for_status()

#         content = response.json()["choices"][0]["message"]["content"]
#         print("Raw LLM response:\n", content)

#         json_blocks = extract_all_json_blocks(content)

#         if not json_blocks:
#             print("⚠️ No valid JSON blocks found in LLM response.")
#             json_count = 1
#         else:
#             json_blocks.sort(key=len)

#             final_blocks = []
#             skipped = []

#             for i, block in enumerate(json_blocks):
#                 redundant = any(
#                     is_prefix_or_suffix(block, other)
#                     for other in json_blocks if len(other) > len(block)
#                 )
#                 if redundant:
#                     skipped.append(block)
#                 else:
#                     final_blocks.append(block)

#             for i, block in enumerate(final_blocks, start=1):
#                 output_file = f"input_vectors_{i}.json"
#                 with open(output_file, "w") as f:
#                     f.write("[\n")
#                     for j, item in enumerate(block):
#                         line = " " + json.dumps(item)
#                         if j < len(block) - 1:
#                             line += ","
#                         f.write(line + "\n")
#                     f.write("]")

#                 append_block_to_total_vectors(block, loop_it)
#                 print(f"✅ Saved non-redundant JSON block {i} ({len(block)} vectors) → {output_file}")

#                 json_count = len(final_blocks)

#             print("Inside function json_count =", json_count)
#             print(f"\n📦 Total Test JSON sequences saved: {len(final_blocks)}")
#             print(f"🚫 Skipped redundant sequences: {len(skipped)}")

#     except requests.exceptions.RequestException as err:
#         print(f"❌ Error calling API: {err}")
#     except Exception as e:
#         print(f"⚠️ Unexpected error: {e}")

#     return json_count


###### DEEPSEEK #########################3
# def get_test_vector_from_gpt(loop_it, system_msg, count, idx, output_file):

#     prompt_file = "gpt_input.txt"
#     with open(prompt_file, "r") as f:
#         prompt = f.read()

#     with open(output_file, "r") as f:
#         vectors = json.load(f)

#     if not hasattr(get_test_vector_from_gpt, "prev_count"):
#         get_test_vector_from_gpt.prev_count = 0

#     messages = [
#         {"role": "system", "content": system_msg},
#         {"role": "user", "content": prompt}
#     ]

#     # Duplicate case → attach last output + ask user
#     if count != get_test_vector_from_gpt.prev_count and idx == -1:
#         user_input = input("Enter your message for the LLM: ")

#         messages.append({
#             "role": "assistant",
#             "content":
#                 "This was the assistant’s last output, don’t repeat it.\n\n"
#                 f"{json.dumps(vectors, indent=4)}"
#         })

#         messages.append({
#             "role": "user",
#             "content": user_input
#         })

#     get_test_vector_from_gpt.prev_count = count

#     # --------------------------------------
#     # DEEPSEEK API REQUEST SECTION
#     # --------------------------------------
#     url = "https://api.deepseek.com/chat/completions"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
#     }

#     data = {
#         "model": "deepseek-chat",   # or "deepseek-reasoner"
#         "messages": messages,
#         "max_tokens": 1024,
#         "temperature": 0.0,
#         "stream": False
#     }

#     json_count = 0
#     try:
#         response = requests.post(url, headers=headers, data=json.dumps(data))
#         response.raise_for_status()

#         content = response.json()["choices"][0]["message"]["content"]
#         print("Raw LLM response:\n", content)

#         json_blocks = extract_all_json_blocks(content)

#         if not json_blocks:
#             print("⚠️ No valid JSON blocks found in LLM response.")
#             json_count = 1
#         else:
#             json_blocks.sort(key=len)

#             final_blocks = []
#             skipped = []

#             for i, block in enumerate(json_blocks):
#                 redundant = any(
#                     is_prefix_or_suffix(block, other)
#                     for other in json_blocks if len(other) > len(block)
#                 )
#                 if redundant:
#                     skipped.append(block)
#                 else:
#                     final_blocks.append(block)

#             for i, block in enumerate(final_blocks, start=1):
#                 output_file = f"input_vectors_{i}.json"
#                 with open(output_file, "w") as f:
#                     f.write("[\n")
#                     for j, item in enumerate(block):
#                         line = " " + json.dumps(item)
#                         if j < len(block) - 1:
#                             line += ","
#                         f.write(line + "\n")
#                     f.write("]")

#                 append_block_to_total_vectors(block, loop_it)
#                 print(f"✅ Saved non-redundant JSON block {i} ({len(block)} vectors) → {output_file}")

#                 json_count = len(final_blocks)

#             print("Inside function json_count =", json_count)
#             print(f"\n📦 Total Test JSON sequences saved: {len(final_blocks)}")
#             print(f"🚫 Skipped redundant sequences: {len(skipped)}")

#     except requests.exceptions.RequestException as err:
#         print(f"❌ Error calling API: {err}")
#     except Exception as e:
#         print(f"⚠️ Unexpected error: {e}")

#     return json_count

#### CLAUDE ################
# def get_test_vector_from_gpt(loop_it, system_msg, count, idx, output_file):

#     prompt_file = "gpt_input.txt"
#     with open(prompt_file, "r") as f:
#         prompt = f.read()

#     with open(output_file, "r") as f:
#         vectors = json.load(f)

#     if not hasattr(get_test_vector_from_gpt, "prev_count"):
#         get_test_vector_from_gpt.prev_count = 0

#     # Claude uses "system" and user messages inside "messages":[]
#     # Same roles as OpenAI.
#     messages = [
#         {"role": "system", "content": system_msg},
#         {"role": "user", "content": prompt}
#     ]

#     # Duplicate case → attach last output + ask user
#     if count != get_test_vector_from_gpt.prev_count and idx == -1:
#         user_input = input("Enter your message for the LLM: ")

#         messages.append({
#             "role": "assistant",
#             "content":
#                 "This was the assistant’s last output, don’t repeat it.\n\n"
#                 f"{json.dumps(vectors, indent=4)}"
#         })

#         messages.append({
#             "role": "user",
#             "content": user_input
#         })

#     get_test_vector_from_gpt.prev_count = count

#     # --------------------------------------
#     # CLAUDE API REQUEST SECTION
#     # --------------------------------------
#     url = "https://api.anthropic.com/v1/messages"
#     headers = {
#         "Content-Type": "application/json",
#         "x-api-key": CLAUDE_API_KEY,
#         "anthropic-version": "2023-06-01"
#     }

#     data = {
#         "model": "claude-3-7-sonnet-latest",
#         "max_tokens": 1024,
#         "temperature": 0.0,
#         "messages": messages
#     }

#     json_count = 0

#     try:
#         response = requests.post(url, headers=headers, data=json.dumps(data))
#         response.raise_for_status()

#         # Claude returns content like:
#         # "content": [{"type": "text", "text": "..."}]
#         content = response.json()["content"][0]["text"]
#         print("Raw LLM response:\n", content)

#         json_blocks = extract_all_json_blocks(content)

#         if not json_blocks:
#             print("⚠️ No valid JSON blocks found in LLM response.")
#             json_count = 1
#         else:
#             json_blocks.sort(key=len)

#             final_blocks = []
#             skipped = []

#             for i, block in enumerate(json_blocks):
#                 redundant = any(
#                     is_prefix_or_suffix(block, other)
#                     for other in json_blocks if len(other) > len(block)
#                 )
#                 if redundant:
#                     skipped.append(block)
#                 else:
#                     final_blocks.append(block)

#             for i, block in enumerate(final_blocks, start=1):
#                 output_file = f"input_vectors_{i}.json"
#                 with open(output_file, "w") as f:
#                     f.write("[\n")
#                     for j, item in enumerate(block):
#                         line = " " + json.dumps(item)
#                         if j < len(block) - 1:
#                             line += ","
#                         f.write(line + "\n")
#                     f.write("]")

#                 append_block_to_total_vectors(block, loop_it)
#                 print(f"✅ Saved non-redundant JSON block {i} ({len(block)} vectors) → {output_file}")

#                 json_count = len(final_blocks)

#             print("Inside function json_count =", json_count)
#             print(f"\n📦 Total Test JSON sequences saved: {len(final_blocks)}")
#             print(f"🚫 Skipped redundant sequences: {len(skipped)}")

#     except requests.exceptions.RequestException as err:
#         print(f"❌ Error calling Claude API: {err}")
#     except Exception as e:
#         print(f"⚠️ Unexpected error: {e}")

#     return json_count


# if __name__ == "__main__":
#     # system_msg= """ please reply as a friend. No need to add any references"""
#     # count_x = 0
#     # bdex = -1
#     # json_count = get_test_vector_from_gpt(1,system_msg,count_x,bdex,f"input_vectors_2.json") #count_2 is for to send correct test sequence to role:assistant 
#     # print("json_count",json_count)
     
