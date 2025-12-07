#include <verilated.h>
#include "Vtop_1.h"
#include <iostream>
#include <fstream>
#include <nlohmann/json.hpp>
#include <vector>
#include <string>
#include <sstream>
#include <memory>
#include <unordered_map>
#include "rfuzz-harness.h"
#include <sys/stat.h>
#include <cstdlib>       // For system()

void ensure_directory_exists(const std::string& path) {
    struct stat st{};
    if (stat(path.c_str(), &st) != 0 || !S_ISDIR(st.st_mode)) {
        mkdir(path.c_str(), 0755);
    }
}


using json = nlohmann::json;

// Load input signal bit order from signal_info.txt
std::vector<std::string> load_input_signal_order(const std::string& filename) {
    std::ifstream infile(filename);
    std::vector<std::string> inputs;
    std::string line;

    while (std::getline(infile, line)) {
        std::istringstream iss(line);
        std::string category, name;
        int width;
        if (iss >> category >> name >> width && category == "input") {
            for (int i = 0; i < width; ++i) {
                if (width == 1) {
                    inputs.push_back(name);
                } else {
                    inputs.push_back(name + "[" + std::to_string(i) + "]");
                }
            }
        }
    }
    return inputs;
}

// bool has_signal_in_info(const std::string& filename, const std::string& sig_name) {
//     std::ifstream infile(filename);
//     std::string category, name;
//     int width;
//     while (infile >> category >> name >> width) {
//         if (category == "input" && name == sig_name) {
//             return true;
//         }
//     }
//     return false;
// }

int main(int argc, char** argv) 
{ 
    Verilated::commandArgs(argc, argv); 
    auto contextp = std::make_unique<VerilatedContext>(); 
    auto top_1 = std::make_shared<Vtop_1>(); 
    contextp->randReset(2); 
    // Randomize initial state 
    contextp->debug(0); 
    // No debug output 
    contextp->traceEverOn(true); 
    // Enable tracing 
    //Verilated::coveragep()->bindToContext(contextp.get()); // Ensure coverage tracking works 
    // Read input vectors 
    std::ifstream infile("output.json"); 
    // std::ifstream infile("input_vectors.json"); 
    if (!infile.is_open()) { 
        std::cerr << "❌ Failed to open input_vectors.json" << std::endl; 
        return 1; 
    } 
    json input_json; 
    infile >> input_json; std::vector<std::string> input_order = load_input_signal_order("signal_info.txt"); 
    vluint64_t sim_time = 0; 
    size_t cycle = 0; 

//         // -------------------------
//         // Sequential DUT with clock
//         // -------------------------

    // while (cycle < input_json.size()) {
    //     // 1️⃣ Apply input vector
    //     const auto& cycle_input = input_json[cycle];
    //     std::unordered_map<std::string, int> values;
    //     for (auto& [key, val] : cycle_input.items()) {
    //         values[key] = std::stoi(val.get<std::string>());
    //     }

    //     std::vector<bool> bitstream;
    //     for (const std::string& sig : input_order) {
    //         std::string base = sig;
    //         size_t idx = sig.find('[');
    //         int bit = 0;
    //         if (idx != std::string::npos) {
    //             base = sig.substr(0, idx);
    //             bit = std::stoi(sig.substr(idx + 1, sig.find(']') - idx - 1));
    //         }
    //         int value = values.count(base) ? values[base] : 0;
    //         bitstream.push_back((value >> bit) & 1);
    //     }

    //     fuzz_poke(bitstream, top_1.get());

    //     // 2️⃣ Generate rising edge
    //     top_1->clk = 0; top_1->eval(); contextp->timeInc(1);  // falling edge
    //     top_1->clk = 1; top_1->eval(); contextp->timeInc(1);  // rising edge

    //     ++cycle;  // move to next vector
    // }
    while (cycle < input_json.size()) 
    { 
        contextp->timeInc(1); 
        top_1->clk = !top_1->clk; 
        if (!top_1->clk) { 
            // Apply input vector at falling edge 
            const auto& cycle_input = input_json[cycle]; 
            std::unordered_map<std::string, int> values; 
            for (auto& [key, val] : cycle_input.items()) {
                std::string str_val = val.get<std::string>();
                // Convert binary string to integer
                values[key] = std::stoi(str_val, nullptr, 2);
            }
            std::vector<bool> bitstream; 
            for (const std::string& sig : input_order) { 
                std::string base = sig; 
                size_t idx = sig.find('['); 
                int bit = 0; 
                if (idx != std::string::npos) { 
                    base = sig.substr(0, idx); 
                    bit = std::stoi(sig.substr(idx + 1, sig.find(']') - idx - 1)); 
                } 
                int value = values.count(base) ? values[base] : 0; 
                bitstream.push_back((value >> bit) & 1); 
            } 
            fuzz_poke(bitstream, top_1.get()); 
            ++cycle; 
        } 
        top_1->eval(); 
    }  



    
        // -------------------------
        // Combinational DUT without clock comment it if sequential design is used
        // -------------------------

    // while (cycle < input_json.size()) {
    //         contextp->timeInc(1);

    //         const auto& cycle_input = input_json[cycle];
    //         std::unordered_map<std::string, int> values;
    //         for (auto& [key, val] : cycle_input.items()) {
    //             values[key] = std::stoi(val.get<std::string>());
    //         }

    //         std::vector<bool> bitstream;
    //         for (const std::string& sig : input_order) {
    //             std::string base = sig;
    //             size_t idx = sig.find('[');
    //             int bit = 0;
    //             if (idx != std::string::npos) {
    //                 base = sig.substr(0, idx);
    //                 bit = std::stoi(sig.substr(idx + 1, sig.find(']') - idx - 1));
    //             }
    //             int value = values.count(base) ? values[base] : 0;
    //             bitstream.push_back((value >> bit) & 1);
    //         }

    //         fuzz_poke(bitstream, top_1.get());
    //         ++cycle;

    //         top_1->eval();
    //     }
    

   top_1->final();
   ensure_directory_exists("cov_total");

    // Write current coverage data
    const std::string cov_path = "logs/coverage.dat";
    contextp->coveragep()->write(cov_path.c_str());

    // Merge coverage using verilator_coverage tool
    const std::string cov_total = "cov_total/coverage.dat.total";

    std::string cmd;
    
    if (std::ifstream(cov_total).good()) {
        // Merge existing total with new coverage
        cmd = "verilator_coverage --write " + cov_total + " " + cov_total + " " + cov_path;
    } else {
        // Create initial total file
        cmd = "verilator_coverage --write " + cov_total + " " + cov_path;
    }

    int result = system(cmd.c_str());
    if (result != 0) {
        std::cerr << "❌ Coverage merge failed with exit code " << result << std::endl;
        return 1;
    }

    std::cout << "✅ Coverage merged successfully. Total: " << cov_total << std::endl;
    return 0;
}