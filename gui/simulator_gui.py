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
            size=64,         # Reduced from 256 to 64 bytes
            line_size=1,     # Keep 1 byte per line for simplicity
            associativity=4, # 4-way set associative
            access_time=30,  # 30ns access time
            write_policy="write-back",
            next_level=self.main_memory,
            logger=self.logger
        )

        # Create L1 cache (faster, smaller)
        self.l1_cache = Cache(
            name="L1Cache",
            size=32,         # Reduced from 64 to 32 bytes
            line_size=1,     # Keep 1 byte per line for simplicity
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

        # Update the cache info display to reflect new sizes
        cache_info = [
            ("L1 Cache", "32 bytes", "1 byte", "2-way", "10ns", "Write-through"),
            ("L2 Cache", "64 bytes", "1 byte", "4-way", "30ns", "Write-back"),
            ("Main Memory", "1024 bytes", "N/A", "N/A", "100ns", "N/A")
        ]

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

        # Create all sections first
        self.system_info_section = self.create_system_info_section()
        self.cpu_section = self.create_cpu_section()
        self.register_section = self.create_register_section()
        self.memory_section = self.create_memory_section()
        self.control_section = self.create_controls()

        # Create left side layout for system info, CPU status, and registers
        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Add sections to left layout
        self.system_info_section.setFixedWidth(400)
        left_layout.addWidget(self.system_info_section)

        self.cpu_section.setFixedWidth(400)
        left_layout.addWidget(self.cpu_section)

        left_layout.addWidget(self.register_section)
        left_layout.addStretch()

        # Create main horizontal layout
        main_horizontal = QHBoxLayout()

        # Add left side layout
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        main_horizontal.addWidget(left_widget)

        # Add memory section with stretch to fill remaining space
        main_horizontal.addWidget(self.memory_section, 1)  # Added stretch factor of 1

        main_layout.addLayout(main_horizontal)
        main_layout.addWidget(self.control_section)

    def create_system_info_section(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # Create toggle button with left alignment
        toggle_button = QPushButton("Show System Information")
        toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: #00ff00;
                border: 1px solid #00ff00;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10pt;
                min-width: 150px;
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
        container_layout.setContentsMargins(4, 4, 4, 4)

        # System Configuration title
        title = QLabel("System Configuration")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        container_layout.addWidget(title)

        # Create grid for system info
        grid = QGridLayout()
        grid.setSpacing(8)

        # Cache Configuration
        cache_info = [
            ("L1 Cache", "32 bytes", "1 byte", "2-way", "10ns", "Write-through"),
            ("L2 Cache", "64 bytes", "1 byte", "4-way", "30ns", "Write-back"),
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
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        # Create grid layout for tightly grouped labels
        grid = QGridLayout()
        grid.setSpacing(4)

        # Title
        title = QLabel("CPU & Instruction Status")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        grid.addWidget(title, 0, 0, 1, 2)

        # Program Counter label and value
        pc_title = QLabel("Program Counter:")
        pc_title.setFont(QFont("Courier", 10))
        grid.addWidget(pc_title, 1, 0)

        self.pc_label = QLabel("0x00")
        self.pc_label.setFont(QFont("Courier", 10))
        self.pc_label.setStyleSheet("QLabel { color: #0099ff; }")
        grid.addWidget(self.pc_label, 1, 1)

        # Current Instruction label and value
        instr_title = QLabel("Current Instruction:")
        instr_title.setFont(QFont("Courier", 10))
        grid.addWidget(instr_title, 0, 2)

        self.instruction_label = QLabel("None")
        self.instruction_label.setFont(QFont("Courier", 10))
        self.instruction_label.setStyleSheet("QLabel { color: #00ff00; }")
        grid.addWidget(self.instruction_label, 0, 3)

        # Status label and value
        status_title = QLabel("Status:")
        status_title.setFont(QFont("Courier", 10))
        grid.addWidget(status_title, 1, 2)

        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Courier", 10))
        self.status_label.setStyleSheet("QLabel { color: #ffaa00; }")
        grid.addWidget(self.status_label, 1, 3)

        # Add grid to main layout
        layout.addLayout(grid)
        layout.addStretch()

        frame.setMaximumHeight(80)
        return frame

    def create_register_section(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header layout for title
        title = QLabel("Registers")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Create register grid for our actual registers
        register_grid = QGridLayout()  # Changed to grid layout
        register_grid.setSpacing(8)
        register_grid.setContentsMargins(4, 4, 4, 4)

        # Define our actual registers
        registers = ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi']
        self.register_labels = {}

        # Create registers in a 3x2 grid
        for i, reg_name in enumerate(registers):
            row = i // 2
            col = i % 2

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
            reg_layout.setContentsMargins(8, 4, 8, 4)
            reg_layout.setSpacing(8)

            reg_label = QLabel(reg_name)
            reg_label.setFont(QFont("Courier", 11))
            reg_label.setStyleSheet("QLabel { color: #888888; }")
            reg_layout.addWidget(reg_label)

            value_label = QLabel("0")
            value_label.setFont(QFont("Courier", 11, QFont.Weight.Bold))
            value_label.setStyleSheet("QLabel { color: #ffaa00; }")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.register_labels[reg_name] = value_label
            reg_layout.addWidget(value_label)

            register_grid.addWidget(reg_frame, row, col)

        # Add the grid to the layout
        layout.addLayout(register_grid)

        # Set fixed width and add stretch to fill vertical space
        frame.setFixedWidth(400)
        layout.addStretch()
        return frame

    def create_memory_section(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Cache title and stats in horizontal layout
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)

        # Left side: Cache Status title
        title = QLabel("Cache Status")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Right side: Cache statistics
        self.l1_stats_label = QLabel("L1 Cache: Hits: 0, Misses: 0, Hit Rate: 0.00%")
        self.l1_stats_label.setFont(QFont("Arial", 9))
        self.l1_stats_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(self.l1_stats_label)

        self.l2_stats_label = QLabel("L2 Cache: Hits: 0, Misses: 0, Hit Rate: 0.00%")
        self.l2_stats_label.setFont(QFont("Arial", 9))
        self.l2_stats_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(self.l2_stats_label)

        layout.addLayout(header_layout)

        # Create split layout for caches
        cache_layout = QHBoxLayout()
        cache_layout.setSpacing(20)

        # L1 Cache section
        l1_layout = QVBoxLayout()
        l1_title = QLabel("L1 Cache (2-way)")
        l1_title.setFont(QFont("Arial", 10))
        l1_title.setStyleSheet("QLabel { color: #ff69b4; }")
        l1_layout.addWidget(l1_title)

        # L1 Cache grid
        l1_grid = QGridLayout()
        l1_grid.setSpacing(4)

        # Create L1 cache blocks (16 sets, 2 blocks each)
        self.l1_blocks = {}
        for set_idx in range(16):
            set_label = QLabel(f"{set_idx}")
            set_label.setStyleSheet("QLabel { color: #888888; }")
            set_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            l1_grid.addWidget(set_label, set_idx, 0)

            for block_idx in range(2):
                block = QFrame()
                block.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
                block.setStyleSheet("""
                    QFrame {
                        background-color: #1e1e1e;
                        border: 1px solid #ff69b4;
                        border-radius: 2px;
                    }
                """)
                block_layout = QHBoxLayout(block)
                block_layout.setContentsMargins(4, 2, 4, 2)
                block_layout.setSpacing(0)

                value_label = QLabel("Empty")
                value_label.setStyleSheet("QLabel { color: #666666; }")
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                block_layout.addWidget(value_label)

                self.l1_blocks[f"{set_idx}_{block_idx}"] = value_label
                l1_grid.addWidget(block, set_idx, block_idx + 1)

        l1_layout.addLayout(l1_grid)
        cache_layout.addLayout(l1_layout)

        # Add vertical separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("QFrame { color: #666666; }")
        cache_layout.addWidget(separator)

        # L2 Cache section
        l2_layout = QVBoxLayout()
        l2_title = QLabel("L2 Cache (4-way)")
        l2_title.setFont(QFont("Arial", 10))
        l2_title.setStyleSheet("QLabel { color: #9370db; }")
        l2_layout.addWidget(l2_title)

        # L2 Cache grid
        l2_grid = QGridLayout()
        l2_grid.setSpacing(4)

        # Create L2 cache blocks (16 sets, 4 blocks each)
        self.l2_blocks = {}
        for set_idx in range(16):
            set_label = QLabel(f"{set_idx}")
            set_label.setStyleSheet("QLabel { color: #888888; }")
            set_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            l2_grid.addWidget(set_label, set_idx, 0)

            for block_idx in range(4):
                block = QFrame()
                block.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
                block.setStyleSheet("""
                    QFrame {
                        background-color: #1e1e1e;
                        border: 1px solid #9370db;
                        border-radius: 2px;
                    }
                """)
                block_layout = QHBoxLayout(block)
                block_layout.setContentsMargins(4, 2, 4, 2)
                block_layout.setSpacing(0)

                value_label = QLabel("Empty")
                value_label.setStyleSheet("QLabel { color: #666666; }")
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                block_layout.addWidget(value_label)

                self.l2_blocks[f"{set_idx}_{block_idx}"] = value_label
                l2_grid.addWidget(block, set_idx, block_idx + 1)

        l2_layout.addLayout(l2_grid)
        cache_layout.addLayout(l2_layout)

        layout.addLayout(cache_layout)
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
            self.instruction_label.setText("None")
            self.pc_label.setText("0x00")
            self.status_label.setText("Ready")
            self.update_display()
        except Exception as e:
            self.status_label.setText(f"Error loading instructions - {str(e)}")

    def step_execution(self):
        """Execute one instruction and update display"""
        if self.current_instruction < len(self.instructions):
            instruction = self.instructions[self.current_instruction]
            # Show a cleaner instruction display (without any trailing comments)
            self.instruction_label.setText(instruction)
            self.pc_label.setText(f"0x{self.current_instruction:02x}")
            self.status_label.setText("Executing...")

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
                    self.status_label.setText("Instruction Complete")
                else:
                    self.status_label.setText("Program Halted")
                    self.timer.stop()
                    self.is_running = False
                    self.run_button.setText("Run")

            except Exception as e:
                self.status_label.setText(f"Error - {str(e)}")
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
            self.status_label.setText("Program Complete")
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
        self.status_label.setText("Ready")
        self.instruction_label.setText("None")
        self.pc_label.setText("0x00")
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
        for set_idx in range(16):
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
        for set_idx in range(16):
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
