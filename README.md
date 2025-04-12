# Rust Memory Architecture Simulator

## Overview
This project simulates a memory architecture with cache hierarchy and instruction execution. The simulator includes:

- Memory hierarchy (L1 Cache, L2 Cache, Main Memory)
- Instruction Set Architecture (ISA) with x86-like assembly support
- Detailed debugging and performance metrics

## Recent Changes

### Cache Simulation Improvements
- **Simplified Cache Line Size**: Changed to 1-byte cache lines for more intuitive and consistent behavior
- **Enhanced Cache Statistics**: Improved tracking of hits, misses, and hit rates
- **Memory Access Patterns**: Better simulation of memory access patterns and cache behavior
- **Cache Hierarchy**: L1 (64B, 2-way) → L2 (256B, 4-way) → Main Memory (1KB)

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
- **Memory Operation Tracking**: Logs all memory reads and writes with cache interaction
- **Cache Performance Metrics**: Real-time tracking of cache hits, misses, and hit rates
- **Register State Tracking**: Monitors register values before and after each instruction

### Example Programs
- `x86_bubble_sort.asm`: A bubble sort implementation using x86-style assembly
- `test_program.txt`: Memory and cache testing program

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
- **LOAD**: Load value from memory to register

## Memory Hierarchy
The simulator implements a three-level memory hierarchy:

### L1 Cache
- Size: 64 bytes
- Associativity: 2-way
- Line size: 1 byte
- Write policy: Write-through
- Access time: 1ns

### L2 Cache
- Size: 256 bytes
- Associativity: 4-way
- Line size: 1 byte
- Write policy: Write-back
- Access time: 10ns

### Main Memory
- Size: 1KB
- Access time: 100ns

## Debugging
The simulator writes detailed debug information to `debug.txt`, including:

- Instruction execution trace
- Register state changes
- Memory operations with cache interaction
- Control flow decisions
- Performance metrics
- Cache statistics (hits, misses, hit rates)

## Future Improvements
- Support for more x86 instructions
- Enhanced visualization of memory and cache state
- Performance optimization
- More example programs
- GUI improvements for cache visualization
