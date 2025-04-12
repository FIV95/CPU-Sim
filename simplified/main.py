import sys
sys.path.append('..')
from memory import Memory
from cache.cache import Cache
from isa import SimpleISA
from utils.logger import Logger, LogLevel

def main():
    # Initialize logger
    logger = Logger()
    logger.log(LogLevel.INFO, "Starting simplified ISA simulator")

    # Initialize memory hierarchy
    main_memory = Memory(name="MainMemory", size=1024)

    # L2 cache (medium speed, medium size)
    l2_cache = Cache(
        name="L2",
        size=256,        # 256 bytes
        line_size=16,    # 16 bytes per line (reduced from 64)
        associativity=4, # 4-way set associative
        write_policy="write-back",
        access_time=10   # 10ns access time
    )

    # L1 cache (fastest, smallest)
    l1_cache = Cache(
        name="L1",
        size=64,         # 64 bytes
        line_size=8,     # 8 bytes per line (reduced from 32)
        associativity=2, # 2-way set associative
        write_policy="write-through",
        access_time=1    # 1ns access time (10x faster than L2)
    )

    # Connect memory hierarchy (L1 -> L2 -> Main Memory)
    l1_cache.set_next_level(l2_cache)
    l2_cache.set_next_level(main_memory)

    # Initialize ISA
    isa = SimpleISA(memory=main_memory, cache=l1_cache)

    # Load test program
    try:
        with open('test_program.txt', 'r') as f:
            program = f.readlines()
        isa.load_program(program)
        logger.log(LogLevel.INFO, "Program loaded successfully")
    except Exception as e:
        logger.log(LogLevel.ERROR, f"Error loading program: {str(e)}")
        return

    # Run program
    logger.log(LogLevel.INFO, "\n=== Starting Program Execution ===")
    isa.run()

    # Print final memory state
    logger.log(LogLevel.INFO, "\n=== Final Memory State ===")
    for addr in range(100, 116, 4):
        value = main_memory.read(addr)
        logger.log(LogLevel.INFO, f"Memory[{addr}]: {value}")

    # Print cache statistics
    logger.log(LogLevel.INFO, "\n=== Cache Statistics ===")
    l1_stats = l1_cache.get_performance_stats()
    l2_stats = l2_cache.get_performance_stats()

    logger.log(LogLevel.INFO, "L1 Cache (Fastest):")
    logger.log(LogLevel.INFO, f"  Hits: {l1_stats['hit_count']}")
    logger.log(LogLevel.INFO, f"  Misses: {l1_stats['miss_count']}")
    hit_rate = (l1_stats['hit_count'] / (l1_stats['hit_count'] + l1_stats['miss_count']) * 100) if (l1_stats['hit_count'] + l1_stats['miss_count']) > 0 else 0
    logger.log(LogLevel.INFO, f"  Hit Rate: {hit_rate:.2f}%")
    logger.log(LogLevel.INFO, f"  Access Time: 1ns")

    logger.log(LogLevel.INFO, "\nL2 Cache (Medium):")
    logger.log(LogLevel.INFO, f"  Hits: {l2_stats['hit_count']}")
    logger.log(LogLevel.INFO, f"  Misses: {l2_stats['miss_count']}")
    hit_rate = (l2_stats['hit_count'] / (l2_stats['hit_count'] + l2_stats['miss_count']) * 100) if (l2_stats['hit_count'] + l2_stats['miss_count']) > 0 else 0
    logger.log(LogLevel.INFO, f"  Hit Rate: {hit_rate:.2f}%")
    logger.log(LogLevel.INFO, f"  Access Time: 10ns")

    logger.log(LogLevel.INFO, "\nMain Memory (Slowest):")
    logger.log(LogLevel.INFO, f"  Access Time: 100ns")

if __name__ == "__main__":
    main()
