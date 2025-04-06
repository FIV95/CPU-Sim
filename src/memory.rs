use std::collections::HashMap;
use crate::cpu::CPU; // Import the CPU struct

pub const MEMORY_ACCESS_COST: u32 = 10;


pub struct Memory {
    pub data: HashMap<u8, u32>, // 64 addresses, each holding a 32-bit value
}

impl Memory {
    // Constructor to initialize an empty memory
    pub fn new() -> Self {
        Memory {
            data: HashMap::new(),
        }
    }

    // Method to load data into memory from a file
    pub fn read_start_data(&mut self, file_path: &str) {
        use std::fs::File;
        use std::io::{self, BufRead};

        if let Ok(file) = File::open(file_path) {
            let reader = io::BufReader::new(file);

            for line in reader.lines() {
                if let Ok(line) = line {
                    let parts: Vec<&str> = line.split_whitespace().collect();
                    if parts.len() == 2 {
                        if let (Ok(address), Ok(value)) = (
                            u8::from_str_radix(parts[0].trim_start_matches("0x"), 16),
                            u32::from_str_radix(parts[1], 2),
                        ) {
                            self.data.insert(address, value);
                        }
                    }
                }
            }
        } else {
            eprintln!("Failed to open file: {}", file_path);
        }
    }

    // Method to load instructions into memory from a file
    pub fn read_start_instructions(&mut self, file_path: &str) {
        use std::fs::File;
        use std::io::{self, BufRead};

        if let Ok(file) = File::open(file_path) {
            let reader = io::BufReader::new(file);

            for line in reader.lines() {
                if let Ok(line) = line {
                    let parts: Vec<&str> = line.split_whitespace().collect();
                    if parts.len() == 2 {
                        if let (Ok(address), Ok(instruction)) = (
                            u8::from_str_radix(parts[0].trim_start_matches("0x"), 16),
                            u32::from_str_radix(parts[1], 2),
                        ) {
                            self.data.insert(address, instruction);
                        }
                    }
                }
            }
        } else {
            eprintln!("Failed to open file: {}", file_path);
        }
    }
}
