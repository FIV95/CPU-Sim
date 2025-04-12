import os
import sys
import traceback
import psutil
import gc
from isa import ISA
from memory import Memory
from cache.cache import Cache
from utils.logger import Logger, LogLevel

def get_memory_usage():
    """Get current process memory usage"""
    process = psutil.Process(os.getpid())
    return {
        'rss': process.memory_info().rss / 1024 / 1024,  # RSS in MB
        'vms': process.memory_info().vms / 1024 / 1024,  # VMS in MB
        'percent': process.memory_percent()
    }

def print_system_state(logger):
    """Print current system state"""
    mem_usage = get_memory_usage()
    logger.log(LogLevel.DEBUG, "\n=== System State ===")
    logger.log(LogLevel.DEBUG, f"Memory Usage: {mem_usage['rss']:.2f}MB RSS, {mem_usage['vms']:.2f}MB VMS ({mem_usage['percent']:.1f}%)")
    logger.log(LogLevel.DEBUG, f"Python Version: {sys.version}")
    logger.log(LogLevel.DEBUG, f"Platform: {sys.platform}")
    logger.log(LogLevel.DEBUG, f"Current Working Directory: {os.getcwd()}")

    # Get garbage collection stats
    gc.collect()
    gc_stats = gc.get_stats()
    logger.log(LogLevel.DEBUG, "\nGarbage Collection Stats:")
    for gen, stats in enumerate(gc_stats):
        logger.log(LogLevel.DEBUG, f"Generation {gen}: collections={stats['collections']}, collected={stats['collected']}, uncollectable={stats['uncollectable']}")

