from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum, auto
from time import time
import logging

# Import existing utilities
import sys
sys.path.append('..')
from utils.logger import Logger, LogLevel
from memory import Memory
from cache.cache import Cache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class InstructionType(Enum):
    """Types of instructions supported"""
    MOV = auto()    # Move data
    ADD = auto()    # Add values
    SUB = auto()    # Subtract values
    JMP = auto()    # Unconditional jump
    JZ = auto()     # Jump if zero
    JNZ = auto()    # Jump if not zero
    LOAD = auto()   # Load from memory
    HALT = auto()   # Stop execution

@dataclass
class Instruction:
    """Represents a single instruction"""
    type: InstructionType
    operands: List[str]
    line_number: int

class SimpleISA:
    def __init__(self, memory: Optional[Memory] = None, cache: Optional[Cache] = None):
        # Initialize registers
        self.registers = {
            'eax': 0,
            'ebx': 0,
            'ecx': 0,
            'edx': 0,
            'esi': 0,
            'edi': 0,
            'ebp': 0,
            'esp': 0
        }

        # Program state
        self.pc = 0  # Program counter
        self.instructions: List[Instruction] = []
        self.labels: Dict[str, int] = {}
        self.running = False

        # Memory system
        self.memory = memory
        self.cache = cache

        # Logging
        self.logger = Logger()

        # Statistics
        self.instruction_count = 0
        self.start_time = 0
        self.test_mode = True  # Enable test mode by default
        self.max_instructions = 100  # Limit execution in test mode
        self.end_time = 0

    def load_program(self, program: List[str]) -> None:
        """Load a program into the ISA"""
        self.instructions = []
        self.labels = {}
        self.pc = 0

        for i, line in enumerate(program):
            line = line.strip()
            if not line or line.startswith(';'):
                continue

            # Handle labels
            if line.endswith(':'):
                label = line[:-1].strip()
                self.labels[label] = len(self.instructions)
                self.logger.log(LogLevel.DEBUG, f"Found label {label} at instruction {len(self.instructions)}")
                continue

            # Split the line and filter out comments
            parts = line.split()
            instruction_parts = []
            for part in parts:
                if part.startswith(';'):
                    break
                instruction_parts.append(part)

            if not instruction_parts:
                continue

            # Convert instruction type
            try:
                inst_type = InstructionType[instruction_parts[0].upper()]
                operands = instruction_parts[1:]
                self.instructions.append(Instruction(inst_type, operands, i))
                self.logger.log(LogLevel.DEBUG, f"Loaded instruction: {inst_type.name} {operands}")
            except KeyError:
                self.logger.log(LogLevel.ERROR, f"Unknown instruction: {instruction_parts[0]}")

    def execute_step(self) -> bool:
        """Execute one instruction"""
        if not self.running or self.pc >= len(self.instructions):
            return False

        # Check test mode instruction limit
        if self.test_mode and self.instruction_count >= self.max_instructions:
            self.logger.log(LogLevel.WARNING, f"Test mode: Reached maximum instruction limit ({self.max_instructions})")
            self.running = False
            return False

        instruction = self.instructions[self.pc]
        self.logger.log(LogLevel.INFO, f"\nExecuting instruction {self.pc}: {instruction.type.name} {instruction.operands}")

        # Execute instruction
        try:
            # Default behavior: increment PC before execution
            next_pc = self.pc + 1

            if instruction.type == InstructionType.MOV:
                self._execute_mov(instruction.operands)
            elif instruction.type == InstructionType.ADD:
                self._execute_add(instruction.operands)
            elif instruction.type == InstructionType.SUB:
                self._execute_sub(instruction.operands)
            elif instruction.type == InstructionType.JMP:
                next_pc = self._execute_jmp(instruction.operands)
            elif instruction.type == InstructionType.JZ:
                next_pc = self._execute_jz(instruction.operands)
            elif instruction.type == InstructionType.JNZ:
                next_pc = self._execute_jnz(instruction.operands)
            elif instruction.type == InstructionType.LOAD:
                self._execute_load(instruction.operands)
            elif instruction.type == InstructionType.HALT:
                self.running = False
                return False

            # Update PC after execution
            self.pc = next_pc
            self.instruction_count += 1
            self._print_state()
            return True

        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error executing instruction: {str(e)}")
            self.running = False
            return False

    def _execute_mov(self, operands: List[str]) -> None:
        """Execute MOV instruction"""
        if len(operands) != 2:
            raise ValueError("MOV requires 2 operands")

        dest, src = operands

        # Get source value
        if src.startswith('#'):
            value = int(src[1:])
            # Log register operation with enhanced visualization
            self.logger.log_register_operation('mov', {
                'dest': dest,
                'value': value,
                'source': 'immediate'
            })
        elif src.startswith('['):
            # Memory access
            addr = self._evaluate_address(src[1:-1])
            value = self.cache.read(addr) if self.cache else self.memory.read(addr)
            # Log register operation with enhanced visualization
            self.logger.log_register_operation('mov', {
                'dest': dest,
                'value': value,
                'source': f'memory[{addr}]'
            })
        else:
            value = self.registers.get(src, 0)
            # Log register operation with enhanced visualization
            self.logger.log_register_operation('mov', {
                'dest': dest,
                'value': value,
                'source': src
            })

        # Store in destination
        if dest.startswith('['):
            # Memory write
            addr = self._evaluate_address(dest[1:-1])
            if self.cache:
                self.cache.write(addr, value)
                # Ensure write-through to memory
                self.memory.write(addr, value)
            else:
                self.memory.write(addr, value)
        else:
            self.registers[dest] = value

    def _execute_add(self, operands: List[str]) -> None:
        """Execute ADD instruction"""
        if len(operands) != 2:
            raise ValueError("ADD requires 2 operands")

        dest, src = operands

        # Get source value
        if src.startswith('#'):
            value = int(src[1:])
        else:
            value = self.registers.get(src, 0)

        # Add to destination
        self.registers[dest] += value

    def _execute_sub(self, operands: List[str]) -> None:
        """Execute SUB instruction"""
        if len(operands) != 2:
            raise ValueError("SUB requires 2 operands")

        dest, src = operands

        # Get source value
        if src.startswith('#'):
            value = int(src[1:])
        else:
            value = self.registers.get(src, 0)

        # Subtract from destination
        self.registers[dest] -= value

    def _execute_jmp(self, operands: List[str]) -> int:
        """Execute JMP instruction"""
        if len(operands) != 1:
            raise ValueError("JMP requires 1 operand")

        label = operands[0]
        if label not in self.labels:
            raise ValueError(f"Undefined label: {label}")

        return self.labels[label]

    def _execute_jz(self, operands: List[str]) -> int:
        """Execute JZ instruction"""
        if len(operands) != 1:
            raise ValueError("JZ requires 1 operand")

        label = operands[0]
        if label not in self.labels:
            raise ValueError(f"Unknown label: {label}")

        if self.registers['eax'] == 0:
            return self.labels[label]
        return self.pc + 1

    def _execute_jnz(self, operands: List[str]) -> int:
        """Execute JNZ instruction"""
        if len(operands) != 1:
            raise ValueError("JNZ requires 1 operand")

        label = operands[0]
        if label not in self.labels:
            raise ValueError(f"Unknown label: {label}")

        if self.registers['eax'] != 0:
            return self.labels[label]
        return self.pc + 1

    def _execute_load(self, operands: List[str]) -> None:
        """Execute LOAD instruction"""
        if len(operands) != 2:
            raise ValueError("LOAD requires 2 operands")

        dest, src = operands

        # Get memory address
        if src.startswith('['):
            addr = self._evaluate_address(src[1:-1])
        else:
            raise ValueError("LOAD source must be a memory address")

        # Read from memory and store in register
        value = self.cache.read(addr) if self.cache else self.memory.read(addr)
        self.registers[dest] = value

        # Log register operation with enhanced visualization
        self.logger.log_register_operation('load', {
            'dest': dest,
            'value': value,
            'source': f'memory[{addr}]'
        })

    def _evaluate_address(self, expr: str) -> int:
        """Evaluate a memory address expression"""
        # Simple address evaluation - can be extended for more complex expressions
        if expr.isdigit():
            return int(expr)
        return self.registers.get(expr, 0)

    def _print_state(self) -> None:
        """Print the current state of the CPU and memory"""
        print("\nCPU State:")
        print(f"PC: {self.pc}")
        print("Registers:")
        for reg, value in self.registers.items():
            print(f"  {reg}: {value}")

        print("\nCache Performance:")
        if self.cache:
            try:
                stats = self.cache.get_performance_stats()
                print(f"  Hits: {stats.get('hits', 0)}")
                print(f"  Misses: {stats.get('misses', 0)}")
                print(f"  Hit Rate: {stats.get('hit_rate', 0.0):.2f}%")
            except Exception as e:
                print(f"  Error getting cache stats: {str(e)}")
        else:
            print("  No cache present")

    def run(self) -> None:
        """Run the loaded program"""
        self.running = True
        self.start_time = time()
        self.instruction_count = 0

        while self.running:
            if not self.execute_step():
                break

        self.end_time = time()
        exec_time = self.end_time - self.start_time
        ips = self.instruction_count / exec_time if exec_time > 0 else 0

        self.logger.log(LogLevel.INFO, "\nProgram completed:")
        self.logger.log(LogLevel.INFO, f"Instructions executed: {self.instruction_count}")
        self.logger.log(LogLevel.INFO, f"Execution time: {exec_time:.6f}s")
        self.logger.log(LogLevel.INFO, f"Instructions per second: {ips:.2f}")
