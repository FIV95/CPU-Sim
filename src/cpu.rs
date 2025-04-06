pub struct CPU;

impl CPU {
    // Function to translate binary instructions to assembly
    pub fn translate_to_assembly(instruction: u32) -> String {
      let opcode = (instruction >> 26) & 0b111111; // 6-bit opcode
  
      match opcode {
          0b000000 => {
              // R-type: check funct field
              let funct = instruction & 0b111111;
              match funct {
                  0b100000 => "ADD".to_string(),     // Add
                  0b100010 => "SUB".to_string(),     // Subtract
                  0b101010 => "SLT".to_string(),     // Set Less Than
                  0b011000 => "MULT".to_string(),    // Multiply
                  0b011010 => "DIV".to_string(),     // Divide
                  0b100100 => "
                  AND".to_string(),     // AND
                  0b100101 => "OR".to_string(),      // OR
                  0b000000 => "SLL".to_string(),     // Shift Left Logical
                  0b000010 => "SRL".to_string(),     // Shift Right Logical
                  0b001000 => "JR".to_string(),      // Jump Register
                  _ => "UNKNOWN R-TYPE".to_string(),
              }
          }
          0b001000 => "ADDI".to_string(),     // Add Immediate
          0b000100 => "BEQ".to_string(),      // Branch if Equal
          0b000101 => "BNE".to_string(),      // Branch if Not Equal
          0b000010 => "J".to_string(),        // Jump
          0b000011 => "JAL".to_string(),      // Jump and Link
          0b100011 => "LW".to_string(),       // Load Word
          0b101011 => "SW".to_string(),       // Store Word
          0b101111 => "CACHE".to_string(),    // Cache operation (custom)
          0b111111 => "HALT".to_string(),     // Halt (custom)
          _ => "UNKNOWN".to_string(),
      }
  }
  
}