def main():
    # Initialize logger with debug level
    logger = Logger()
    logger.log_level = LogLevel.DEBUG  # Set log level to DEBUG
    logger.log(LogLevel.INFO, "Starting x86 bubble sort test")

    # Print initial system state
    print_system_state(logger)

    # Initialize memory hierarchy with debug info
    main_memory = Memory("Main Memory", 8192)  # 8KB memory to account for Python objects
    l2_cache = Cache("L2", 1024, 64, 4)  # 1KB cache, 64B lines, 4-way
    l1_cache = Cache("L1", 512, 64, 2)  # 512B cache, 64B lines, 2-way

    logger.log(LogLevel.DEBUG, "Memory Hierarchy Configuration:")
    logger.log(LogLevel.DEBUG, f"  Main Memory: Size={main_memory._size}B")
    logger.log(LogLevel.DEBUG, f"  L2 Cache: Size={l2_cache._size}B, Line Size={l2_cache._line_size}B, Ways={l2_cache._associativity}")
    logger.log(LogLevel.DEBUG, f"  L1 Cache: Size={l1_cache._size}B, Line Size={l1_cache._line_size}B, Ways={l1_cache._associativity}")

    # Connect memory hierarchy
    l1_cache.set_next_level(l2_cache)
    l2_cache.set_next_level(main_memory)
    logger.log(LogLevel.DEBUG, "Memory hierarchy connected: L1 -> L2 -> Main Memory")

    # Initialize ISA with L1 cache
    isa = ISA()
    isa.set_memory(l1_cache)  # Connect to L1 cache
    logger.log(LogLevel.DEBUG, "ISA initialized and connected to L1 cache")

    # Initialize test array in memory with debug info
    test_data = [9, 7, 5, 3, 1, 2, 4, 6, 8, 0]
    array_start = 32  # First cache line is reserved

    logger.log(LogLevel.DEBUG, "\n=== Array Initialization ===")
    logger.log(LogLevel.DEBUG, f"Array start address: {array_start}")
    logger.log(LogLevel.DEBUG, "Writing initial array values:")

    for i, value in enumerate(test_data):
        addr = array_start + i * 32  # Use 32-byte spacing to match object size
        logger.log(LogLevel.DEBUG, f"  Writing {value} to address {addr}")
        isa.memory.write(addr, value)  # Use ISA's memory interface

    logger.log(LogLevel.INFO, "Initial array:", test_data)

    # Print memory state after array initialization
    print_system_state(logger)

    # Initialize stack pointer and base pointer with debug info
    logger.log(LogLevel.DEBUG, "\n=== Stack Initialization ===")
    isa.registers['esp'] = (l1_cache._size // 64) * 64 - 64
    isa.registers['ebp'] = isa.registers['esp']
    logger.log(LogLevel.DEBUG, f"Stack pointer (esp) initialized to: {isa.registers['esp']}")
    logger.log(LogLevel.DEBUG, f"Base pointer (ebp) initialized to: {isa.registers['ebp']}")
    logger.log(LogLevel.DEBUG, f"Available stack space: {isa.registers['esp'] - array_start - (len(test_data) * 64)}B")

    # Initialize registers for bubble sort
    logger.log(LogLevel.DEBUG, "\n=== Register Initialization ===")
    isa.registers['esi'] = 0  # i (outer loop counter)
    isa.registers['edi'] = 0  # j (inner loop counter)
    isa.registers['ecx'] = 9  # n-1 (array size - 1)
    isa.registers['edx'] = 0  # temporary for comparisons
    isa.registers['eax'] = 0  # first memory address and first value
    isa.registers['ebx'] = 0  # second memory address and second value
    isa.registers['ebp'] = array_start  # array base address
    logger.log(LogLevel.DEBUG, "Registers initialized for bubble sort:")
    for reg in ['esi', 'edi', 'ecx', 'edx', 'eax', 'ebx', 'ebp']:
        logger.log(LogLevel.DEBUG, f"  {reg}: {isa.registers[reg]}")

    # Read and execute bubble sort program
    logger.log(LogLevel.DEBUG, "\n=== Program Loading ===")
    if not isa.read_instructions("x86_bubble_sort.asm"):
        logger.log(LogLevel.ERROR, "Failed to read instructions")
        return
    logger.log(LogLevel.DEBUG, f"Loaded {len(isa.instructions)} instructions")

    # Execute instructions with detailed logging
    logger.log(LogLevel.DEBUG, "\n=== Program Execution ===")
    logger.log(LogLevel.DEBUG, "Initial register values:")
    for reg in ['esi', 'edi', 'ecx', 'edx', 'eax', 'ebx', 'ebp', 'esp']:
        logger.log(LogLevel.DEBUG, f"  {reg}: {isa.registers[reg]}")

    # Execute instructions using instruction pointer
    while isa.registers['eip'] < len(isa.instructions):
        instruction = isa.instructions[isa.registers['eip']]
        logger.log(LogLevel.DEBUG, f"\nExecuting instruction {isa.registers['eip']}: {instruction}")
        logger.log(LogLevel.DEBUG, "Register values before execution:")
        for reg in ['esi', 'edi', 'ecx', 'edx', 'eax', 'ebx', 'ebp', 'esp']:
            logger.log(LogLevel.DEBUG, f"  {reg}: {isa.registers[reg]}")

        # Print array state before each instruction
        logger.log(LogLevel.DEBUG, "\nArray state before instruction:")
        array_state = []
        for j in range(10):
            addr = array_start + j * 32
            value = isa.memory.read(addr)
            array_state.append(value)
            logger.log(LogLevel.DEBUG, f"  Index {j}: addr={addr}, value={value}")
        logger.log(LogLevel.DEBUG, f"Array: {array_state}")

        # Enhanced memory operation tracking
        if instruction[0] in ["mov", "add", "sub", "cmp"]:
            # Track memory reads
            if any(op.startswith('[') for op in instruction[1]):
                addr = None
                if instruction[1][0].startswith('['):
                    addr_expr = instruction[1][0].strip('[]')
                    # Handle register-based addressing
                    for reg in ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp']:
                        if reg in addr_expr:
                            addr_expr = addr_expr.replace(reg, str(isa.registers[reg]))
                    addr = eval(addr_expr)
                    value = isa.memory.read(addr)
                    logger.log(LogLevel.DEBUG, f"Memory READ at {addr}: got value {value}")
                    l1_stats = l1_cache.get_performance_stats()
                    l2_stats = l2_cache.get_performance_stats()
                    logger.log(LogLevel.DEBUG, f"  L1 Cache stats: hits={l1_stats.get('hits', 0)}, misses={l1_stats.get('misses', 0)}")
                    logger.log(LogLevel.DEBUG, f"  L2 Cache stats: hits={l2_stats.get('hits', 0)}, misses={l2_stats.get('misses', 0)}")
                if len(instruction[1]) > 1 and instruction[1][1].startswith('['):
                    addr_expr = instruction[1][1].strip('[]')
                    # Handle register-based addressing
                    for reg in ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp']:
                        if reg in addr_expr:
                            addr_expr = addr_expr.replace(reg, str(isa.registers[reg]))
                    addr = eval(addr_expr)
                    value = isa.memory.read(addr)
                    logger.log(LogLevel.DEBUG, f"Memory READ at {addr}: got value {value}")
                    l1_stats = l1_cache.get_performance_stats()
                    l2_stats = l2_cache.get_performance_stats()
                    logger.log(LogLevel.DEBUG, f"  L1 Cache stats: hits={l1_stats.get('hits', 0)}, misses={l1_stats.get('misses', 0)}")
                    logger.log(LogLevel.DEBUG, f"  L2 Cache stats: hits={l2_stats.get('hits', 0)}, misses={l2_stats.get('misses', 0)}")

            # Track memory writes for mov instructions
            if instruction[0] == "mov" and instruction[1][0].startswith('['):
                addr_expr = instruction[1][0].strip('[]')
                # Handle register-based addressing
                for reg in ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp']:
                    if reg in addr_expr:
                        addr_expr = addr_expr.replace(reg, str(isa.registers[reg]))
                addr = eval(addr_expr)
                if instruction[1][1] in isa.registers:
                    value = isa.registers[instruction[1][1]]
                else:
                    value = int(instruction[1][1])
                logger.log(LogLevel.DEBUG, f"Memory WRITE at {addr}: writing value {value}")
                l1_stats = l1_cache.get_performance_stats()
                l2_stats = l2_cache.get_performance_stats()
                logger.log(LogLevel.DEBUG, f"  L1 Cache stats: hits={l1_stats.get('hits', 0)}, misses={l1_stats.get('misses', 0)}")
                logger.log(LogLevel.DEBUG, f"  L2 Cache stats: hits={l2_stats.get('hits', 0)}, misses={l2_stats.get('misses', 0)}")

        if not isa.execute_instruction(instruction):
            logger.log(LogLevel.ERROR, f"Failed to execute instruction at {isa.registers['eip']}: {instruction}")
            break

        # Increment instruction pointer if not a jump/branch instruction
        if instruction[0] not in ["jmp", "je", "jne", "jg", "jl", "jge", "jle"]:
            isa.registers['eip'] += 1

        logger.log(LogLevel.DEBUG, "Register values after execution:")
        for reg in ['esi', 'edi', 'ecx', 'edx', 'eax', 'ebx', 'ebp', 'esp']:
            logger.log(LogLevel.DEBUG, f"  {reg}: {isa.registers[reg]}")

        # Print array state after each instruction
        logger.log(LogLevel.DEBUG, "\nArray state after instruction:")

        # Write back all dirty cache lines to main memory
        l1_cache.write_back_all()  # Write back from L1 to L2
        l2_cache.write_back_all()  # Write back from L2 to main memory

        array_state = []
        for j in range(10):
            addr = array_start + j * 32
            value = isa.memory.read(addr)
            array_state.append(value)
            logger.log(LogLevel.DEBUG, f"  Index {j}: addr={addr}, value={value}")
        logger.log(LogLevel.DEBUG, f"Array: {array_state}")

    # Print final memory state
    logger.log(LogLevel.DEBUG, "\n=== Final Memory State ===")
    # Write back all dirty cache lines to main memory
    l1_cache.write_back_all()  # Write back from L1 to L2
    l2_cache.write_back_all()  # Write back from L2 to main memory

    # Read final array values
    final_array = []
    for i in range(10):
        addr = array_start + i * 32
        value = isa.memory.read(addr)
        final_array.append(value)
    logger.log(LogLevel.INFO, "Final sorted array:", final_array)

    # Print final system state
    print_system_state(logger)

    # Print detailed performance statistics
    logger.log(LogLevel.DEBUG, "\n=== Performance Statistics ===")

    isa_stats = isa.get_performance_stats()
    logger.log(LogLevel.INFO, "ISA Statistics:")
    logger.log(LogLevel.DEBUG, f"  Instructions executed: {isa_stats['instruction_count']}")
    logger.log(LogLevel.DEBUG, f"  Execution time: {isa_stats['execution_time']:.6f}s")
    logger.log(LogLevel.DEBUG, f"  Instructions per second: {isa_stats['instructions_per_second']:.2f}")

    l1_stats = l1_cache.get_performance_stats()
    logger.log(LogLevel.INFO, "L1 Cache Statistics:")
    logger.log(LogLevel.DEBUG, f"  Hits: {l1_stats.get('hits', 0)}")
    logger.log(LogLevel.DEBUG, f"  Misses: {l1_stats.get('misses', 0)}")
    logger.log(LogLevel.DEBUG, f"  Hit rate: {l1_stats.get('hit_rate', 0):.2%}")

    l2_stats = l2_cache.get_performance_stats()
    logger.log(LogLevel.INFO, "L2 Cache Statistics:")
    logger.log(LogLevel.DEBUG, f"  Hits: {l2_stats.get('hits', 0)}")
    logger.log(LogLevel.DEBUG, f"  Misses: {l2_stats.get('misses', 0)}")
    logger.log(LogLevel.DEBUG, f"  Hit rate: {l2_stats.get('hit_rate', 0):.2%}")

    mem_stats = main_memory.get_performance_stats()
    logger.log(LogLevel.INFO, "Main Memory Statistics:")
    logger.log(LogLevel.DEBUG, f"  Reads: {mem_stats.get('reads', 0)}")
    logger.log(LogLevel.DEBUG, f"  Writes: {mem_stats.get('writes', 0)}")
    logger.log(LogLevel.DEBUG, f"  Total accesses: {mem_stats.get('total_accesses', 0)}")

if __name__ == "__main__":
    main()
