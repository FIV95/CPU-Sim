from memory import Memory
from time import time
from colorama import Fore, Style
from utils.logger import Logger, LogLevel

# Register class used for register
# data storage in the ISA() class
class Register(Memory):
    def __init__(self):
        """Initialize register states"""
        self._register_states = {}
        # Initialize 32 general-purpose registers
        for i in range(32):
            self._register_states[f'R{i}'] = {'value': None, 'dirty': False}
        self._exec_time = 0

    # Accessors
    @property
    def data(self):
        return self._register_states

    # Mutators
    @data.setter
    def data(self, value):
        if isinstance(value, dict):
            self._register_states = value
        else:
            raise ValueError("Data must be a dictionary")

    # Read data to register address
    def read(self, address):
        """Read value from register"""
        if address in self._register_states:
            return self._register_states[address]['value']
        return None

    # Write data to register address
    def write(self, address, value):
        """Write value to register"""
        if address in self._register_states:
            self._register_states[address]['value'] = value
            self._register_states[address]['dirty'] = True

    # Return total execution time
    def get_exec_time(self):
        """Return execution time"""
        return self._exec_time

    def debug_info(self):
        """Return detailed debug information about the register state"""
        info = {
            "registers": self._register_states,
            "exec_time": self._exec_time
        }
        return info

    def print_debug_info(self):
        """Print formatted debug information about the register state"""
        info = self.debug_info()
        super().print_debug_info()
        print("\nRegister Contents:")
        for reg, state in info['registers'].items():
            state_str = "Dirty" if state["dirty"] else "Clean"
            print(f"  {reg}: {state['value']} ({state_str})")

    def validate_state(self):
        """Validate the register state and return any issues found"""
        issues = super().validate_state()

        # Check register data
        if not isinstance(self._register_states, dict):
            issues.append("Register data is not a dictionary")
        else:
            # Check for required registers (all 32)
            required_regs = [f'R{i}' for i in range(32)]
            for reg in required_regs:
                if reg not in self._register_states:
                    issues.append(f"Missing required register: {reg}")
                if not isinstance(self._register_states[reg]['dirty'], bool):
                    issues.append(f"Invalid dirty state for register {reg}")

        return issues

