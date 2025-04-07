use crate::cache::Cache;
use crate::memory::{Memory, WordKind};

pub enum DecodedInstruction {
    Instruction(String),
    Immediate(u32),
    Address(u8),
    None,
}

pub struct CPU {
    pub registers: [u32; 32],
    pub pc: u8,
    pub cycle: u32,
    pub halted: bool,
}

impl CPU {
    pub fn new() -> Self {
        CPU {
            registers: [0; 32],
            pc: 0,
            cycle: 0,
            halted: false,
        }
    }

    // Instruction parsing helpers
    pub fn opcode(instruction: u32) -> u8 {
        ((instruction >> 26) & 0x3F) as u8
    }

    pub fn rs(instruction: u32) -> u8 {
        ((instruction >> 21) & 0x1F) as u8
    }

    pub fn rt(instruction: u32) -> u8 {
        ((instruction >> 16) & 0x1F) as u8
    }

    pub fn rd(instruction: u32) -> u8 {
        ((instruction >> 11) & 0x1F) as u8
    }

    pub fn shamt(instruction: u32) -> u8 {
        ((instruction >> 6) & 0x1F) as u8
    }

    pub fn funct(instruction: u32) -> u8 {
        (instruction & 0x3F) as u8
    }

    pub fn imm(instruction: u32) -> u16 {
        (instruction & 0xFFFF) as u16
    }

    pub fn get_current_instruction_name(&self, memory: &Memory) -> String {
        match memory.data.get(&self.pc) {
            Some(inst) => Self::translate_to_assembly(*inst),
            None => "None".to_string(),
        }
    }

    pub fn translate_to_assembly(instruction: u32) -> String {
        let opcode = Self::opcode(instruction);
        let rs = Self::rs(instruction);
        let rt = Self::rt(instruction);
        let rd = Self::rd(instruction);
        let funct = Self::funct(instruction);
        let imm = Self::imm(instruction);

        match opcode {
            0x00 => {
                // R-type
                match funct {
                    0x20 => format!("ADD R{}, R{}, R{}", rd, rs, rt),
                    0x22 => format!("SUB R{}, R{}, R{}", rd, rs, rt),
                    0x2A => format!("SLT R{}, R{}, R{}", rd, rs, rt),
                    _ => format!("R-type 0x{:X}", funct),
                }
            }
            0x08 => format!("ADDI R{}, R{}, {}", rt, rs, imm as i16),
            0x04 => format!("BEQ R{}, R{}, {}", rs, rt, imm as i16),
            0x23 => format!("LW R{}, {}(R{})", rt, imm as i16, rs),
            0x2B => format!("SW R{}, {}(R{})", rt, imm as i16, rs),
            _ => format!("Unknown 0x{:X}", opcode),
        }
    }

    pub fn decode(instruction: u32) -> DecodedInstruction {
        DecodedInstruction::Instruction(Self::translate_to_assembly(instruction))
    }

