from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QPushButton, QFrame, QSlider,
                            QTextEdit, QScrollArea, QTabWidget, QGridLayout)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import sys
import os

print("Starting simulator...")

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from isa import SimpleISA
from cache.cache import Cache
from memory import MainMemory
from utils.logger import Logger, LogLevel

print("Imports successful...")

class SimulatorGUI(QMainWindow):
    def __init__(self):
        print("Initializing GUI...")
        super().__init__()
        self.setWindowTitle("CPU & Cache Simulator")
        self.setMinimumSize(1280, 800)
        print("Window created...")

        # Initialize dictionaries for UI elements
        self.register_labels = {}
        self.memory_labels = {}

        # Initialize ISA and components
        self.logger = Logger()
        self.logger.log_level = LogLevel.INFO

        # Create memory hierarchy with correct sizes
        print("Setting up memory hierarchy...")
        self.main_memory = MainMemory("MainMemory", 1024)  # 1KB memory

        # Create L2 cache (slower, larger)
        self.l2_cache = Cache(
            name="L2Cache",
            size=256,        # 256 bytes total size
            line_size=8,     # 8 bytes per line (more realistic)
            associativity=4, # 4-way set associative
            access_time=30,  # 30ns access time
            write_policy="write-back",
            next_level=self.main_memory,
            logger=self.logger
        )

        # Create L1 cache (faster, smaller)
        self.l1_cache = Cache(
            name="L1Cache",
            size=64,         # 64 bytes total size
            line_size=4,     # 4 bytes per line (more realistic)
            associativity=2, # 2-way set associative
            access_time=10,  # 10ns access time
            write_policy="write-through",
            next_level=self.l2_cache,
            logger=self.logger
        )

        # Explicitly connect the cache hierarchy
        self.l1_cache.set_next_level(self.l2_cache)
        self.l2_cache.set_next_level(self.main_memory)

        # Create ISA with L1 cache as its memory interface
        self.isa = SimpleISA(memory=self.main_memory, cache=self.l1_cache)

        # Setup UI
        print("Setting up UI components...")
        self.setup_ui()

        # Initialize simulation state
        self.is_running = False
        self.simulation_speed = 1000
        self.current_instruction = 0
        self.instructions = []

        # Setup timer for continuous execution
        self.timer = QTimer()
        self.timer.timeout.connect(self.step_execution)
        print("GUI initialization complete...")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Create sections
        self.system_info_section = self.create_system_info_section()
        self.cpu_section = self.create_cpu_section()
        self.register_section = self.create_register_section()
        self.memory_section = self.create_memory_section()
        self.control_section = self.create_controls()

        # Add sections to main layout
        main_layout.addWidget(self.system_info_section)
        main_layout.addWidget(self.cpu_section)

        # Create middle section with registers and cache
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(8)
        middle_layout.addWidget(self.register_section)
        middle_layout.addWidget(self.memory_section)

        main_layout.addLayout(middle_layout)
        main_layout.addWidget(self.control_section)

    def create_system_info_section(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)

        # Create toggle button
        toggle_button = QPushButton("Show System Information")
        toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: #00ff00;
                border: 1px solid #00ff00;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12pt;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #3b3b3b;
            }
            QPushButton:pressed {
                background-color: #1b1b1b;
            }
        """)
        layout.addWidget(toggle_button)

        # Create container widget for system info
        self.system_info_container = QWidget()
        container_layout = QVBoxLayout(self.system_info_container)
        container_layout.setSpacing(4)

        # System Configuration title
        title = QLabel("System Configuration")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        container_layout.addWidget(title)

        # Create grid for system info
        grid = QGridLayout()
        grid.setSpacing(8)

        # Cache Configuration
        cache_info = [
            ("L1 Cache", "64 bytes", "4 bytes", "2-way", "10ns", "Write-through"),
            ("L2 Cache", "256 bytes", "8 bytes", "4-way", "30ns", "Write-back"),
            ("Main Memory", "1024 bytes", "N/A", "N/A", "100ns", "N/A")
        ]

        # Headers
        headers = ["Component", "Size", "Line Size", "Associativity", "Access Time", "Write Policy"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            label.setStyleSheet("color: #00ff00;")
            grid.addWidget(label, 0, col)

        # Cache data
        for row, (name, size, line, assoc, time, policy) in enumerate(cache_info, 1):
            grid.addWidget(QLabel(name), row, 0)
            grid.addWidget(QLabel(size), row, 1)
            grid.addWidget(QLabel(line), row, 2)
            grid.addWidget(QLabel(assoc), row, 3)
            grid.addWidget(QLabel(time), row, 4)
            grid.addWidget(QLabel(policy), row, 5)

        container_layout.addLayout(grid)

        # Register Configuration
        reg_title = QLabel("Register Configuration")
        reg_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        reg_title.setStyleSheet("margin-top: 10px;")
        container_layout.addWidget(reg_title)

        reg_grid = QGridLayout()
        reg_grid.setSpacing(8)

        # Register info
        reg_info = [
            ("eax", "General Purpose Register"),
            ("ebx", "General Purpose Register"),
            ("ecx", "General Purpose Register"),
            ("edx", "General Purpose Register"),
            ("esi", "Source Index Register"),
            ("edi", "Destination Index Register")
        ]

        # Register headers
        reg_headers = ["Register", "Purpose"]
        for col, header in enumerate(reg_headers):
            label = QLabel(header)
            label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            label.setStyleSheet("color: #00ff00;")
            reg_grid.addWidget(label, 0, col)

        # Register data
        for row, (reg, purpose) in enumerate(reg_info, 1):
            reg_grid.addWidget(QLabel(reg), row, 0)
            reg_grid.addWidget(QLabel(purpose), row, 1)

        container_layout.addLayout(reg_grid)

        # Initially hide the system info
        self.system_info_container.hide()
        layout.addWidget(self.system_info_container)

        # Connect toggle button
        toggle_button.clicked.connect(self.toggle_system_info)

        return frame

    def toggle_system_info(self):
        """Toggle the visibility of system information"""
        if self.system_info_container.isVisible():
            self.system_info_container.hide()
            self.sender().setText("Show System Information")
        else:
            self.system_info_container.show()
            self.sender().setText("Hide System Information")

    def create_cpu_section(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)

        # CPU title
        title = QLabel("CPU & Instruction Status")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Current instruction with larger, more prominent display
        self.instruction_label = QLabel("Current Instruction: None")
        self.instruction_label.setFont(QFont("Courier", 12, QFont.Weight.Bold))
        self.instruction_label.setStyleSheet("QLabel { background-color: #2b2b2b; color: #00ff00; padding: 10px; border-radius: 5px; }")
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.instruction_label)

        # Program counter with enhanced visibility
        self.pc_label = QLabel("Program Counter: 0x00")
        self.pc_label.setFont(QFont("Courier", 11))
        self.pc_label.setStyleSheet("QLabel { color: #0099ff; }")
        layout.addWidget(self.pc_label)

        # Add status label
        self.status_label = QLabel("Status: Ready")
        self.status_label.setFont(QFont("Courier", 11))
        self.status_label.setStyleSheet("QLabel { color: #ffaa00; }")
        layout.addWidget(self.status_label)

        return frame

    def create_register_section(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header layout for title
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 4)

        # Registers title
        title = QLabel("Registers")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Create register grid for our actual registers
        register_grid = QVBoxLayout()
        register_grid.setSpacing(4)
        register_grid.setContentsMargins(0, 0, 0, 0)

        # Define our actual registers
        registers = ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi']
        self.register_labels = {}

        for reg_name in registers:
            reg_frame = QFrame()
            reg_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
            reg_frame.setStyleSheet("""
                QFrame {
                    background-color: #1e1e1e;
                    border: 1px solid #ffaa00;
                    border-radius: 2px;
                }
            """)
            reg_layout = QHBoxLayout(reg_frame)
            reg_layout.setContentsMargins(4, 2, 4, 2)
            reg_layout.setSpacing(4)

            reg_label = QLabel(reg_name)
            reg_label.setFont(QFont("Courier", 11))
            reg_label.setStyleSheet("QLabel { color: #888888; }")
            reg_label.setFixedWidth(32)
            reg_layout.addWidget(reg_label)

            value_label = QLabel("0")
            value_label.setFont(QFont("Courier", 11, QFont.Weight.Bold))
            value_label.setStyleSheet("QLabel { color: #ffaa00; }")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_label.setMinimumWidth(45)
            self.register_labels[reg_name] = value_label
            reg_layout.addWidget(value_label)

            reg_frame.setFixedHeight(24)
            register_grid.addWidget(reg_frame)

        # Add stretch to push registers to the top
        register_grid.addStretch()

        # Create a widget to hold the register grid
        register_container = QWidget()
        register_container.setLayout(register_grid)
        layout.addWidget(register_container)

        # Set a fixed size for the entire register section
        frame.setFixedWidth(200)
        return frame

    def create_memory_section(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Create header with title
        title = QLabel("Cache Status")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # L1 Cache (2-way set associative)
        l1_title = QLabel("L1 Cache (2-way)")
        l1_title.setFont(QFont("Arial", 11))
        l1_title.setStyleSheet("QLabel { color: #ff69b4; }")
        layout.addWidget(l1_title)

        # L1 Cache visualization
        self.l1_blocks = {}
        l1_grid = QGridLayout()
        l1_grid.setSpacing(4)

        # Headers for L1
        l1_grid.addWidget(QLabel("Set"), 0, 0)
        l1_grid.addWidget(QLabel("Block 0"), 0, 1)
        l1_grid.addWidget(QLabel("Block 1"), 0, 2)

        # Create L1 cache blocks (32 sets, 2 blocks each)
        for set_idx in range(32):  # 64 bytes / 1 byte per line / 2-way = 32 sets
            set_label = QLabel(f"{set_idx}")
            set_label.setStyleSheet("QLabel { color: #888888; }")
            l1_grid.addWidget(set_label, set_idx + 1, 0)

            for block_idx in range(2):
                block = QFrame()
                block.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
                block.setStyleSheet("""
                    QFrame {
                        background-color: #1e1e1e;
                        border: 1px solid #ff69b4;
                        border-radius: 2px;
                        min-height: 20px;
                    }
                """)
                block_layout = QHBoxLayout(block)
                block_layout.setContentsMargins(2, 2, 2, 2)

                value_label = QLabel("Empty")
                value_label.setStyleSheet("QLabel { color: #666666; }")  # Dim color for empty blocks
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                block_layout.addWidget(value_label)

                self.l1_blocks[f"{set_idx}_{block_idx}"] = value_label
                l1_grid.addWidget(block, set_idx + 1, block_idx + 1)

        # Create a widget to hold the L1 grid
        l1_container = QWidget()
        l1_container.setLayout(l1_grid)

        # Create a scroll area for L1 cache
        l1_scroll = QScrollArea()
        l1_scroll.setWidget(l1_container)
        l1_scroll.setWidgetResizable(True)
        l1_scroll.setMaximumHeight(200)
        layout.addWidget(l1_scroll)

        # Add spacing between caches
        layout.addSpacing(12)

        # L2 Cache (4-way set associative)
        l2_title = QLabel("L2 Cache (4-way)")
        l2_title.setFont(QFont("Arial", 11))
        l2_title.setStyleSheet("QLabel { color: #9370db; }")
        layout.addWidget(l2_title)

        # L2 Cache visualization
        self.l2_blocks = {}
        l2_grid = QGridLayout()
        l2_grid.setSpacing(4)

        # Headers for L2
        l2_grid.addWidget(QLabel("Set"), 0, 0)
        for i in range(4):
            l2_grid.addWidget(QLabel(f"Block {i}"), 0, i + 1)

        # Create L2 cache blocks (64 sets, 4 blocks each)
        for set_idx in range(64):  # 256 bytes / 1 byte per line / 4-way = 64 sets
            set_label = QLabel(f"{set_idx}")
            set_label.setStyleSheet("QLabel { color: #888888; }")
            l2_grid.addWidget(set_label, set_idx + 1, 0)

            for block_idx in range(4):
                block = QFrame()
                block.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
                block.setStyleSheet("""
                    QFrame {
                        background-color: #1e1e1e;
                        border: 1px solid #9370db;
                        border-radius: 2px;
                        min-height: 20px;
                    }
                """)
                block_layout = QHBoxLayout(block)
                block_layout.setContentsMargins(2, 2, 2, 2)

                value_label = QLabel("Empty")
                value_label.setStyleSheet("QLabel { color: #666666; }")  # Dim color for empty blocks
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                block_layout.addWidget(value_label)

                self.l2_blocks[f"{set_idx}_{block_idx}"] = value_label
                l2_grid.addWidget(block, set_idx + 1, block_idx + 1)

        # Create a widget to hold the L2 grid
        l2_container = QWidget()
        l2_container.setLayout(l2_grid)

        # Create a scroll area for L2 cache
        l2_scroll = QScrollArea()
        l2_scroll.setWidget(l2_container)
        l2_scroll.setWidgetResizable(True)
        l2_scroll.setMaximumHeight(200)
        layout.addWidget(l2_scroll)

        # Add cache statistics
        stats_frame = QFrame()
        stats_layout = QVBoxLayout(stats_frame)
        self.l1_stats_label = QLabel("L1 Cache: Hits: 0, Misses: 0, Hit Rate: 0%")
        self.l2_stats_label = QLabel("L2 Cache: Hits: 0, Misses: 0, Hit Rate: 0%")
        stats_layout.addWidget(self.l1_stats_label)
        stats_layout.addWidget(self.l2_stats_label)
        layout.addWidget(stats_frame)

        return frame

    def create_controls(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)

        # Control buttons with better styling
        button_style = """
            QPushButton {
                background-color: #2b2b2b;
                color: #00ff00;
                border: 1px solid #00ff00;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12pt;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3b3b3b;
            }
            QPushButton:pressed {
                background-color: #1b1b1b;
            }
        """

        self.step_button = QPushButton("Step")
        self.step_button.clicked.connect(self.step_execution)
        self.step_button.setStyleSheet(button_style)
        layout.addWidget(self.step_button)

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.toggle_run)
        self.run_button.setStyleSheet(button_style)
        layout.addWidget(self.run_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_simulation)
        self.reset_button.setStyleSheet(button_style)
        layout.addWidget(self.reset_button)

        # Speed control
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("QLabel { color: #00ff00; font-size: 12pt; }")
        layout.addWidget(speed_label)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(2000)
        self.speed_slider.setValue(1000)
        self.speed_slider.valueChanged.connect(self.update_speed)
        self.speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #00ff00;
                height: 8px;
                background: #2b2b2b;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00ff00;
                border: 1px solid #00ff00;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
        """)
        layout.addWidget(self.speed_slider)

        return frame

    def load_instructions(self, filename):
        """Load instructions from file"""
        try:
            with open(filename, 'r') as f:
                # Filter out empty lines and comments
                self.instructions = []
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comment-only lines
                    if not line or line.startswith(';'):
                        continue
                    # For lines with inline comments, only keep the instruction part
                    if ';' in line:
                        line = line.split(';')[0].strip()
                    if line:  # Only add non-empty lines
                        self.instructions.append(line)

            self.current_instruction = 0
            self.instruction_label.setText("Current Instruction: None")
            self.pc_label.setText("Program Counter: 0x00")
            self.status_label.setText("Status: Ready")
            self.update_display()
        except Exception as e:
            self.status_label.setText(f"Status: Error loading instructions - {str(e)}")

    def step_execution(self):
        """Execute one instruction and update display"""
        if self.current_instruction < len(self.instructions):
            instruction = self.instructions[self.current_instruction]
            # Show a cleaner instruction display (without any trailing comments)
            self.instruction_label.setText(f"Current Instruction: {instruction}")
            self.pc_label.setText(f"Program Counter: 0x{self.current_instruction:02x}")
            self.status_label.setText("Status: Executing...")

            # Force GUI update
            QApplication.processEvents()

            # Load and execute instruction
            try:
                # First load the program if we haven't already
                if self.current_instruction == 0:
                    self.isa.load_program(self.instructions)

                # Execute one step
                result = self.isa.execute_step()
                if result:
                    self.status_label.setText("Status: Instruction Complete")
                else:
                    self.status_label.setText("Status: Program Halted")
                    self.timer.stop()
                    self.is_running = False
                    self.run_button.setText("Run")

            except Exception as e:
                self.status_label.setText(f"Status: Error - {str(e)}")
                self.timer.stop()
                self.is_running = False
                self.run_button.setText("Run")

            self.current_instruction += 1
            self.update_display()

            # Force another GUI update after state changes
            QApplication.processEvents()
        else:
            self.timer.stop()
            self.is_running = False
            self.run_button.setText("Run")
            self.status_label.setText("Status: Program Complete")
            QApplication.processEvents()

    def toggle_run(self):
        """Toggle between run and pause states"""
        self.is_running = not self.is_running
        if self.is_running:
            self.run_button.setText("Pause")
            self.timer.start(self.simulation_speed)
        else:
            self.run_button.setText("Run")
            self.timer.stop()

    def reset_simulation(self):
        """Reset the simulation to initial state"""
        self.current_instruction = 0
        self.isa = SimpleISA(memory=self.main_memory, cache=self.l1_cache)
        self.status_label.setText("Status: Ready")
        self.instruction_label.setText("Current Instruction: None")
        self.pc_label.setText("Program Counter: 0x00")
        self.update_display()
        if self.is_running:
            self.toggle_run()

    def update_speed(self, value):
        """Update simulation speed"""
        self.simulation_speed = value
        if self.is_running:
            self.timer.setInterval(value)

    def update_display(self):
        """Update all visual elements based on current state"""
        # Update registers
        for reg_name in ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi']:
            value = self.isa.registers.get(reg_name, 0)
            self.register_labels[reg_name].setText(f"{value}")

        # Get cache states
        l1_info = self.l1_cache.get_cache_state()
        l2_info = self.l2_cache.get_cache_state()

        print("\nDEBUG: Cache States")
        print(f"L1 Cache: {l1_info}")
        print(f"L2 Cache: {l2_info}")

        # Update L1 Cache blocks
        for set_idx in range(32):
            for block_idx in range(2):
                block_key = f"{set_idx}_{block_idx}"
                if block_key in self.l1_blocks:
                    value_label = self.l1_blocks[block_key]
                    if (set_idx, block_idx) in l1_info:
                        value = l1_info[(set_idx, block_idx)]
                        display_text = f"T:0 V:{value}"
                        value_label.setText(display_text)
                        value_label.setStyleSheet("QLabel { background-color: #1e1e1e; color: #ff69b4; font-weight: bold; }")
                        print(f"DEBUG: Updating L1 block {block_key} with {display_text}")
                    else:
                        value_label.setText("Empty")
                        value_label.setStyleSheet("QLabel { background-color: #1e1e1e; color: #666666; }")
                        print(f"DEBUG: Setting L1 block {block_key} to Empty")
                    value_label.update()

        # Update L2 Cache blocks
        for set_idx in range(64):
            for block_idx in range(4):
                block_key = f"{set_idx}_{block_idx}"
                if block_key in self.l2_blocks:
                    value_label = self.l2_blocks[block_key]
                    if (set_idx, block_idx) in l2_info:
                        value = l2_info[(set_idx, block_idx)]
                        display_text = f"T:0 V:{value}"
                        value_label.setText(display_text)
                        value_label.setStyleSheet("QLabel { background-color: #1e1e1e; color: #9370db; font-weight: bold; }")
                        print(f"DEBUG: Updating L2 block {block_key} with {display_text}")
                    else:
                        value_label.setText("Empty")
                        value_label.setStyleSheet("QLabel { background-color: #1e1e1e; color: #666666; }")
                        print(f"DEBUG: Setting L2 block {block_key} to Empty")
                    value_label.update()

        # Update cache statistics
        l1_stats = self.l1_cache.get_performance_stats()
        l2_stats = self.l2_cache.get_performance_stats()

        self.l1_stats_label.setText(
            f"L1 Cache: Hits: {l1_stats['hits']}, "
            f"Misses: {l1_stats['misses']}, "
            f"Hit Rate: {l1_stats['hit_rate']:.2f}%"
        )

        self.l2_stats_label.setText(
            f"L2 Cache: Hits: {l2_stats['hits']}, "
            f"Misses: {l2_stats['misses']}, "
            f"Hit Rate: {l2_stats['hit_rate']:.2f}%"
        )

        # Force immediate update of the entire window
        self.repaint()
        QApplication.processEvents()

def main():
    print("Starting main application...")
    app = QApplication(sys.argv)
    print("Created QApplication...")
    window = SimulatorGUI()
    print("Created main window...")

    # Get test file from command line or use default
    test_file = sys.argv[1] if len(sys.argv) > 1 else 'tests/test_program.txt'
    window.load_instructions(test_file)
    print(f"Loaded instructions from {test_file}...")

    window.show()
    print("Showing window...")
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
