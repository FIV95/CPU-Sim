use eframe::egui::{self, CentralPanel, Ui, RichText};
use crate::{cpu::{CPU, DecodedInstruction}, memory::Memory, cache::Cache};
use crate::memory::WordKind;

// App structure - holds all state
pub struct MyApp {
    cpu: CPU,
    memory: Memory,
    cache: Cache,
    user_code: String, // Text area content
    compiled_instructions: Vec<u32>, // Compiled instructions
    running: bool,
    last_step: f64, // For timing the step updates
}

// Constructor and implementation
impl MyApp {
    pub fn new(cpu: CPU, memory: Memory, cache: Cache) -> Self {
        Self { 
            cpu, 
            memory, 
            cache,
            user_code: String::new(),
            compiled_instructions: Vec::new(),
            running: false,
            last_step: 0.0,
        }
    }

    // Code compilation methods
    fn compile_code(&self, code: &str) -> Vec<u32> {
        let mut instructions = Vec::new();
        
        for line in code.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with("#") {
                continue; // Skip empty lines and comments
            }
            
            // Simple pattern matching for Python-like code
            if let Some(inst) = self.translate_line_to_instruction(line) {
                instructions.push(inst);
            } else {
                println!("Cannot compile line: {}", line);
            }
        }
        
        instructions
    }
    
    fn translate_line_to_instruction(&self, line: &str) -> Option<u32> {
        // Match patterns like "r1 = r2 + r3" or "load r1, 32"
        if line.contains("=") && line.contains("+") {
            // Addition: "r1 = r2 + r3"
            let parts: Vec<&str> = line.split(&['=', '+'][..]).map(|s| s.trim()).collect();
            if parts.len() == 3 {
                let dest = self.parse_register(parts[0])?;
                let src1 = self.parse_register(parts[1])?;
                let src2 = self.parse_register(parts[2])?;
                
                // Build ADD instruction (opcode 0, funct 0x20)
                return Some(self.build_r_type(0, src1, src2, dest, 0, 0x20));
            }
        } else if line.starts_with("load") {
            // Load word: "load r1, 32"
            let parts: Vec<&str> = line[4..].split(',').map(|s| s.trim()).collect();
            if parts.len() == 2 {
                let dest = self.parse_register(parts[0])?;
                let offset = parts[1].parse::<u16>().ok()?;
                
                // Build LW instruction (opcode 0x23)
                return Some(self.build_i_type(0x23, 0, dest, offset));
            }
        }
        // Add more patterns for other instructions
        
        None
    }
    
    fn parse_register(&self, reg: &str) -> Option<u8> {
        // Handle "r0", "r1", etc.
        if reg.starts_with('r') {
            if let Ok(num) = reg[1..].parse::<u8>() {
                if num < 32 {
                    return Some(num);
                }
            }
        }
        None
    }
    
    fn build_r_type(&self, opcode: u8, rs: u8, rt: u8, rd: u8, shamt: u8, funct: u8) -> u32 {
        ((opcode as u32) << 26) | ((rs as u32) << 21) | ((rt as u32) << 16) |
        ((rd as u32) << 11) | ((shamt as u32) << 6) | (funct as u32)
    }
    
    fn build_i_type(&self, opcode: u8, rs: u8, rt: u8, imm: u16) -> u32 {
        ((opcode as u32) << 26) | ((rs as u32) << 21) | ((rt as u32) << 16) | (imm as u32)
    }
    
    // Simulation control methods
    fn load_compiled_instructions(&mut self) {
        // Reset memory
        for addr in 0..self.compiled_instructions.len() {
            if addr < 64 {  // Assuming 64 addresses max
                let addr_u8 = addr as u8;
                self.memory.data.insert(addr_u8, self.compiled_instructions[addr]);
                self.memory.kinds.insert(addr_u8, WordKind::Instruction);
            }
        }
        
        // Reset CPU
        self.cpu = CPU::new();
    }
    
    fn step_cpu(&mut self) {
        self.cpu.step(&mut self.memory, &mut self.cache);
    }
    
    fn reset_simulation(&mut self) {
        self.cpu = CPU::new();
        self.memory = Memory::new();
        self.cache = Cache::new(4, 2);
        self.running = false;
    }
    
    fn get_operation_description(&self) -> String {
        // Get current instruction
        match self.memory.data.get(&(self.cpu.pc)) {
            Some(inst) => {
                let assembly = CPU::translate_to_assembly(*inst);
                format!("{} (0x{:08X})", assembly, inst)
            },
            None => "No instruction".to_string(),
        }
    }
    
    // UI drawing methods
    fn draw_code_editor(&mut self, ui: &mut Ui) {
        ui.group(|ui| {
            ui.set_min_size(egui::vec2(400.0, 300.0));
            ui.heading("Code Editor");
            
            // Multiline text editor
            ui.text_edit_multiline(&mut self.user_code);
            
            ui.horizontal(|ui| {
                if ui.button("Compile").clicked() {
                    self.compiled_instructions = self.compile_code(&self.user_code);
                    self.load_compiled_instructions();
                }
                
                if ui.button("Run").clicked() {
                    self.running = true;
                }
                
                if ui.button("Step").clicked() {
                    self.step_cpu();
                }
                
                if ui.button("Stop").clicked() {
                    self.running = false;
                }
                
                if ui.button("Reset").clicked() {
                    self.reset_simulation();
                }
            });
            
            // Add example/demo buttons
            ui.separator();
            ui.horizontal(|ui| {
                if ui.button("Example: Addition").clicked() {
                    self.user_code = "# Basic addition\nload r1, 10  # Load value 10 into r1\nload r2, 20  # Load value 20 into r2\nr3 = r1 + r2  # Add r1 and r2, store in r3\n".to_string();
                }
            });
        });
    }
}

