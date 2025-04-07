mod memory;
mod cpu;
mod cache;
mod gui;

use memory::Memory;
use cpu::CPU;
use cache::Cache;
use std::io::{self, Write};
use std::time::Duration;
use std::thread;

use eframe::egui;
use gui::MyApp;

fn main() -> Result<(), eframe::Error> {
    // First, ask the user which version they want to run
    println!("===================================================");
    println!("    Welcome to the CPU Simulator                   ");
    println!("===================================================");
    println!("\nThis simulator demonstrates how a CPU works with memory and cache.");
    println!("You can see the simulation step-by-step in the terminal or through a GUI.");
    
    println!("\nWould you like to run the:");
    println!("1) Terminal Version (step-by-step with detailed output)");
    println!("2) GUI Version (visual representation of the CPU)");
    print!("\nEnter your choice (1 or 2): ");
    io::stdout().flush().unwrap();
    
    let mut choice = String::new();
    io::stdin().read_line(&mut choice).unwrap();
    
    match choice.trim() {
        "1" => run_terminal_version(),
        _ => run_gui_version(),
    }
}

fn run_gui_version() -> Result<(), eframe::Error> {
    // Load memory and instructions
    let mut memory = Memory::new();
    memory.read_start_data("data/data_input.txt");
    memory.read_start_instructions("data/instruction_input.txt");

    // Create CPU and Cache
    let cpu = CPU::new();
    let cache = Cache::new(4, 2);  // 4 sets, 2 blocks per set
    
    // Launch the GUI app
    let options = eframe::NativeOptions::default();
    eframe::run_native(
        "CPU Simulator",
        options,
        Box::new(|_cc| Box::new(MyApp::new(cpu, memory, cache))),
    )
}

// Modify the run_terminal_version function to not clear the screen between steps

fn run_terminal_version() -> Result<(), eframe::Error> {
    println!("===================================================");
    println!("    CPU Simulator - Terminal Version               ");
    println!("===================================================");
    
    // Show the python program that will be executed
    println!("\nThe following Python program will be simulated:");
    println!("----------------------------------------------");
    display_sample_program();
    println!("----------------------------------------------");
    println!("\nThis program has been converted to assembly instructions");
    println!("and then to binary machine code that our CPU can execute.");
    
    println!("\nPress Enter to start the simulation...");
    wait_for_enter();
    
    // Load memory and instructions
    let mut memory = Memory::new();
    memory.read_start_data("data/data_input.txt");
    memory.read_start_instructions("data/instruction_input.txt");

    // Create CPU and Cache
    let mut cpu = CPU::new();
    let mut cache = Cache::new(4, 2);  // 4 sets, 2 blocks per set
    
    // Map of instruction addresses to Python lines for display
    let instruction_to_python = create_instruction_to_python_map();
    
    // Execute the program step by step
    let mut step_count = 1;
    while !cpu.halted {
        // Removed clear_screen() to keep all output visible
        println!("===================================================");
        println!("    CPU Simulator - Step {}                        ", step_count);
        println!("===================================================");
        
        // Show the current Python line being executed
        if let Some(python_line) = instruction_to_python.get(&cpu.pc) {
            println!("\nExecuting Python: \x1b[32m{}\x1b[0m", python_line);
        }
        
        // Show the current CPU state
        println!("\nCPU State:");
        println!("  PC: 0x{:02X}", cpu.pc);
        println!("  Cycle: {}", cpu.cycle);
        
        // Show registers (only non-zero for cleanliness)
        println!("\nRegisters:");
        for i in 0..32 {
            if cpu.registers[i] != 0 {
                println!("  R{}: {}", i, cpu.registers[i]);
            }
        }
        
        // Show cache status
        println!("\nCache Status:");
        println!("  Hits: {}", cache.hits);
        println!("  Misses: {}", cache.misses);
        println!("  Hit Rate: {:.2}%", cache.get_hit_rate() * 100.0);
        
        // Show cache contents
        println!("\nCache Contents:");
        for set_idx in 0..cache.num_sets {
            if let Some(set) = cache.sets.get(&(set_idx as u8)) {
                println!("  Set {}: ", set_idx);
                for (block_idx, block) in set.blocks.iter().enumerate() {
                    if block.valid {
                        println!("    Block {}: Tag: 0x{:02X}, Data: {}", block_idx, block.tag, block.data);
                    } else {
                        println!("    Block {}: Empty", block_idx);
                    }
                }
            } else {
                println!("  Set {}: Empty", set_idx);
            }
        }
        
        // Show the instruction about to be executed
        if let Some(instruction) = memory.data.get(&cpu.pc) {
            let assembly = CPU::translate_to_assembly(*instruction);
            println!("\nCurrent Instruction (0x{:02X}): {}", cpu.pc, assembly);
            
            // Execute a single step and capture details
            println!("\nExecuting instruction...");
            
            // Now actually execute the instruction
            cpu.step(&mut memory, &mut cache);
            
            println!("\nPress Enter for next step or 'q' to quit...");
            if wait_for_enter_or_quit() {
                break;
            }
            
            step_count += 1;
        } else {
            println!("\nNo instruction at address 0x{:02X}. Halting simulation.", cpu.pc);
            cpu.halted = true;
            
            println!("\nPress Enter to continue...");
            wait_for_enter();
        }
    }
    
    // Show final state (no need to clear screen)
    println!("===================================================");
    println!("    CPU Simulator - Final State                    ");
    println!("===================================================");
    
    // Show the final CPU state
    println!("\nFinal CPU State:");
    println!("  PC: 0x{:02X}", cpu.pc);
    println!("  Cycle: {}", cpu.cycle);
    println!("  Halted: {}", cpu.halted);
    
    // Show registers (only non-zero for cleanliness)
    println!("\nFinal Register Values:");
    for i in 0..32 {
        if cpu.registers[i] != 0 {
            println!("  R{}: {}", i, cpu.registers[i]);
        }
    }
    
    // Show cache stats
    println!("\nCache Statistics:");
    println!("  Hits: {}", cache.hits);
    println!("  Misses: {}", cache.misses);
    println!("  Hit Rate: {:.2}%", cache.get_hit_rate() * 100.0);
    
    // Show output of the program (values at memory locations 40, 44, 48)
    println!("\nProgram Output:");
    if let Some(c) = memory.data.get(&40) {
        println!("  c = {}", c);
    }
    if let Some(d) = memory.data.get(&44) {
        println!("  d = {}", d);
    }
    if let Some(f) = memory.data.get(&48) {
        println!("  f = {}", f);
    }
    
    println!("\nPress Enter to return to the main menu...");
    wait_for_enter();
    
    run_gui_version() // After terminal version is done, launch the GUI
}

