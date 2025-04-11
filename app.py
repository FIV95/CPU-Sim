from isa import ISA
from memory import MainMemory
from cache import Cache
from utils.logger import CacheLogger
from time import time

if __name__ == "__main__":
    # Create shared logger
    logger = CacheLogger()

    # Create cache architecture
    main_memory = MainMemory()
    l2_cache = Cache("L2Cache", 16, 2, "fifo", 5, main_memory, logger)
    l1_cache = Cache("L1Cache", 8, 1, "lru", 1, l2_cache, logger)

    # Create ISA and set memory
    isa = ISA()
    isa.set_memory(l1_cache)

    # Read instructions from file
    isa.read_instructions("ex9_instructions")

    # Log final results
    logger.log_result(isa.output, isa.get_exec_time())