// The egui App implementation
impl eframe::App for MyApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // If in running mode, step the CPU on each update
        if self.running && ctx.input(|i| i.time) - self.last_step > 0.25 {
            self.step_cpu();
            self.last_step = ctx.input(|i| i.time);
        }
        
        // UI layout
        CentralPanel::default().show(ctx, |ui| {
            ui.vertical_centered(|ui| {
                ui.horizontal_centered(|ui| {
                    self.draw_code_editor(ui);
                    ui.add_space(20.0);
                    ui.vertical(|ui| {
                        draw_control_block(ui, &self.cpu, &self.memory);
                        ui.label("    ⟶    ");
                        draw_cache_panel(ui, &self.cache);
                    });
                });
                
                ui.add_space(20.0);
                draw_memory_panel(ui, &self.memory, &self.cpu);
                
                // Status display
                ui.label(format!("CPU Cycle: {}", self.cpu.cycle));
                ui.label(format!("Last Operation: {}", self.get_operation_description()));
            });
        });
    }
}

// These drawing functions should be outside the impl blocks since they're not methods
fn draw_control_block(ui: &mut Ui, cpu: &CPU, memory: &Memory) {
    ui.group(|ui| {
        ui.set_min_size(egui::vec2(300.0, 400.0));
        ui.set_max_size(egui::vec2(300.0, 400.0));

        ui.vertical_centered(|ui| {
            ui.heading("CPU");

            ui.add_space(10.0);

            // Control Unit and ALU Section
            ui.horizontal(|ui| {
                // Control Unit
                ui.group(|ui| {
                    ui.set_min_size(egui::vec2(140.0, 100.0));
                    ui.set_max_size(egui::vec2(140.0, 100.0));
                    ui.style_mut().visuals.override_text_color = Some(egui::Color32::WHITE);
                    ui.style_mut().visuals.widgets.inactive.bg_fill = egui::Color32::from_rgb(128, 0, 128);
                    ui.vertical_centered(|ui| {
                        ui.heading("Control Unit");
                    });
                });

                ui.add_space(10.0);

                // ALU
                ui.group(|ui| {
                    ui.set_min_size(egui::vec2(140.0, 100.0));
                    ui.set_max_size(egui::vec2(140.0, 100.0));
                    ui.style_mut().visuals.override_text_color = Some(egui::Color32::WHITE);
                    ui.style_mut().visuals.widgets.inactive.bg_fill = egui::Color32::from_rgb(0, 0, 128);
                    ui.vertical_centered(|ui| {
                        ui.heading("ALU");
                        ui.label("+ - × ÷");
                        ui.label(format!("Current: {}", cpu.get_current_instruction_name(memory)));
                    });
                });
            });

            ui.add_space(10.0);

            // Registers Section
            ui.group(|ui| {
                ui.set_min_size(egui::vec2(280.0, 300.0));
                ui.set_max_size(egui::vec2(280.0, 300.0));
                ui.vertical(|ui| {
                    ui.heading("Registers (32 bits)");

                    ui.add_space(5.0);

                    // Display registers in a 4x8 grid
                    for row in 0..4 {
                        ui.horizontal(|ui| {
                            for col in 0..8 {
                                let i = row * 8 + col;

                                ui.group(|ui| {
                                    ui.set_min_size(egui::vec2(48.0, 34.0));
                                    ui.set_max_size(egui::vec2(48.0, 34.0));
                                    ui.vertical_centered(|ui| {
                                        ui.label(
                                            RichText::new(format!("R{}", i))
                                                .monospace()
                                                .size(10.0),
                                        );
                                        ui.label(
                                            RichText::new(cpu.registers[i].to_string())
                                                .monospace()
                                                .size(10.0),
                                        );
                                    });
                                });
                            }
                        });
                    }
                });
            });
        });
    });
}