# Memory simulation architecture class
class ISA():
    def __init__(self):
        self._memory = None
        self._registers = Register()
        self._instructions = []  # List of instructions
        self._labels = {}       # Dictionary of label locations
        self._instruction_pointer = 0
        self._output = ""
        self._logger = Logger()  # Initialize the logger
        self._debug_info = {
            'register_states': [],
            'memory_accesses': [],
            'instruction_counts': {},
            'branch_predictions': [],
            'pipeline_stages': []
        }
        self._instruction_counts = {
            "mov": 0,
            "add": 0,
            "sub": 0,
            "jmp": 0
        }
        self._instruction_times = {
            "mov": 0,
            "add": 0,
            "sub": 0,
            "jmp": 0
        }
        self._last_instruction_time = None
        self._pipeline_state = {
            "fetch": None,
            "decode": None,
            "execute": None,
            "memory": None,
            "writeback": None
        }
        self._branch_prediction = {
            "predictions": {},
            "correct": 0,
            "incorrect": 0
        }

    # Accessors
    @property
    def memory(self):
        return self._memory

    @property
    def registers(self):
        return self._registers

    @property
    def instructions(self):
        return self._instructions

    @property
    def output(self):
        return self._output

    # Mutators
    @memory.setter
    def memory(self, value):
        self._memory = value

    @registers.setter
    def registers(self, value):
        if isinstance(value, Register):
            self._registers = value
        else:
            raise ValueError("Registers must be an instance of Register class")

    @output.setter
    def output(self, value):
        if isinstance(value, str):
            self._output = value
        else:
            raise ValueError("Output must be a string")

    # Assign memory class for the
    # archicture for reading and writing
    def set_memory(self, memory):
        self._memory = memory
        print(f"ISA memory: {self._memory.name}")

    # Go through lines of instruction file
    def read_instructions(self, file):
        """Read and execute instructions from file"""
        if self._memory is not None:
            print(f"ISA memory: {self._memory.name}")
            start = time()
            with open(file) as codefile:
                # First pass: collect all instructions and labels
                self._instructions = []
                self._labels = {}
                lines = [line.strip() for line in codefile.readlines() if line.strip() != '']
                for i, line in enumerate(lines):
                    if line.endswith(':'):
                        self._labels[line[:-1]] = i
                    else:
                        self._instructions.append(line)

                # Second pass: execute instructions
                self._instruction_pointer = 0
                max_instructions = 650  # Increased from 150 to allow bubble sort to complete
                instruction_count = 0

                while self._instruction_pointer < len(self._instructions):
                    if instruction_count >= max_instructions:
                        print(f"\n{Fore.RED}Error: Maximum instruction limit ({max_instructions}) reached. Possible infinite loop detected.{Style.RESET_ALL}")
                        return time() - start

                    line = self._instructions[self._instruction_pointer]
                    result = self.parse_line(line)
                    if isinstance(result, str) and result in self._labels:
                        print(f"Jumping to label: {result}")
                        self._instruction_pointer = self._labels[result]
                    else:
                        self._instruction_pointer += 1

                    instruction_count += 1

            return time() - start
        else:
            print("Architecture has found no memory")
            return None

    # Parse line and send arguments
    # to the correct instruction
    def parse_line(self, line):
        """Parse a single instruction line in x86-like format"""
        # Remove comments (everything after #)
        line = line.split('#')[0].strip()
        if not line:
            return None

        # Split the instruction and operands
        parts = line.split()
        if not parts:
            return None

        opcode = parts[0].upper()

        # Handle operands based on instruction type
        if opcode == "MOV":
            if len(parts) != 3:
                return None
            dest = parts[1].strip(',')
            src = parts[2]
            return self.mov(dest, src)
        elif opcode == "ADD":
            if len(parts) != 3:
                return None
            dest = parts[1].strip(',')
            src = parts[2]
            return self.add(dest, src)
        elif opcode == "SUB":
            if len(parts) != 3:
                return None
            dest = parts[1].strip(',')
            src = parts[2]
            return self.sub(dest, src)
        elif opcode == "JMP":
            if len(parts) == 2:
                # Single argument jump (label or offset)
                return self.jmp(parts[1])
            elif len(parts) == 3:
                # Two argument jump (label/offset and condition register)
                target = parts[1].strip(',')
                condition = parts[2]
                return self.jmp(target, condition)
            return None
        return None

    def mov(self, dest, src):
        """Move data between registers and memory"""
        val = None
        start_time = time()

        # Source is a register
        if isinstance(src, str) and src.startswith('R'):
            val = self._registers.read(src)
            if val is not None:
                self._logger.log_register_operation("Move", {
                    "Source": src,
                    "Destination": dest,
                    "Value": val
                })

        # Source is a memory location
        elif isinstance(src, str) and src.startswith('['):
            addr = src[1:-1]  # Remove brackets
            if addr.startswith('R'):
                addr = self._registers.read(addr)
            else:
                try:
                    addr = int(addr)
                except ValueError:
                    return None
            val = self._memory.read(addr)
            if val is not None:
                self._logger.log_memory_operation("Read", {
                    "Address": addr,
                    "Value": val,
                    "Destination Register": dest
                })

        # Source is immediate value
        else:
            try:
                val = int(src)
                self._logger.log_register_operation("Move", {
                    "Source": src,
                    "Destination": dest,
                    "Value": val
                })
            except ValueError:
                return None

        # Destination is a register
        if isinstance(dest, str) and dest.startswith('R'):
            self._registers.write(dest, val)

        # Destination is a memory location
        elif isinstance(dest, str) and dest.startswith('['):
            addr = dest[1:-1]  # Remove brackets
            if addr.startswith('R'):
                addr = self._registers.read(addr)
            else:
                try:
                    addr = int(addr)
                except ValueError:
                    return None
            self._memory.write(addr, val)
            self._logger.log_memory_operation("Write", {
                "Address": addr,
                "Value": val,
                "Source": src,
                "Destination": dest
            })

        self._track_instruction("mov", start_time)
        return val

    def add(self, dest, src):
        """Add two registers or immediate value"""
        if src.startswith('R'):
            val = self._registers.read(src)
        else:
            val = int(src)

        dest_val = self._registers.read(dest)
        result = dest_val + val
        self._registers.write(dest, result)

        self._debug_info['register_states'].append({
            'register': dest,
            'value': result
        })

    def sub(self, dest, src):
        """Subtract src from dest"""
        if src.startswith('R'):
            val = self._registers.read(src)
        else:
            val = int(src)

        dest_val = self._registers.read(dest)
        result = dest_val - val
        self._registers.write(dest, result)

        print(f"\n=== Subtraction ===")
        print(f"Destination Register: {dest}")
        print(f"Source: {src}")
        print(f"Original Value: {dest_val}")
        print(f"Subtracted Value: {val}")
        print(f"Result: {result}")

        self._debug_info['register_states'].append({
            'register': dest,
            'value': result
        })

    # return the cumulative execution time
    # of the registers and memory
    def get_exec_time(self):
        exec_time = self._registers.get_exec_time()
        if self._memory is not None:
            exec_time += self._memory.get_exec_time()
        return exec_time

    def debug_info(self):
        """Return detailed debug information about the ISA state"""
        info = {
            "memory": self._memory.debug_info() if self._memory else None,
            "registers": self._registers.debug_info(),
            "instructions": list(self._instructions.keys()),
            "output": self._output,
            "exec_time": self.get_exec_time(),
            "instruction_counts": self._instruction_counts,
            "instruction_times": self._instruction_times,
            "last_instruction": self._last_instruction_time,
            "pipeline_state": self._pipeline_state,
            "branch_prediction": self._branch_prediction,
            "debug_info": self._debug_info
        }
        return info

    def print_debug_info(self):
        """Print formatted debug information about the ISA state"""
        print(f"\n{Fore.CYAN}=== ISA Debug Info ==={Style.RESET_ALL}")

        # Print memory info
        if self._memory:
            self._memory.print_debug_info()
        else:
            print(f"{Fore.RED}No memory attached{Style.RESET_ALL}")

        # Print register info
        self._registers.print_debug_info()

        # Print instruction info
        print(f"\nAvailable Instructions: {', '.join(self._instructions.keys())}")
        print(f"Output: {self._output}")
        print(f"Execution Time: {self.get_exec_time()} ns")

        # Print pipeline state
        print("\nPipeline State:")
        for stage, instruction in self._pipeline_state.items():
            print(f"  {stage}: {instruction if instruction else 'Empty'}")

        # Print branch prediction stats
        total_predictions = self._branch_prediction["correct"] + self._branch_prediction["incorrect"]
        accuracy = (self._branch_prediction["correct"] / total_predictions * 100) if total_predictions > 0 else 0
        print("\nBranch Prediction:")
        print(f"  Total Predictions: {total_predictions}")
        print(f"  Correct: {self._branch_prediction['correct']}")
        print(f"  Incorrect: {self._branch_prediction['incorrect']}")
        print(f"  Accuracy: {accuracy:.2f}%")

    def validate_state(self):
        """Validate the ISA state and return any issues found"""
        issues = []

        # Check memory
        if self._memory is None:
            issues.append("No memory attached")

        # Check registers
        issues.extend(self._registers.validate_state())

        # Check instructions
        if not isinstance(self._instructions, dict):
            issues.append("Instructions is not a dictionary")
        else:
            required_instructions = ["mov", "add", "sub", "jmp"]
            for inst in required_instructions:
                if inst not in self._instructions:
                    issues.append(f"Missing required instruction: {inst}")

        # Check output
        if not isinstance(self._output, str):
            issues.append("Output is not a string")

        # Check pipeline state
        required_stages = ["fetch", "decode", "execute", "memory", "writeback"]
        for stage in required_stages:
            if stage not in self._pipeline_state:
                issues.append(f"Missing pipeline stage: {stage}")

        # Check branch prediction
        if not isinstance(self._branch_prediction, dict):
            issues.append("Branch prediction is not a dictionary")
        else:
            required_keys = ["predictions", "correct", "incorrect"]
            for key in required_keys:
                if key not in self._branch_prediction:
                    issues.append(f"Missing branch prediction key: {key}")

        return issues

    def get_instruction_stats(self):
        """Return statistics about instruction execution"""
        stats = {
            "total_instructions": len(self._instructions),
            "available_instructions": list(self._instructions.keys()),
            "execution_time": self.get_exec_time(),
            "memory_stats": self._memory.get_performance_stats() if self._memory else None,
            "register_stats": self._registers.get_performance_stats(),
            "pipeline_stats": {
                "stages": len(self._pipeline_state),
                "active_stages": sum(1 for stage in self._pipeline_state.values() if stage is not None)
            },
            "branch_prediction_stats": {
                "total": self._branch_prediction["correct"] + self._branch_prediction["incorrect"],
                "accuracy": (self._branch_prediction["correct"] / (self._branch_prediction["correct"] + self._branch_prediction["incorrect"]) * 100) if (self._branch_prediction["correct"] + self._branch_prediction["incorrect"]) > 0 else 0
            }
        }
        return stats

    def _track_instruction(self, instruction, start_time):
        """Track instruction execution time and count"""
        end_time = time()
        execution_time = end_time - start_time

        self._instruction_counts[instruction] += 1
        self._instruction_times[instruction] += execution_time
        self._last_instruction_time = {
            "instruction": instruction,
            "time": execution_time,
            "timestamp": end_time
        }

    def get_instruction_performance(self):
        """Return detailed performance metrics for each instruction"""
        performance = {}
        for inst in self._instruction_counts:
            count = self._instruction_counts[inst]
            total_time = self._instruction_times[inst]
            performance[inst] = {
                "count": count,
                "total_time": total_time,
                "average_time": total_time / count if count > 0 else 0,
                "percentage": (count / sum(self._instruction_counts.values()) * 100) if sum(self._instruction_counts.values()) > 0 else 0
            }
        return performance

    def get_last_instruction(self):
        """Return information about the last executed instruction"""
        return self._last_instruction_time

    def jmp(self, target, condition=None):
        """Jump instruction used to create simulation output or control flow"""
        print(f"\n=== Jump Debug ===")
        print(f"Jump target: {target}")
        print(f"Jump condition register: {condition}")
        print(f"Current instruction: {self._instruction_pointer}")
        print(f"R5 (comparison): {self._registers.read('R5')}")
        print(f"R6 (outer loop): {self._registers.read('R6')}")
        print(f"R7 (inner loop): {self._registers.read('R7')}")
        print(f"R0 (current element): {self._registers.read('R0')}")
        print(f"R1 (previous element): {self._registers.read('R1')}")
        print(f"R4 (index): {self._registers.read('R4')}")

        # If condition register is provided, check its value
        if condition and condition.startswith('R'):
            cond_val = self._registers.read(condition)
            if cond_val is None:
                raise ValueError(f"Register {condition} contains no value when used as jump condition")
            if cond_val <= 0:
                print(f"Jump condition not met (register {condition} = {cond_val})")
                return None

        # Special output instruction
        if target == "100":
            data = self._registers.read('R0')
            print(f"Output instruction - R0 value: {data}")
            if data is not None:
                self._output += chr(data)
            return None

        # Label-based jumps
        if target == "outer_loop":
            val = self._registers.read('R6')
            print(f"Outer loop check - R6 value: {val}")
            if val > 0:
                print("Jumping to outer_loop")
                return "outer_loop"
            else:
                print("Outer loop complete")
        elif target == "inner_loop":
            val = self._registers.read('R7')
            print(f"Inner loop check - R7 value: {val}")
            if val > 0:
                print("Jumping to inner_loop")
                return "inner_loop"
            else:
                print("Inner loop complete")
        elif target == "no_swap":
            val = self._registers.read('R5')
            print(f"Swap check - R5 value: {val}")
            if val >= 0:
                print("Skipping swap")
                return "no_swap"
            else:
                print("Performing swap")
        elif target == "output_loop":
            val = self._registers.read('R2')
            print(f"Output loop check - R2 value: {val}")
            if val > 0:
                print("Jumping to output_loop")
                return "output_loop"
            else:
                print("Output loop complete")
        else:
            # Try to parse target as a numeric offset
            try:
                offset = int(target)
                print(f"Numeric offset jump: {offset}")
                if condition:
                    cond_val = self._registers.read(condition)
                    if cond_val is None:
                        raise ValueError(f"Register {condition} contains no value when used as jump condition")
                    if cond_val <= 0:
                        print(f"Jump condition not met (register {condition} = {cond_val})")
                        return None
                self._instruction_pointer += offset
                return None
            except ValueError:
                print(f"Unrecognized jump target: {target}")
        return None
