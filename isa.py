from memory import Memory
from time import time
from colorama import Fore, Style

# Register class used for register
# data storage in the ISA() class
class Register(Memory):
    def __init__(self):
        super().__init__(name="Register", access_time=0.1)
        self._data = {"r0": None, "r1": None}
        # New attributes
        self._register_states = {
            "r0": {"dirty": False, "last_modified": None},
            "r1": {"dirty": False, "last_modified": None}
        }

    # Accessors
    @property
    def data(self):
        return self._data

    # Mutators
    @data.setter
    def data(self, value):
        if isinstance(value, dict):
            self._data = value
        else:
            raise ValueError("Data must be a dictionary")

    # Read data to register address
    def read(self, address):
        super().read(output=False)
        return self._data[address]

    # Write data to register address
    def write(self, address, data):
        """Write data to register address"""
        super().write(output=False)
        self._data[address] = data
        self._register_states[address]["dirty"] = True
        self._register_states[address]["last_modified"] = time()

    # Return total execution time
    def get_exec_time(self):
        return self._exec_time

    def debug_info(self):
        """Return detailed debug information about the register state"""
        info = super().debug_info()
        info.update({
            "registers": self._data,
            "register_states": self._register_states
        })
        return info

    def print_debug_info(self):
        """Print formatted debug information about the register state"""
        info = self.debug_info()
        super().print_debug_info()
        print("\nRegister Contents:")
        for reg, value in info['registers'].items():
            state = info['register_states'][reg]
            state_str = "Dirty" if state["dirty"] else "Clean"
            last_modified = state["last_modified"] if state["last_modified"] else "Never"
            print(f"  {reg}: {value} ({state_str}, Last Modified: {last_modified})")

    def validate_state(self):
        """Validate the register state and return any issues found"""
        issues = super().validate_state()

        # Check register data
        if not isinstance(self._data, dict):
            issues.append("Register data is not a dictionary")
        else:
            # Check for required registers
            required_regs = ["r0", "r1"]
            for reg in required_regs:
                if reg not in self._data:
                    issues.append(f"Missing required register: {reg}")
                if reg not in self._register_states:
                    issues.append(f"Missing state for register: {reg}")

        # Check register states
        for reg, state in self._register_states.items():
            if reg not in self._data:
                issues.append(f"State exists for non-existent register: {reg}")
            if not isinstance(state["dirty"], bool):
                issues.append(f"Invalid dirty state for register {reg}")

        return issues

# Memory simulation architecture class
class ISA():
    def __init__(self):
        self._memory = None
        self._registers = Register()
        self._instructions = {
            "lb": self.load_b,
            "sb": self.store,
            "li": self.load_i,
            "j": self.jump,
        }
        self._output = ""
        self._instruction_counts = {
            "lb": 0,
            "sb": 0,
            "li": 0,
            "j": 0
        }
        self._instruction_times = {
            "lb": 0,
            "sb": 0,
            "li": 0,
            "j": 0
        }
        self._last_instruction_time = None
        # New attributes
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
        if self._memory is not None:
            print(f"ISA memory: {self._memory.name}")
            start = time()
            with open(file) as codefile:
                code = codefile.readlines()
                lines = [line.strip() for line in code if line.strip() != '']
                for line in lines:
                    self.parse_line(line)
            return time() - start
        else:
            print("Architecture has found no memory")
            return None

    # Parse line and send arguments
    # to the correct instruction
    def parse_line(self, line):
        tokens = line.split(' ')
        inst = tokens[0]
        start_time = time()

        if inst == "lb" or inst == "sb":
            print(f"{line}", end="")
        arg1 = tokens[1]
        if len(tokens) == 2 and inst == "li":
            arg2 = " "
            self._instructions[inst](arg1, arg2)
        elif len(tokens) > 2:
            arg2 = tokens[2]
            self._instructions[inst](arg1, arg2)
        else:
            self._instructions[inst](arg1)

        self._track_instruction(inst, start_time)

    # load data to register from
    # memory address
    def load_b(self, arg1, arg2):
        address = int(self._registers.read(arg2))
        data = self._memory.read(address)
        self._registers.write(arg1, data)
        if data is not None:
            print(data)

    # store data in register from
    # memory address
    def store(self, arg1, arg2):
        data = self._registers.read(arg1)
        address = int(self._registers.read(arg2))
        self._memory.write(address, data)
        if data is not None:
            print(data)

    # load number in register
    def load_i(self, arg1, arg2):
        self._registers.write(arg1, arg2)

    # jump instruction used to create
    # simulation output
    def jump(self, arg1):
        if arg1 == "100":
            data = self._registers.read('r0')
            if data is not None:
                self._output += data
            else:
                print("- NO DATA")
        else:
            print("Jump address not recognized.")

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
            "branch_prediction": self._branch_prediction
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
            required_instructions = ["lb", "sb", "li", "j"]
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
