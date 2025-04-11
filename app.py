from isa import ISA
from cache.cache import Cache
from memory import MainMemory
from utils.logger import Logger, LogLevel
import time

def print_transition_stats(cache):
    """Print cache transition statistics."""
    total_ops = len(cache._data_flow)
    upward_transitions = sum(1 for entry in cache._data_flow if entry['operation'] == 'READ' and entry.get('next_level_data') is not None)
    downward_transitions = sum(1 for entry in cache._data_flow if entry['operation'] == 'WRITE' and entry.get('next_level_data') is not None)

    logger = Logger()
    logger.log_cache_transitions(cache._name, {
        'total_ops': total_ops,
        'upward_transitions': upward_transitions,
        'downward_transitions': downward_transitions
    })

def print_cache_state_issues(cache):
    """Print cache state validation issues."""
    issues = cache.validate_state()
    if issues:
        logger = Logger()
        logger.log_cache_issues(cache._name, issues)

def print_entry_stats(cache):
    """Print cache entry statistics."""
    stats = cache.get_entry_stats()
    logger = Logger()
    logger.log_cache_entries(cache._name, stats)

def print_access_patterns(cache):
    """Print access pattern statistics for a cache."""
    patterns = cache.get_access_patterns()
    logger = Logger()
    logger.log_cache_patterns(cache._name, patterns)

def main():
    # Create a logger
    logger = Logger()
    logger.log_level = LogLevel.DEBUG  # Set to DEBUG to see all operations

    # Create memory hierarchy with larger block sizes and more associativity
    main_memory = MainMemory("MainMemory", 100)  # 100ns access time
    l2_cache = Cache("L2Cache", 32, 4, 4, 20, "write-back", main_memory, logger)  # 32 bytes, 4-way set associative, 4-byte blocks, 20ns access time
    l1_cache = Cache("L1Cache", 16, 2, 4, 10, "write-back", l2_cache, logger)  # 16 bytes, 2-way set associative, 4-byte blocks, 10ns access time

    # Create ISA
    isa = ISA()
    isa.set_memory(l1_cache)

    # Read instructions from file
    isa.read_instructions("ex9_instructions")

    # Print hierarchy information
    logger.log(LogLevel.INFO, "\n=== Cache Hierarchy Analysis ===")
    l1_cache.print_hierarchy_info()
    l2_cache.print_hierarchy_info()

    # Validate hierarchy
    l1_hierarchy_issues = l1_cache.validate_hierarchy()
    l2_hierarchy_issues = l2_cache.validate_hierarchy()

    if l1_hierarchy_issues:
        logger.log(LogLevel.WARNING, "\n=== L1 Cache Hierarchy Issues ===")
        for issue in l1_hierarchy_issues:
            logger.log(LogLevel.WARNING, f"- {issue}")

    if l2_hierarchy_issues:
        logger.log(LogLevel.WARNING, "\n=== L2 Cache Hierarchy Issues ===")
        for issue in l2_hierarchy_issues:
            logger.log(LogLevel.WARNING, f"- {issue}")

    # Print data flow history
    logger.log(LogLevel.INFO, "\n=== Data Flow History: L1Cache ===")
    for entry in l1_cache._data_flow:
        logger.log(LogLevel.INFO, f"\n[{time.time()}] {entry['operation']} at address {entry['address']}")
        logger.log(LogLevel.DEBUG, f"  Tag: {entry['tag']}, Index: {entry['set_index']}, Block: {entry['block_addr']}, Offset: {entry['offset']}")
        logger.log(LogLevel.DEBUG, f"  Data: {entry['data']}")
        logger.log(LogLevel.DEBUG, f"  Next Level Data: {entry.get('next_level_data', 'Not available')}")

    logger.log(LogLevel.INFO, "\n=== Data Flow History: L2Cache ===")
    for entry in l2_cache._data_flow:
        logger.log(LogLevel.INFO, f"\n[{time.time()}] {entry['operation']} at address {entry['address']}")
        logger.log(LogLevel.DEBUG, f"  Tag: {entry['tag']}, Index: {entry['set_index']}, Block: {entry['block_addr']}, Offset: {entry['offset']}")
        logger.log(LogLevel.DEBUG, f"  Data: {entry['data']}")
        logger.log(LogLevel.DEBUG, f"  Next Level Data: {entry.get('next_level_data', 'Not available')}")

    # Print cache transition stats
    print_transition_stats(l1_cache)
    print_transition_stats(l2_cache)

    # Print cache state issues
    print_cache_state_issues(l1_cache)
    print_cache_state_issues(l2_cache)

    # Print entry stats
    print_entry_stats(l1_cache)
    print_entry_stats(l2_cache)

    # Print access patterns
    print_access_patterns(l1_cache)
    print_access_patterns(l2_cache)

    # Print final output string
    logger.log(LogLevel.INFO, "\nOutput string: " + isa.output)
    logger.log(LogLevel.INFO, f"Total execution time: {l1_cache._exec_time + l2_cache._exec_time:.2f} nanoseconds")

if __name__ == "__main__":
    main()
