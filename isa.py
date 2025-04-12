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
    """Instruction types supported by the CPU"""
    MOV = auto()    # Move data between registers/memory
    LOAD = auto()   # Load from memory to register
    STORE = auto()  # Store from register to memory
    ADD = auto()    # Add two values
    SUB = auto()    # Subtract two values
    JMP = auto()    # Unconditional jump
    JZ = auto()     # Jump if zero
    JNZ = auto()    # Jump if not zero
    AND = auto()    # Bitwise AND
    OR = auto()     # Bitwise OR
    XOR = auto()    # Bitwise XOR
    NOT = auto()    # Bitwise NOT
    INC = auto()    # Increment register
    DEC = auto()    # Decrement register
    SHL = auto()    # Shift left
    SHR = auto()    # Shift right
    CMP = auto()    # Compare two values
    TEST = auto()   # Test bits (AND without storing)
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
        self.running = True

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

        instruction = self.instructions[self.pc]
        self.pc += 1
        self.instruction_count += 1

        try:
            if instruction.type == InstructionType.MOV:
                self._execute_mov(instruction.operands)
            elif instruction.type == InstructionType.LOAD:
                self._execute_load(instruction.operands)
            elif instruction.type == InstructionType.ADD:
                self._execute_add(instruction.operands)
            elif instruction.type == InstructionType.SUB:
                self._execute_sub(instruction.operands)
            elif instruction.type == InstructionType.INC:
                self._execute_inc(instruction.operands)
            elif instruction.type == InstructionType.DEC:
                self._execute_dec(instruction.operands)
            elif instruction.type == InstructionType.NOT:
                self._execute_not(instruction.operands)
            elif instruction.type == InstructionType.AND:
                self._execute_and(instruction.operands)
            elif instruction.type == InstructionType.OR:
                self._execute_or(instruction.operands)
            elif instruction.type == InstructionType.XOR:
                self._execute_xor(instruction.operands)
            elif instruction.type == InstructionType.CMP:
                self._execute_cmp(instruction.operands)
            elif instruction.type == InstructionType.TEST:
                self._execute_test(instruction.operands)
            elif instruction.type == InstructionType.SHL:
                self._execute_shift(instruction.operands, True)
            elif instruction.type == InstructionType.SHR:
                self._execute_shift(instruction.operands, False)
            elif instruction.type == InstructionType.JMP:
                self.pc = self._execute_jmp(instruction.operands)
            elif instruction.type == InstructionType.JZ:
                self.pc = self._execute_jz(instruction.operands)
            elif instruction.type == InstructionType.JNZ:
                self.pc = self._execute_jnz(instruction.operands)
            elif instruction.type == InstructionType.HALT:
                self.running = False
                return False
            else:
                raise ValueError(f"Unknown instruction: {instruction.type}")

            return True

        except Exception as e:
            print(f"Error executing instruction: {e}")
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

    def _execute_inc(self, operands: List[str]) -> None:
        """Execute INC instruction - increment register by 1"""
        if len(operands) != 1:
            raise ValueError(f"INC instruction requires 1 operand, got {len(operands)}")

        dest = operands[0]
        if dest not in self.registers:
            raise ValueError(f"Invalid register {dest}")

        self.registers[dest] += 1
        self.logger.log_register_operation('inc', {
            'dest': dest,
            'value': self.registers[dest],
            'source': 'increment'
        })

    def _execute_dec(self, operands: List[str]) -> None:
        """Execute DEC instruction - decrement register by 1"""
        if len(operands) != 1:
            raise ValueError(f"DEC instruction requires 1 operand, got {len(operands)}")

        dest = operands[0]
        if dest not in self.registers:
            raise ValueError(f"Invalid register {dest}")

        self.registers[dest] -= 1
        self.logger.log_register_operation('dec', {
            'dest': dest,
            'value': self.registers[dest],
            'source': 'decrement'
        })

    def _execute_not(self, operands: List[str]) -> None:
        """Execute NOT instruction"""
        if len(operands) != 1:
            raise ValueError("NOT requires 1 operand")

        reg = operands[0]
        if reg not in self.registers:
            raise ValueError(f"Invalid register: {reg}")

        # Perform bitwise NOT operation
        self.registers[reg] = ~self.registers[reg]

        # Log register operation with enhanced visualization
        self.logger.log_register_operation('not', {
            'register': reg,
            'result': self.registers[reg]
        })

    def _execute_and(self, operands: List[str]) -> None:
        """Execute AND instruction"""
        if len(operands) != 2:
            raise ValueError("AND requires 2 operands")

        dest, src = operands
        if dest not in self.registers:
            raise ValueError(f"Invalid destination register: {dest}")

        # Get source value
        if src.startswith('#'):
            value = int(src[1:])
        elif src.startswith('['):
            # Memory access
            addr = self._evaluate_address(src[1:-1])
            value = self.cache.read(addr) if self.cache else self.memory.read(addr)
        else:
            value = self.registers.get(src, 0)

        # Perform bitwise AND operation
        self.registers[dest] &= value

        # Log register operation with enhanced visualization
        self.logger.log_register_operation('and', {
            'dest': dest,
            'value': value,
            'result': self.registers[dest]
        })

    def _execute_or(self, operands: List[str]) -> None:
        """Execute OR instruction"""
        if len(operands) != 2:
            raise ValueError("OR requires 2 operands")

        dest, src = operands
        if not dest in self.registers:
            raise ValueError(f"Invalid destination register: {dest}")

        # Get source value
        if src.startswith('#'):
            src_value = int(src[1:])
        elif src in self.registers:
            src_value = self.registers[src]
        else:
            raise ValueError(f"Invalid source operand: {src}")

        # Perform bitwise OR
        result = self.registers[dest] | src_value

        # Update destination register
        self.registers[dest] = result

        # Log register operation
        self.logger.log_register_operation('or', {
            'dest': dest,
            'value': result,
            'source': src
        })

    def _execute_xor(self, operands: List[str]) -> None:
        """Execute XOR instruction"""
        if len(operands) != 2:
            raise ValueError("XOR requires 2 operands")

        dest, src = operands

        # Get source value
        if src.startswith('#'):
            src_val = int(src[1:])
        elif src.startswith('['):
            addr = self._evaluate_address(src[1:-1])
            src_val = self.cache.read(addr) if self.cache else self.memory.read(addr)
        else:
            if src not in self.registers:
                raise ValueError(f"Invalid source register: {src}")
            src_val = self.registers[src]

        # Get destination value and perform XOR
        if dest.startswith('['):
            # Memory operation
            addr = self._evaluate_address(dest[1:-1])
            dest_val = self.cache.read(addr) if self.cache else self.memory.read(addr)
            result = dest_val ^ src_val
            if self.cache:
                self.cache.write(addr, result)
            self.memory.write(addr, result)
            self.logger.log_register_operation('xor', {
                'dest': f"Memory[{addr}]",
                'value': result,
                'source': src
            })
        else:
            # Register operation
            if dest not in self.registers:
                raise ValueError(f"Invalid destination register: {dest}")
            dest_val = self.registers[dest]
            result = dest_val ^ src_val
            self.registers[dest] = result
            self.logger.log_register_operation('xor', {
                'dest': dest,
                'value': result,
                'source': src
            })

    def _execute_shift(self, operands: List[str], left: bool) -> None:
        """Execute SHL or SHR instruction"""
        if len(operands) != 2:
            raise ValueError("Shift requires 2 operands")

        dest, src = operands

        # Get shift amount
        if src.startswith('#'):
            shift_amount = int(src[1:])
        elif src.startswith('['):
            addr = self._evaluate_address(src[1:-1])
            shift_amount = self.cache.read(addr) if self.cache else self.memory.read(addr)
        else:
            if src not in self.registers:
                raise ValueError(f"Invalid source register: {src}")
            shift_amount = self.registers[src]

        # Perform shift operation
        if dest.startswith('['):
            # Memory operation
            addr = self._evaluate_address(dest[1:-1])
            dest_val = self.cache.read(addr) if self.cache else self.memory.read(addr)
            result = dest_val << shift_amount if left else dest_val >> shift_amount
            if self.cache:
                self.cache.write(addr, result)
            self.memory.write(addr, result)
            self.logger.log_register_operation('shift', {
                'dest': f"Memory[{addr}]",
                'value': result,
                'source': src,
                'left': left
            })
        else:
            # Register operation
            if dest not in self.registers:
                raise ValueError(f"Invalid destination register: {dest}")
            dest_val = self.registers[dest]
            result = dest_val << shift_amount if left else dest_val >> shift_amount
            self.registers[dest] = result
            self.logger.log_register_operation('shift', {
                'dest': dest,
                'value': result,
                'source': src,
                'left': left
            })

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
        return self.pc

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

    def _execute_cmp(self, operands: List[str]) -> None:
        """Execute CMP instruction"""
        if len(operands) != 2:
            raise ValueError("CMP requires 2 operands")

        dest, src = operands

        # Get source value
        if src.startswith('#'):
            value = int(src[1:])
        else:
            value = self.registers.get(src, 0)

        # Compare values
        self.registers['eax'] = 1 if self.registers['eax'] < value else 0

    def _execute_test(self, operands: List[str]) -> None:
        """Execute TEST instruction"""
        if len(operands) != 2:
            raise ValueError("TEST requires 2 operands")

        dest, src = operands

        # Get source value
        if src.startswith('#'):
            value = int(src[1:])
        else:
            value = self.registers.get(src, 0)

        # Test bits (AND without storing)
        self.registers['eax'] = 1 if self.registers['eax'] & value else 0

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
