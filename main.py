import sys
sys.path.append('..')
from memory import Memory
from cache.cache import Cache
from isa import SimpleISA
from utils.logger import Logger, LogLevel
from PyQt5.QtWidgets import QApplication
from gui.simulator_gui import SimulatorGUI

def main():
    # Get test file from command line or use default
    test_file = sys.argv[1] if len(sys.argv) > 1 else 'tests/test_program.txt'

    # Initialize logger
    logger = Logger()
    logger.log(LogLevel.INFO, f"Starting simplified ISA simulator with test file: {test_file}")

    # Create memory hierarchy
    main_memory = Memory("MainMemory", 1024)  # 1KB memory

    # Create L2 cache (slower, larger)
    l2_cache = Cache(
        name="L2Cache",
        size=64,         # 64 bytes
        line_size=1,     # 1 byte per line for simplicity
        associativity=4, # 4-way set associative
        access_time=30,  # 30ns access time
        write_policy="write-back",
        next_level=main_memory,
        logger=logger
    )

    # Create L1 cache (faster, smaller)
    l1_cache = Cache(
        name="L1Cache",
        size=32,         # 32 bytes
        line_size=1,     # 1 byte per line for simplicity
        associativity=2, # 2-way set associative
        access_time=10,  # 10ns access time
        write_policy="write-through",
        next_level=l2_cache,
        logger=logger
    )

    # Connect memory hierarchy (L1 -> L2 -> Main Memory)
    l1_cache.set_next_level(l2_cache)
    l2_cache.set_next_level(main_memory)

    # Create ISA with L1 cache as its memory interface
    isa = SimpleISA(memory=main_memory, cache=l1_cache)

    # Create GUI with existing memory hierarchy
    app = QApplication(sys.argv)
    window = SimulatorGUI(main_memory=main_memory, l1_cache=l1_cache, l2_cache=l2_cache)
    window.load_instructions(test_file)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
