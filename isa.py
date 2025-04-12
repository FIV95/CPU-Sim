from memory import Memory
from cache.cache import Cache
from utils.logger import Logger, LogLevel
from time import time
from typing import Dict, List, Tuple, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum, auto

class AddressingMode(Enum):
    """Supported addressing modes"""
    REGISTER = auto()      # eax, ebx, etc.
    IMMEDIATE = auto()     # #42
    MEMORY_DIRECT = auto() # [1000]
    MEMORY_REG = auto()    # [eax]
    MEMORY_DISP = auto()   # [eax + 10]
    MEMORY_INDEX = auto()  # [eax + ebx*2]
    MEMORY_COMPLEX = auto()# [eax + ebx*2 + 10]

@dataclass
class InstructionHandler:
    """Handler for a specific instruction"""
    opcode: str
    handler: Callable
    validate: Callable
    description: str
    operands: int  # Number of operands expected

class ISA:
    def __init__(self, memory=None, cache=None):
        # Simple registers
        self.registers = {
            'eax': 0,
            'ebx': 0,
            'ecx': 0,
            'edx': 0,
            'esi': 0,
            'edi': 0
        }

        # Program counter and memory system
        self.pc = 0
        self.memory = memory
        self.cache = cache
        self.logger = Logger()

        # For visualization
        self.last_operation = None
        self.last_memory_access = None

    def read_instructions(self, filename):
        """Read instructions from file"""
        with open(filename, 'r') as f:
            self.instructions = []
            self.labels = {}

            # Parse instructions and labels
            for i, line in enumerate(f.readlines()):
                line = line.strip()
                if not line or line.startswith(';'):
                    continue

                if line.endswith(':'):
                    # Store label
                    label = line[:-1].strip()
                    self.labels[label] = len(self.instructions)
                else:
                    # Store instruction
                    self.instructions.append(line)

    def execute_step(self):
        """Execute one instruction and show memory hierarchy state"""
        if self.pc >= len(self.instructions):
            return False

        instruction = self.instructions[self.pc]
        self.pc += 1

        # Parse instruction
        parts = instruction.split()
        op = parts[0]

        # Log start of instruction
        self.logger.log(LogLevel.INFO, f"\n=== Executing {instruction} ===")

        if op == 'mov':
            dest, src = parts[1], parts[2]
            # Memory access
            if src.startswith('['):
                # Read from memory through cache
                addr = self.registers[src[1:-1]]
                value = self.cache.read(addr)
                self.registers[dest] = value
                self.last_memory_access = ('read', addr, value)
            elif dest.startswith('['):
                # Write to memory through cache
                addr = self.registers[dest[1:-1]]
                value = int(src) if src.isdigit() else self.registers[src]
                self.cache.write(addr, value)
                self.last_memory_access = ('write', addr, value)
            else:
                # Register to register
                value = int(src) if src.isdigit() else self.registers[src]
                self.registers[dest] = value

        elif op == 'add':
            dest, src = parts[1], parts[2]
            value = int(src) if src.isdigit() else self.registers[src]
            self.registers[dest] += value

        elif op == 'cmp':
            a, b = parts[1], parts[2]
            a_val = self.registers[a]
            b_val = int(b) if b.isdigit() else self.registers[b]
            self.last_cmp = (a_val, b_val)

        elif op == 'jmp':
            label = parts[1]
            self.pc = self.labels[label]

        elif op == 'jge':
            label = parts[1]
            if self.last_cmp[0] >= self.last_cmp[1]:
                self.pc = self.labels[label]

        elif op == 'jle':
            label = parts[1]
            if self.last_cmp[0] <= self.last_cmp[1]:
                self.pc = self.labels[label]

        elif op == 'halt':
            return False

        # Log system state
        self.print_state()
        return True

    def print_state(self):
        """Display current state of CPU and memory hierarchy"""
        self.logger.log(LogLevel.INFO, "\nCPU State:")
        self.logger.log(LogLevel.INFO, f"PC: {self.pc}")
        self.logger.log(LogLevel.INFO, "Registers:")
        for reg, val in self.registers.items():
            self.logger.log(LogLevel.INFO, f"  {reg}: {val}")

        if self.last_memory_access:
            op, addr, val = self.last_memory_access
            self.logger.log(LogLevel.INFO, f"\nLast Memory Access:")
            self.logger.log(LogLevel.INFO, f"  Operation: {op}")
            self.logger.log(LogLevel.INFO, f"  Address: {addr}")
            self.logger.log(LogLevel.INFO, f"  Value: {val}")

        # Get cache stats
        if self.cache:
            stats = self.cache.get_performance_stats()
            self.logger.log(LogLevel.INFO, "\nCache Performance:")
            self.logger.log(LogLevel.INFO, f"  Total Accesses: {stats['access_count']}")
            self.logger.log(LogLevel.INFO, f"  Hit Count: {stats['hit_count']}")
            self.logger.log(LogLevel.INFO, f"  Miss Count: {stats['miss_count']}")
            self.logger.log(LogLevel.INFO, f"  Hit Rate: {(stats['hit_count'] / stats['access_count'] * 100) if stats['access_count'] > 0 else 0:.2f}%")

        # Get memory stats
        if self.memory:
            stats = self.memory.get_performance_stats()
            self.logger.log(LogLevel.INFO, "\nMemory Performance:")
            self.logger.log(LogLevel.INFO, f"  Reads: {stats['reads']}")
            self.logger.log(LogLevel.INFO, f"  Writes: {stats['writes']}")
            self.logger.log(LogLevel.INFO, f"  Access Time: {stats['avg_access_time']:.2f}ns")

    def get_array(self):
        """Get the current array state"""
        return self.array

    def set_memory(self, memory):
        """Set the memory interface"""
        self.memory = memory
        self.logger.log(LogLevel.DEBUG, f"Set memory interface: {memory}")

    def get_performance_stats(self):
        """Get performance statistics"""
        return {
            'instruction_count': self.instruction_count,
            'execution_time': self.execution_time,
            'instructions_per_second': self.instruction_count / self.execution_time if self.execution_time > 0 else 0,
            'instruction_counts': self.instruction_counts,
            'instruction_times': self.instruction_times
        }

    def load_program(self, program):
        """Load a program into memory"""
        self.instructions = []
        self.labels = {}
        self.pc = 0
        self.instruction_count = 0
        self.execution_time = 0
        self.instruction_counts = {k: 0 for k in self.instruction_counts}
        self.instruction_times = {k: 0 for k in self.instruction_times}

        for i, line in enumerate(program):
            line = line.strip()
            if not line or line.startswith(';'):
                continue

            # Remove comments
            if ';' in line:
                line = line[:line.index(';')].strip()

            if line.endswith(':'):
                # Label
                label = line[:-1]
                self.labels[label] = len(self.instructions)
                self.logger.log(LogLevel.DEBUG, f"Found label {label} at instruction {len(self.instructions)}")
            else:
                # Instruction
                parts = line.split()
                if not parts:
                    continue
                opcode = parts[0]
                operands = parts[1:]
                self.instructions.append((opcode, operands))
                self.logger.log(LogLevel.DEBUG, f"Loaded instruction: {opcode} {operands}")

    def mov(self, dest, src):
        """Move value to register or memory"""
        start_time = time()

        try:
            if src.startswith('#'):
                value = int(src[1:])
                self.logger.log(LogLevel.DEBUG, f"MOV: Immediate value {value} -> {dest}")
            elif src.isdigit():
                value = int(src)
                self.logger.log(LogLevel.DEBUG, f"MOV: Immediate value {value} -> {dest}")
            elif src.startswith('['):
                # Memory access
                addr = int(src[1:-1])
                value = self.memory.read(addr)
                self.logger.log(LogLevel.DEBUG, f"MOV: Memory[{addr}] ({value}) -> {dest}")
            else:
                value = getattr(self, src)
                self.logger.log(LogLevel.DEBUG, f"MOV: Register {src} ({value}) -> {dest}")

            if dest.startswith('['):
                # Memory write
                addr = int(dest[1:-1])
                self.memory.write(addr, value)
                self.logger.log(LogLevel.DEBUG, f"MOV: Memory[{addr}] = {value}")
            else:
                setattr(self, dest, value)
                self.logger.log(LogLevel.DEBUG, f"MOV: {dest} = {value}")

            # Update performance stats
            end_time = time()
            self.instruction_counts["mov"] += 1
            self.instruction_times["mov"] += end_time - start_time
            self.instruction_count += 1
            self.execution_time += end_time - start_time

            return True

        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in MOV instruction: {str(e)}")
            return False

    def add(self, dest, src):
        """Add two values"""
        start_time = time()

        try:
            if src.startswith('#'):
                value = int(src[1:])
            else:
                value = getattr(self, src)
            result = getattr(self, dest) + value

            setattr(self, dest, result)
            self.logger.log(LogLevel.DEBUG, f"ADD: {dest} = {getattr(self, dest)} + {value} = {result}")

            # Update performance stats
            end_time = time()
            self.instruction_counts["add"] += 1
            self.instruction_times["add"] += end_time - start_time
            self.instruction_count += 1
            self.execution_time += end_time - start_time

            return True

        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in ADD instruction: {str(e)}")
            return False

    def sub(self, dest, src):
        """Subtract two values"""
        start_time = time()

        try:
            if src.startswith('#'):
                value = int(src[1:])
            else:
                value = getattr(self, src)
            result = getattr(self, dest) - value

            setattr(self, dest, result)
            self.logger.log(LogLevel.DEBUG, f"SUB: {dest} = {getattr(self, dest)} - {value} = {result}")

            # Update performance stats
            end_time = time()
            self.instruction_counts["sub"] += 1
            self.instruction_times["sub"] += end_time - start_time
            self.instruction_count += 1
            self.execution_time += end_time - start_time

            return True

        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in SUB instruction: {str(e)}")
            return False

    def cmp(self, src1, src2):
        """Compare two values"""
        start_time = time()

        try:
            if src2.startswith('#'):
                b_val = int(src2[1:])
            else:
                b_val = getattr(self, src2)
            a_val = getattr(self, src1)
            result = a_val - b_val

            self.logger.log(LogLevel.DEBUG, f"CMP: {a_val} - {b_val} = {result}")
            self.logger.log(LogLevel.DEBUG, f"Flags: ZF={result == 0}, SF={result < 0}")

            # Update performance stats
            end_time = time()
            self.instruction_counts["cmp"] += 1
            self.instruction_times["cmp"] += end_time - start_time
            self.instruction_count += 1
            self.execution_time += end_time - start_time

            return True

        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in CMP instruction: {str(e)}")
            return False

    def shl(self, dest, src):
        """Shift left"""
        start_time = time()

        try:
            if src.startswith('#'):
                shift = int(src[1:])
            else:
                shift = getattr(self, src)
            result = getattr(self, dest) << shift

            setattr(self, dest, result)
            self.logger.log(LogLevel.DEBUG, f"SHL: {dest} = {getattr(self, dest)} << {shift} = {result}")

            # Update performance stats
            end_time = time()
            self.instruction_counts["shl"] += 1
            self.instruction_times["shl"] += end_time - start_time
            self.instruction_count += 1
            self.execution_time += end_time - start_time

            return True

        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in SHL instruction: {str(e)}")
            return False

    def jmp(self, label):
        """Unconditional jump"""
        start_time = time()

        try:
            if label not in self.labels:
                self.logger.log(LogLevel.ERROR, f"Undefined label: {label}")
                return False

            self.pc = self.labels[label]
            self.logger.log(LogLevel.DEBUG, f"JMP: Jumping to {label} (PC = {self.pc})")

            # Update performance stats
            end_time = time()
            self.instruction_counts["jmp"] += 1
            self.instruction_times["jmp"] += end_time - start_time
            self.instruction_count += 1
            self.execution_time += end_time - start_time

            return True

        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in JMP instruction: {str(e)}")
            return False

    def jge(self, label):
        """Jump if greater than or equal"""
        start_time = time()

        try:
            if label not in self.labels:
                self.logger.log(LogLevel.ERROR, f"Undefined label: {label}")
                return False

            if self.last_cmp[0] >= self.last_cmp[1]:
                self.pc = self.labels[label]
                self.logger.log(LogLevel.DEBUG, f"JGE: Jumping to {label} (PC = {self.pc})")
            else:
                self.logger.log(LogLevel.DEBUG, f"JGE: Not jumping (ZF={self.last_cmp[0] < self.last_cmp[1]}, SF={self.last_cmp[0] < 0})")

            # Update performance stats
            end_time = time()
            self.instruction_counts["jge"] += 1
            self.instruction_times["jge"] += end_time - start_time
            self.instruction_count += 1
            self.execution_time += end_time - start_time

            return True

        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in JGE instruction: {str(e)}")
            return False

    def jle(self, label):
        """Jump if less than or equal"""
        start_time = time()

        try:
            if label not in self.labels:
                self.logger.log(LogLevel.ERROR, f"Undefined label: {label}")
                return False

            if self.last_cmp[0] <= self.last_cmp[1]:
                self.pc = self.labels[label]
                self.logger.log(LogLevel.DEBUG, f"JLE: Jumping to {label} (PC = {self.pc})")
            else:
                self.logger.log(LogLevel.DEBUG, f"JLE: Not jumping (ZF={self.last_cmp[0] < self.last_cmp[1]}, SF={self.last_cmp[0] < 0})")

            # Update performance stats
            end_time = time()
            self.instruction_counts["jle"] += 1
            self.instruction_times["jle"] += end_time - start_time
            self.instruction_count += 1
            self.execution_time += end_time - start_time

            return True

        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in JLE instruction: {str(e)}")
            return False

    def halt(self):
        """Stop execution"""
        start_time = time()

        try:
            self.logger.log(LogLevel.DEBUG, "HALT: Stopping execution")

            # Update performance stats
            end_time = time()
            self.instruction_counts["halt"] += 1
            self.instruction_times["halt"] += end_time - start_time
            self.instruction_count += 1
            self.execution_time += end_time - start_time

            return True

        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in HALT instruction: {str(e)}")
            return False

    def _update_flags(self, result):
        """Update CPU flags based on operation result"""
        self.flags['zero'] = result == 0
        self.flags['sign'] = result < 0
        self.flags['carry'] = result > 0xFFFFFFFF
        self.flags['overflow'] = result > 0x7FFFFFFF or result < -0x80000000

    def debug_info(self):
        """Get debug information"""
        return {
            "registers": {k: getattr(self, k) for k in ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi']},
            "flags": self.flags,
            "instruction_count": self.instruction_count,
            "execution_time": self.execution_time,
            "memory_stats": self.memory.get_performance_stats() if self.memory else None,
            "performance_stats": self.get_performance_stats()
        }

    def print_debug_info(self):
        """Print formatted debug information"""
        self.logger.log(LogLevel.DEBUG, "=== ISA Debug Info ===")

        # Print register info
        self.logger.log(LogLevel.DEBUG, "\nRegisters:")
        for reg, value in self.registers.items():
            self.logger.log(LogLevel.DEBUG, f"  {reg}: {value}")

        # Print flags
        self.logger.log(LogLevel.DEBUG, "\nFlags:")
        for flag, value in self.flags.items():
            self.logger.log(LogLevel.DEBUG, f"  {flag}: {value}")

        # Print performance info
        stats = self.get_performance_stats()
        self.logger.log(LogLevel.DEBUG, "\nPerformance:")
        self.logger.log(LogLevel.DEBUG, f"  Total Instructions: {stats['instruction_count']}")
        self.logger.log(LogLevel.DEBUG, f"  Execution Time: {stats['execution_time']:.6f} seconds")
        self.logger.log(LogLevel.DEBUG, f"  Instructions/Second: {stats['instructions_per_second']:.2f}")

        # Print instruction counts
        self.logger.log(LogLevel.DEBUG, "\nInstruction Counts:")
        for opcode, count in stats['instruction_counts'].items():
            if count > 0:
                self.logger.log(LogLevel.DEBUG, f"  {opcode}: {count}")

        # Print memory info if available
        if self.memory:
            self.memory.print_debug_info()

    def inc(self, dest):
        """Increment value"""
        start_time = time()
        try:
            value = getattr(self, dest)
            setattr(self, dest, value + 1)
            self.logger.log(LogLevel.DEBUG, f"INC: {dest} = {value} + 1 = {getattr(self, dest)}")
            return True
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in INC instruction: {str(e)}")
            return False

    def dec(self, dest):
        """Decrement value"""
        start_time = time()
        try:
            value = getattr(self, dest)
            setattr(self, dest, value - 1)
            self.logger.log(LogLevel.DEBUG, f"DEC: {dest} = {value} - 1 = {getattr(self, dest)}")
            return True
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in DEC instruction: {str(e)}")
            return False

    def shr(self, dest, count):
        """Shift right"""
        start_time = time()
        try:
            if count.startswith('#'):
                shift = int(count[1:])
            else:
                shift = getattr(self, count)
            value = getattr(self, dest)
            result = value >> shift
            setattr(self, dest, result)
            self.logger.log(LogLevel.DEBUG, f"SHR: {dest} = {value} >> {shift} = {result}")
            return True
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in SHR instruction: {str(e)}")
            return False

    def je(self, label):
        """Jump if equal"""
        start_time = time()
        try:
            if label not in self.labels:
                raise ValueError(f"Undefined label: {label}")
            if self.flags['zero']:
                self.pc = self.labels[label]
            self.logger.log(LogLevel.DEBUG, f"JE: Jumping to {label} (PC = {self.pc})")
            return True
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in JE instruction: {str(e)}")
            return False

    def jne(self, label):
        """Jump if not equal"""
        start_time = time()
        try:
            if label not in self.labels:
                raise ValueError(f"Undefined label: {label}")
            if not self.flags['zero']:
                self.pc = self.labels[label]
            self.logger.log(LogLevel.DEBUG, f"JNE: Jumping to {label} (PC = {self.pc})")
            return True
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in JNE instruction: {str(e)}")
            return False

    def jl(self, label):
        """Jump if less"""
        start_time = time()
        try:
            if label not in self.labels:
                raise ValueError(f"Undefined label: {label}")
            if self.flags['sign'] and not self.flags['zero']:
                self.pc = self.labels[label]
            self.logger.log(LogLevel.DEBUG, f"JL: Jumping to {label} (PC = {self.pc})")
            return True
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in JL instruction: {str(e)}")
            return False

    def jg(self, label):
        """Jump if greater"""
        start_time = time()
        try:
            if label not in self.labels:
                raise ValueError(f"Undefined label: {label}")
            if not self.flags['sign'] and not self.flags['zero']:
                self.pc = self.labels[label]
            self.logger.log(LogLevel.DEBUG, f"JG: Jumping to {label} (PC = {self.pc})")
            return True
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in JG instruction: {str(e)}")
            return False

    def call(self, label):
        """Call subroutine"""
        start_time = time()
        try:
            if label not in self.labels:
                raise ValueError(f"Undefined label: {label}")
            # Save return address
            self.registers['esp'] -= 4
            self.memory.write(self.registers['esp'], self.pc + 1)
            # Jump to subroutine
            self.pc = self.labels[label]
            self.logger.log(LogLevel.DEBUG, f"CALL: Jumping to {label} (PC = {self.pc})")
            return True
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in CALL instruction: {str(e)}")
            return False

    def ret(self):
        """Return from subroutine"""
        start_time = time()
        try:
            # Restore return address
            return_addr = self.memory.read(self.registers['esp'])
            self.registers['esp'] += 4
            self.pc = return_addr
            self.logger.log(LogLevel.DEBUG, f"RET: Returning to {return_addr} (PC = {self.pc})")
            return True
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in RET instruction: {str(e)}")
            return False

    def nop(self):
        """No operation"""
        start_time = time()
        try:
            self.logger.log(LogLevel.DEBUG, "NOP: No operation")
            return True
        except Exception as e:
            self.logger.log(LogLevel.ERROR, f"Error in NOP instruction: {str(e)}")
            return False