    pub fn step(&mut self, memory: &mut Memory, cache: &mut Cache) {
        if self.halted {
            return;
        }
    
        // Fetch instruction from memory
        let pc = self.pc;
        let instruction = memory.data.get(&pc).copied().unwrap_or(0);
    
        // Decode instruction
        let opcode = Self::opcode(instruction);
        let rs = Self::rs(instruction);
        let rt = Self::rt(instruction);
        let rd = Self::rd(instruction);
        let shamt = Self::shamt(instruction);
        let funct = Self::funct(instruction);
        let imm = Self::imm(instruction) as i16; // Use signed for branch offsets
    
        println!("Executing: {}", Self::translate_to_assembly(instruction));
    
        // Execute instruction
        match opcode {
            0x00 => {
                // R-type instructions
                match funct {
                    0x20 => {
                        // ADD: rd = rs + rt
                        self.registers[rd as usize] =
                            self.registers[rs as usize].wrapping_add(self.registers[rt as usize]);
                        println!(
                            "ADD: R{} = R{}({}) + R{}({}) = {}",
                            rd,
                            rs,
                            self.registers[rs as usize],
                            rt,
                            self.registers[rt as usize],
                            self.registers[rd as usize]
                        );
                        self.pc = self.pc.wrapping_add(1);
                    }
                    0x22 => {
                        // SUB: rd = rs - rt
                        self.registers[rd as usize] =
                            self.registers[rs as usize].wrapping_sub(self.registers[rt as usize]);
                        println!(
                            "SUB: R{} = R{}({}) - R{}({}) = {}",
                            rd,
                            rs,
                            self.registers[rs as usize],
                            rt,
                            self.registers[rt as usize],
                            self.registers[rd as usize]
                        );
                        self.pc = self.pc.wrapping_add(1);
                    }
                    0x2A => {
                        // SLT: rd = (rs < rt) ? 1 : 0
                        self.registers[rd as usize] = if (self.registers[rs as usize] as i32)
                            < (self.registers[rt as usize] as i32)
                        {
                            1
                        } else {
                            0
                        };
                        println!(
                            "SLT: R{} = (R{}({}) < R{}({})) = {}",
                            rd,
                            rs,
                            self.registers[rs as usize],
                            rt,
                            self.registers[rt as usize],
                            self.registers[rd as usize]
                        );
                        self.pc = self.pc.wrapping_add(1);
                    }
                    _ => {
                        println!("Unsupported R-type instruction: function 0x{:02X}", funct);
                        self.pc = self.pc.wrapping_add(1);
                    }
                }
            }
            0x08 => {
                // ADDI: rt = rs + imm
                self.registers[rt as usize] = self.registers[rs as usize].wrapping_add(imm as u32);
                println!(
                    "ADDI: R{} = R{}({}) + {} = {}",
                    rt, rs, self.registers[rs as usize], imm, self.registers[rt as usize]
                );
                self.pc = self.pc.wrapping_add(1);
            }
            0x04 => {
                // BEQ: Branch if equal
                println!(
                    "BEQ: R{}({}) == R{}({}) ? {}",
                    rs,
                    self.registers[rs as usize],
                    rt,
                    self.registers[rt as usize],
                    self.registers[rs as usize] == self.registers[rt as usize]
                );
    
                // Handle backward jumps (for loops) differently
                if imm < 0 {
                    println!("Loop jump: Going back {} instructions", -imm);
                    if self.registers[rs as usize] == self.registers[rt as usize] {
                        // Cast to i16 first to handle negative values correctly
                        self.pc = (self.pc as i16 + 1 + imm) as u8;
                        println!("Loop branch taken, new PC = 0x{:02X}", self.pc);
                    } else {
                        self.pc = self.pc.wrapping_add(1);
                        println!("Loop branch not taken, PC = 0x{:02X}", self.pc);
                    }
                } else {
                    // Regular forward branch
                    if self.registers[rs as usize] == self.registers[rt as usize] {
                        // Branch taken - PC is incremented by the immediate value
                        self.pc = self.pc.wrapping_add(1).wrapping_add(imm as u8);
                        println!("Branch taken, new PC = 0x{:02X}", self.pc);
                    } else {
                        // Branch not taken - PC is just incremented by 1
                        self.pc = self.pc.wrapping_add(1);
                        println!("Branch not taken, PC = 0x{:02X}", self.pc);
                    }
                }
            }
            0x23 => {
                // LW: Load word from memory (rt = MEM[rs + offset])
                let addr = (self.registers[rs as usize].wrapping_add(imm as u32) & 0xFF) as u8;
                println!(
                    "LW: Calculate address = R{}({}) + {} = 0x{:02X}",
                    rs, self.registers[rs as usize], imm, addr
                );
    
                // Always try cache first (should record miss if not found)
                let (data, cache_hit) = cache.read(addr);
    
                if cache_hit {
                    self.registers[rt as usize] = data;
                    println!(
                        "LW: Cache HIT at address 0x{:02X}, R{} = {}",
                        addr, rt, data
                    );
                } else {
                    // Explicitly forcing a MISS for the first access
                    println!("LW: Cache MISS at address 0x{:02X}", addr);
                    
                    // Cache miss - access memory
                    if let Some(data) = memory.data.get(&addr) {
                        self.registers[rt as usize] = *data;
                        // Update cache
                        cache.write(addr, *data);
                        println!(
                            "LW: Retrieved from memory, R{} = {}",
                            rt, *data
                        );
                    } else {
                        // Address not found in memory, create it with zero
                        self.registers[rt as usize] = 0;
                        memory.data.insert(addr, 0);
                        cache.write(addr, 0);
                        println!("LW: Memory address 0x{:02X} not found, initialized to 0, R{} = 0", addr, rt);
                    }
                }
    
                self.pc = self.pc.wrapping_add(1);
            }
            0x2B => {
                // SW: Store word to memory (MEM[rs + offset] = rt)
                let addr = (self.registers[rs as usize].wrapping_add(imm as u32) & 0xFF) as u8;
                let data = self.registers[rt as usize];
                println!("SW: Store R{}({}) to address 0x{:02X}", rt, data, addr);
    
                // Write to memory
                memory.data.insert(addr, data);
    
                // Also write to cache
                cache.write(addr, data);
                println!("SW: Updated memory and cache");
    
                self.pc = self.pc.wrapping_add(1);
            }
            _ => {
                println!("Unsupported instruction: opcode 0x{:02X}", opcode);
                self.pc = self.pc.wrapping_add(1);
            }
        }
    
        // Update the cycle counter
        self.cycle += 1;
    
        // Improve halting condition to check for instructions at higher addresses
        if !memory.data.contains_key(&self.pc) {
            println!("Program execution complete at PC 0x{:02X}. No more instructions found.", self.pc);
            self.halted = true;
        }
    }
}