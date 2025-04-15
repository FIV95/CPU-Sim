# CPU Architecture Simulator

## Overview
This project simulates a CPU architecture with memory hierarchy and instruction execution. The simulator includes:

- Memory hierarchy (L1 Cache, L2 Cache, Main Memory)
- Custom assembly language with simple instruction set
- GUI-based visualization of memory and cache states
- Detailed debugging and performance metrics

## Recent Changes

### GUI Improvements
- **Memory Display Window**: Added real-time memory value display
- **Cache Visualization**: Enhanced cache state visualization
- **Interactive Controls**: Step-by-step execution and program loading

### Cache Simulation Improvements
- **Simplified Cache Line Size**: Changed to 1-byte cache lines for more intuitive and consistent behavior
- **Enhanced Cache Statistics**: Improved tracking of hits, misses, and hit rates
- **Memory Access Patterns**: Better simulation of memory access patterns and cache behavior
- **Cache Hierarchy**: L1 (64B, 2-way) → L2 (256B, 4-way) → Main Memory (1KB)

### Custom Assembly Language
The simulator implements a simple assembly language with the following features:

- **Memory Operations**: LOAD, STORE, MOV
- **Arithmetic**: ADD, SUB
- **Bitwise**: AND, OR, XOR
- **Shifts**: SHL, SHR
- **Comparison**: CMP
- **Control Flow**: JMP, JZ, JNZ

### Improved Debugging
Added comprehensive debugging capabilities:

- **Instruction Trace**: Detailed logging of each instruction execution
- **Control Flow Tracking**: Records all jumps and branches
- **Memory Operation Tracking**: Logs all memory reads and writes with cache interaction
- **Cache Performance Metrics**: Real-time tracking of cache hits, misses, and hit rates
- **Register State Tracking**: Monitors register values before and after each instruction

### Example Programs
- `tests/test_program.txt`: Comprehensive test program demonstrating memory operations, cache interactions, and instruction execution

## Usage

### Running the Simulator
```bash
# Run with a specific program file
python gui/simulator_gui.py tests/test_program.txt

# Run without a program file (load one through the GUI)
python gui/simulator_gui.py
```

### Writing Assembly Programs
Assembly programs should follow our custom syntax:

```
; Comments start with ;
LABEL:
    INSTRUCTION OPERAND1 OPERAND2
```

### Supported Instructions
- **MOV**: Move data between registers and memory
- **LOAD**: Load value from memory to register
- **STORE**: Store value from register to memory
- **ADD**: Add two values
- **SUB**: Subtract two values
- **AND**: Bitwise AND
- **OR**: Bitwise OR
- **XOR**: Bitwise XOR
- **SHL**: Shift left
- **SHR**: Shift right
- **CMP**: Compare two values
- **JMP**: Unconditional jump
- **JZ/JNZ**: Jump if zero/not zero

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

## Project Structure
```
.
├── gui/
│   └── simulator_gui.py    # GUI implementation
├── tests/
│   └── test_program.txt    # Test program
├── cache/                  # Cache implementation
├── utils/                  # Utility functions
├── isa.py                  # Instruction Set Architecture
├── memory.py              # Memory implementation
├── main.py                # Main entry point
├── instructions.txt       # Instruction documentation
├── INSTRUCTION_ADDITION.md # Instruction addition guidelines
├── TODO.md               # Planned improvements
├── FUTURE_IMPROVEMENTS.txt # Detailed future plans
└── README.md             # This file
```

## Debugging
The simulator provides real-time debugging information through the GUI, including:

- Instruction execution trace
- Register state changes
- Memory operations with cache interaction
- Control flow decisions
- Performance metrics
- Cache statistics (hits, misses, hit rates)

## Future Improvements
- Support for more instructions
- Enhanced cache visualization
- Performance optimization
- Additional test programs
