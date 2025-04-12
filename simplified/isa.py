from enum import Enum, auto
from typing import List

class InstructionType(Enum):
    """Instruction types supported by the CPU"""
    MOV = auto()    # Move data between registers/memory
    LOAD = auto()   # Load from memory to register
    ADD = auto()    # Add two values
    SUB = auto()    # Subtract two values
    JMP = auto()    # Unconditional jump
    JZ = auto()     # Jump if zero
    HALT = auto()   # Stop execution
    NOT = auto()    # Logical NOT
    AND = auto()    # Logical AND
    OR = auto()     # Logical OR
    XOR = auto()    # Logical XOR (Exclusive OR)

    def execute_step(self) -> bool:
        """Execute one instruction"""
        if self.pc >= len(self.program):
            return False

        instruction = self.program[self.pc]
        opcode = instruction[0]
        operands = instruction[1:]

        # Update CPU state before execution
        self._print_state()

        # Execute instruction
        if opcode == InstructionType.MOV:
            self._execute_mov(operands)
        elif opcode == InstructionType.LOAD:
            self._execute_load(operands)
        elif opcode == InstructionType.ADD:
            self._execute_add(operands)
        elif opcode == InstructionType.SUB:
            self._execute_sub(operands)
        elif opcode == InstructionType.JMP:
            self._execute_jmp(operands)
        elif opcode == InstructionType.JZ:
            self._execute_jz(operands)
        elif opcode == InstructionType.HALT:
            return False
        elif opcode == InstructionType.NOT:
            self._execute_not(operands)
        elif opcode == InstructionType.AND:
            self._execute_and(operands)
        elif opcode == InstructionType.OR:
            self._execute_or(operands)
        elif opcode == InstructionType.XOR:
            self._execute_xor(operands)

    def _execute_xor(self, operands: List[str]) -> None:
        """Execute XOR instruction"""
        if len(operands) != 2:
            raise ValueError("XOR instruction requires exactly 2 operands")

        dest = operands[0]
        src = operands[1]

        # Get source value
        if src.startswith('#'):
            src_val = int(src[1:])
        elif src.startswith('['):
            src_val = self._read_memory(int(src[1:-1]))
        else:
            src_val = self.registers[src]

        # Get destination value
        if dest.startswith('['):
            dest_addr = int(dest[1:-1])
            dest_val = self._read_memory(dest_addr)
            result = dest_val ^ src_val
            self._write_memory(dest_addr, result)
            self.logger.log_register_operation(
                'XOR',
                f"Memory[{dest_addr}]",
                dest_val,
                result,
                f"XOR with {src_val}"
            )
        else:
            dest_val = self.registers[dest]
            result = dest_val ^ src_val
            self.registers[dest] = result
            self.logger.log_register_operation(
                'XOR',
                dest,
                dest_val,
                result,
                f"XOR with {src_val}"
            )
