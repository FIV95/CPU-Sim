mod memory;
mod cpu; // Add the CPU module

use memory::Memory;

    // Initialize memory
    fn main() {
        // Initialize memory
        let mut memory = Memory::new();
    
        // Load memory from the data file
        let data_file_path = "data/data_input.txt";
        memory.read_start_data(data_file_path);
    
        // Debug print the memory
        for (address, value) in &memory.data {
            println!("Address: 0x{:02X}, Value: {:032b}", address, value);
        }
    
        // Load instructions from the instruction file
        let instruction_file_path = "data/instruction_input.txt";
        memory.read_start_instructions(instruction_file_path);

        // Debug print the memory after processing instructions
        for (address, value) in &memory.data {
            println!("Address: 0x{:02X}, Value: {:032b}", address, value);
        }
    }