fn display_sample_program() {
    match std::fs::read_to_string("data/sample_program.txt") {
        Ok(contents) => println!("{}", contents),
        Err(_) => println!(r#"# A practical Python program that demonstrates cache behavior
def calculate_values():
    # Initialize values
    a = 10
    b = 20
    
    # Create a small array/list and fill it
    data = [0] * 5
    data[0] = a        # Store a at index 0
    data[1] = b        # Store b at index 1
    data[2] = a + b    # Calculate and store c
    
    # Conditional logic
    if data[0] < data[1]:  # Compare values from array
        data[3] = 10       # Set if true
    else:
        data[3] = 0        # Set if false
    
    # More calculations
    data[4] = data[2] - data[0]  # Calculate using array values
    
    # Process the data multiple times (to demonstrate cache hits)
    total = 0
    for i in range(3):
        # Accessing the same array elements repeatedly causes cache hits
        total += data[2] + data[3]
    
    # Return results
    return data[2], data[3], data[4]

# Call the function
result_c, result_d, result_f = calculate_values()
print(f"c = {{result_c}}, d = {{result_d}}, f = {{result_f}}")"#)
    }
}

fn create_instruction_to_python_map() -> std::collections::HashMap<u8, String> {
    let mut map = std::collections::HashMap::new();
    
    // Map each instruction address to the corresponding Python line
    map.insert(0, "a = 10".to_string());
    map.insert(1, "b = 20".to_string());
    map.insert(2, "data[0] = a".to_string());
    map.insert(3, "data[1] = b".to_string());
    map.insert(4, "Calculate a + b".to_string());
    map.insert(5, "data[2] = a + b".to_string());
    map.insert(6, "Loading data[0] for comparison".to_string());
    map.insert(7, "Loading data[1] for comparison".to_string());
    map.insert(8, "if data[0] < data[1]:".to_string());
    map.insert(9, "Checking branch condition".to_string());
    map.insert(10, "data[3] = 10 (inside if block)".to_string());
    map.insert(11, "Storing to data[3]".to_string());
    map.insert(12, "Skip else block".to_string());
    map.insert(13, "data[3] = 0 (inside else block - skipped)".to_string());
    map.insert(14, "Storing to data[3] (skipped)".to_string());
    map.insert(15, "Loading data[2] for calculation".to_string());
    map.insert(16, "Loading data[0] for calculation".to_string());
    map.insert(17, "data[4] = data[2] - data[0]".to_string());
    map.insert(18, "Storing to data[4]".to_string());
    map.insert(19, "total = 0".to_string());
    map.insert(20, "i = 0".to_string());
    map.insert(21, "Starting loop: for i in range(3):".to_string());
    map.insert(22, "Checking if i < 3".to_string());
    map.insert(23, "Loop condition check".to_string());
    map.insert(24, "Loading data[2] (iteration 1)".to_string());
    map.insert(25, "Loading data[3] (iteration 1)".to_string());
    map.insert(26, "Calculating data[2] + data[3]".to_string());
    map.insert(27, "total += data[2] + data[3]".to_string());
    map.insert(28, "i += 1".to_string());
    map.insert(29, "Jump back to loop start".to_string());
    map.insert(30, "Preparing return values".to_string());
    map.insert(31, "Loading return value c (data[2])".to_string());
    map.insert(32, "Loading return value d (data[3])".to_string());
    map.insert(33, "Loading return value f (data[4])".to_string());
    map.insert(34, "Storing c to memory[40]".to_string());
    map.insert(35, "Storing d to memory[44]".to_string());
    map.insert(36, "Storing f to memory[48]".to_string());
    
    map
}

fn clear_screen() {
    // For Windows
    if cfg!(target_os = "windows") {
        let _ = std::process::Command::new("cmd")
            .args(["/c", "cls"])
            .status();
    } 
    // For Unix-based systems (Linux, macOS)
    else {
        let _ = std::process::Command::new("clear")
            .status();
    }
}

fn wait_for_enter() {
    let mut buffer = String::new();
    io::stdout().flush().unwrap();
    io::stdin().read_line(&mut buffer).unwrap();
}

fn wait_for_enter_or_quit() -> bool {
    let mut buffer = String::new();
    io::stdout().flush().unwrap();
    io::stdin().read_line(&mut buffer).unwrap();
    
    buffer.trim().to_lowercase() == "q"
}