fn draw_cache_panel(ui: &mut Ui, cache: &Cache) {
    ui.group(|ui| {
        ui.set_min_size(egui::vec2(300.0, 400.0));
        ui.set_max_size(egui::vec2(300.0, 400.0));
        
        ui.vertical_centered(|ui| {
            ui.heading("Cache");
            ui.add_space(10.0);
            
            // Display cache structure: 4 sets, each with 2 blocks
            for set_idx in 0..4 {
                ui.group(|ui| {
                    ui.set_min_size(egui::vec2(280.0, 80.0));
                    ui.set_max_size(egui::vec2(280.0, 80.0));
                    
                    ui.vertical_centered(|ui| {
                        ui.label(RichText::new(format!("Set {}", set_idx)).heading());
                        
                        // Display the 2 blocks in this set
                        for block_idx in 0..2 {
                            ui.group(|ui| {
                                ui.set_min_size(egui::vec2(260.0, 25.0));
                                ui.set_max_size(egui::vec2(260.0, 25.0));
                                
                                // Get block data if it exists in the cache
                                let block_info = match cache.sets.get(&(set_idx as u8)) {
                                    Some(set) => {
                                        if block_idx < set.blocks.len() {
                                            let block = &set.blocks[block_idx];
                                            format!("Tag: 0x{:02X}, Data: {}", block.tag, block.data)
                                        } else {
                                            "Empty".to_string()
                                        }
                                    },
                                    None => "Empty".to_string()
                                };
                                
                                ui.horizontal_centered(|ui| {
                                    ui.label(format!("Block {}: {}", block_idx, block_info));
                                });
                            });
                            ui.add_space(2.0);
                        }
                    });
                });
                ui.add_space(5.0);
            }
        });
    });
}

fn draw_memory_panel(ui: &mut Ui, memory: &Memory, cpu: &CPU) {
    ui.group(|ui| {
        ui.set_min_size(egui::vec2(800.0, 400.0));
        ui.heading("Memory / RAM (64 words)");

        for row in 0..8 {
            ui.horizontal(|ui| {
                for col in 0..8 {
                    let addr = row * 8 + col;
                    let addr_u8 = addr as u8;
                    
                    // Get memory value and type
                    let value = memory.data.get(&addr_u8).copied();
                    let kind = memory.kinds.get(&addr_u8);
                    
                    // Check if this is the current instruction
                    let is_current = cpu.pc == addr_u8;
                    
                    // Determine display text
                    let display_text = match (value, kind) {
                        (Some(word), Some(WordKind::Instruction)) => {
                            match CPU::decode(word) {
                                DecodedInstruction::Instruction(asm) => asm,
                                _ => format!("{}", word),
                            }
                        },
                        (Some(word), Some(WordKind::Data)) => format!("{}", word),
                        (Some(word), None) => format!("{}", word),
                        (None, _) => "--".to_string(),
                    };
                    
                    // Create styled text
                    let mut label_text = RichText::new(format!("0x{:02X}\n{}", addr, display_text))
                        .monospace();
                    
                    // Highlight current instruction
                    if is_current {
                        label_text = label_text
                            .background_color(egui::Color32::from_rgb(0, 128, 0))
                            .color(egui::Color32::WHITE);
                    }
                    
                    // Draw the memory cell
                    ui.group(|ui| {
                        ui.set_min_size(egui::vec2(100.0, 48.0));
                        ui.vertical_centered(|ui| {
                            ui.label(label_text);
                        });
                    });
                }
            });
        }
    });
}