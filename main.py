import sys
sys.path.append('..')
from memory import Memory
from cache.cache import Cache
from isa import SimpleISA
from utils.logger import Logger, LogLevel

def main():
    # Get test file from command line or use default
    test_file = sys.argv[1] if len(sys.argv) > 1 else 'tests/test_program.txt'

    # Initialize logger
    logger = Logger()
    logger.log(LogLevel.INFO, f"Starting simplified ISA simulator with test file: {test_file}")

    # Initialize memory hierarchy
    main_memory = Memory(name="MainMemory", size=1024)  # 1KB memory

    # Create L2 cache (slower, larger)
    l2_cache = Cache(
        name="L2",
        size=256,        # 256 bytes
        line_size=1,     # 1 byte per line (simplified for simulation)
        associativity=4, # 4-way set associative
        access_time=30,  # 30ns access time (3x slower than L1)
        write_policy="write-back",
        next_level=main_memory
    )

    # Create L1 cache (faster, smaller)
    l1_cache = Cache(
        name="L1",
        size=64,         # 64 bytes
        line_size=1,     # 1 byte per line (simplified for simulation)
        associativity=2, # 2-way set associative
        access_time=10,  # 10ns access time (fastest)
        write_policy="write-through",
        next_level=l2_cache
    )

    # Connect memory hierarchy (L1 -> L2 -> Main Memory)
    l1_cache.set_next_level(l2_cache)
    l2_cache.set_next_level(main_memory)

    # Initialize ISA
    isa = SimpleISA(memory=main_memory, cache=l1_cache)

    # Load test program
    try:
        with open(test_file, 'r') as f:
            program = f.readlines()
        isa.load_program(program)
        logger.log(LogLevel.INFO, "Program loaded successfully")
    except Exception as e:
        logger.log(LogLevel.ERROR, f"Error loading program: {str(e)}")
        return

    # Run program
    logger.log(LogLevel.INFO, "\n=== Starting Program Execution ===")
    isa.run()

    # Print cache performance
    if l1_cache:
        l1_stats = l1_cache.get_performance_stats()
        logger.log(LogLevel.INFO, "\nCache Performance:")
        logger.log(LogLevel.INFO, f"  Hits: {l1_stats['hits']}")
        logger.log(LogLevel.INFO, f"  Misses: {l1_stats['misses']}")
        logger.log(LogLevel.INFO, f"  Hit Rate: {l1_stats['hit_rate']:.2f}%")

        # Print final memory state
    logger.log(LogLevel.INFO, "\n=== Final Memory State ===")
    for addr in [100, 104, 108, 112]:
        value = main_memory.read(addr)
        logger.log(LogLevel.INFO, f"Memory[{addr}]: {value}")

        # Print cache statistics
    logger.log(LogLevel.INFO, "\n=== Cache Statistics ===")
    if l1_cache:
        l1_stats = l1_cache.get_performance_stats()
        logger.log(LogLevel.INFO, "L1 Cache (Fastest):")
        logger.log(LogLevel.INFO, f"  Hits: {l1_stats['hits']}")
        logger.log(LogLevel.INFO, f"  Misses: {l1_stats['misses']}")
        logger.log(LogLevel.INFO, f"  Hit Rate: {l1_stats['hit_rate']:.2f}%")
        logger.log(LogLevel.INFO, f"  Access Time: {l1_cache._access_time}ns")

    if l2_cache:
        l2_stats = l2_cache.get_performance_stats()
        logger.log(LogLevel.INFO, "\nL2 Cache (Medium):")
        logger.log(LogLevel.INFO, f"  Hits: {l2_stats['hits']}")
        logger.log(LogLevel.INFO, f"  Misses: {l2_stats['misses']}")
        logger.log(LogLevel.INFO, f"  Hit Rate: {l2_stats['hit_rate']:.2f}%")
        logger.log(LogLevel.INFO, f"  Access Time: {l2_cache._access_time}ns")

    logger.log(LogLevel.INFO, "\nMain Memory (Slowest):")
    logger.log(LogLevel.INFO, f"  Access Time: {main_memory._access_time}ns")

if __name__ == "__main__":
    main()
