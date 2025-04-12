# Rust Memory Architecture Simulator

## Overview
This project simulates a memory architecture with cache hierarchy and instruction execution. The simulator includes:

- Memory hierarchy (L1 Cache, L2 Cache, Main Memory)
- Instruction Set Architecture (ISA) with x86-like assembly support
- Detailed debugging and performance metrics

## Recent Changes

### Enhanced ISA with x86 Assembly Support
We've expanded the ISA to support x86-style assembly instructions, including:

- **Conditional Jumps**: JZ, JNZ, JG, JL, JGE, JLE
- **Stack Operations**: PUSH, POP
- **Subroutine Calls**: CALL, RET
- **Comparison**: CMP (sets flags for conditional jumps)

### Improved Debugging
Added comprehensive debugging capabilities:

- **Instruction Trace**: Detailed logging of each instruction execution
- **Control Flow Tracking**: Records all jumps and branches
- **Memory Operation Tracking**: Logs all memory reads and writes
- **Comparison Results**: Tracks comparison operations and their results
- **Register State Tracking**: Monitors register values before and after each instruction

### Example Programs
- `x86_bubble_sort.asm`: A bubble sort implementation using x86-style assembly

## Usage

### Running the Simulator
```bash
python3 gui/simulator_gui.py
```

### Writing Assembly Programs
Assembly programs should follow the x86-like syntax:

```
# Comments start with #
LABEL:
    INSTRUCTION OPERAND1, OPERAND2
```

### Supported Instructions
- **MOV**: Move data between registers and memory
- **ADD**: Add two values
- **SUB**: Subtract two values
- **CMP**: Compare two values (sets flags)
- **JMP**: Unconditional jump
- **JZ/JNZ**: Jump if zero/not zero
- **JG/JL**: Jump if greater/less than
- **JGE/JLE**: Jump if greater or equal/less or equal
- **PUSH/POP**: Stack operations
- **CALL/RET**: Subroutine calls

## Debugging
The simulator writes detailed debug information to `debug.txt`, including:

- Instruction execution trace
- Register state changes
- Memory operations
- Control flow decisions
- Performance metrics

## Future Improvements
- Support for more x86 instructions
- Enhanced visualization of memory and cache state
- Performance optimization
- More example programs
