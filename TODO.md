# ISA Implementation TODO List

## Memory Operations
- [ ] STORE (register to memory)
- [ ] PUSH/POP (stack operations)

## Arithmetic
- [ ] MUL (multiplication)
- [ ] DIV (division)

## Logical
- [ ] NEG (negate)
- [ ] ROL/ROR (rotate left/right)

## Comparison
- [ ] JG/JL (jump if greater/less)
- [ ] JGE/JLE (jump if greater/equal or less/equal)

## Bit Manipulation
- [ ] BTS/BTR (bit test and set/reset)
- [ ] BSF/BSR (bit scan forward/reverse)

## Notes
- All instructions can be implemented using existing registers (eax, ebx, ecx, edx, esi, edi)
- Each new instruction will require:
  - Adding to InstructionType enum
  - Implementing execution method
  - Creating test cases
  - Updating documentation
