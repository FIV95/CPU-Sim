from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QPushButton, QFrame, QSlider,
                            QTextEdit, QScrollArea, QTabWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import sys
import os

print("Starting simulator...")

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from isa import ISA
from cache.cache import Cache
from memory import MainMemory
from utils.logger import Logger, LogLevel

print("Imports successful...")

class SimulatorGUI(QMainWindow):
    def __init__(self):
        print("Initializing GUI...")
        super().__init__()
        self.setWindowTitle("CPU & Cache Simulator")
        self.setMinimumSize(1200, 800)
        print("Window created...")

        # Initialize dictionaries for UI elements
        self.register_labels = {}
        self.memory_labels = {}

        # Initialize ISA and components
        self.logger = Logger()
        self.logger.log_level = LogLevel.INFO

        # Create memory hierarchy
        print("Setting up memory hierarchy...")
        self.main_memory = MainMemory("MainMemory", 100)
        self.l2_cache = Cache("L2Cache", 32, 4, 4, 20, "write-back", self.main_memory, self.logger)
        self.l1_cache = Cache("L1Cache", 16, 2, 4, 10, "write-back", self.l2_cache, self.logger)

        # Create ISA
        self.isa = ISA()
        self.isa.set_memory(self.l1_cache)

        # Setup UI
        print("Setting up UI components...")
        self.setup_ui()

        # Initialize simulation state
        self.is_running = False
        self.simulation_speed = 1000  # milliseconds between steps
        self.current_instruction = 0
        self.instructions = []

        # Setup timer for continuous execution
        self.timer = QTimer()
        self.timer.timeout.connect(self.step_execution)
        print("GUI initialization complete...")

    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)  # Increased spacing
        main_layout.setContentsMargins(8, 8, 8, 8)  # Increased margins

        # Create sections
        self.cpu_section = self.create_cpu_section()
        self.register_section = self.create_register_section()
        self.memory_section = self.create_memory_section()
        self.ram_section = self.create_ram_section()
        self.array_section = self.create_array_visualization()
        self.control_section = self.create_controls()

        # Add sections to main layout
        main_layout.addWidget(self.cpu_section)

        # Create middle section with registers and cache
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(8)  # Increased spacing between register and cache sections

        # Add register section with stretch factor
        middle_layout.addWidget(self.register_section, 45)  # Increased to 45% of space
        middle_layout.addWidget(self.memory_section, 55)  # Decreased to 55% of space

        main_layout.addLayout(middle_layout)

        # Create memory view window (hidden by default)
        self.memory_window = QMainWindow(self)
        self.memory_window.setWindowTitle("Memory View")
        self.memory_window.setCentralWidget(self.ram_section)
        self.memory_window.setMinimumSize(800, 300)  # Increased height

        main_layout.addWidget(self.array_section)
        main_layout.addWidget(self.control_section)

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
        layout.setContentsMargins(8, 8, 8, 8)  # Increased padding for better spacing
        layout.setSpacing(4)  # Increased spacing between elements

        # Registers title with better spacing
        title = QLabel("Registers")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setContentsMargins(0, 0, 0, 4)  # Added bottom margin
        layout.addWidget(title)

        # Create register grid (8 rows x 4 columns)
        register_grid = QHBoxLayout()
        register_grid.setSpacing(6)  # Increased spacing between columns
        register_grid.setContentsMargins(0, 0, 0, 0)

        for col in range(4):
            col_layout = QVBoxLayout()
            col_layout.setSpacing(4)  # Increased spacing between registers
            col_layout.setContentsMargins(0, 0, 0, 0)
            for row in range(8):
                reg_num = col * 8 + row
                reg_frame = QFrame()
                reg_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
                reg_frame.setStyleSheet("""
                    QFrame {
                        background-color: #1e1e1e;
                        border: 1px solid #ffaa00;
                        border-radius: 3px;
                        padding: 2px;
                    }
                """)
                reg_layout = QHBoxLayout(reg_frame)
                reg_layout.setContentsMargins(6, 4, 6, 4)  # Increased padding
                reg_layout.setSpacing(6)  # Increased spacing between name and value

                reg_name = QLabel(f"R{reg_num}")
                reg_name.setFont(QFont("Courier", 11))
                reg_name.setStyleSheet("QLabel { color: #888888; }")
                reg_name.setFixedWidth(35)  # Increased width for register names
                reg_layout.addWidget(reg_name)

                value_label = QLabel("0")
                value_label.setFont(QFont("Courier", 11, QFont.Weight.Bold))
                value_label.setStyleSheet("QLabel { color: #ffaa00; }")
                value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
                value_label.setFixedWidth(40)  # Increased width for values
                self.register_labels[f"R{reg_num}"] = value_label
                reg_layout.addWidget(value_label)

                reg_frame.setFixedHeight(28)  # Increased height for better readability
                col_layout.addWidget(reg_frame)
            register_grid.addLayout(col_layout)

        layout.addLayout(register_grid)

        # Set a fixed size for the entire register section
        frame.setFixedWidth(380)  # Increased width for better proportions
        return frame

    def create_memory_section(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)  # Increased padding
        layout.setSpacing(6)  # Increased spacing

        # Create header with title and memory view button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Memory Hierarchy title
        title = QLabel("Cache Hierarchy")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(title)

        # Add stretch to push the button to the right
        header_layout.addStretch(1)

        # Create memory view button with better styling
        self.memory_view_button = QPushButton("Memory")
        self.memory_view_button.setFixedSize(80, 30)  # Smaller fixed size
        self.memory_view_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: #00ff00;
                border: 1px solid #00ff00;
                border-radius: 4px;
                padding: 2px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #3b3b3b;
            }
        """)
        self.memory_view_button.clicked.connect(self.toggle_memory_view)
        header_layout.addWidget(self.memory_view_button)

        layout.addLayout(header_layout)

        # L1 Cache (Fastest)
        l1_title = QLabel("L1 Cache (Fastest)")
        l1_title.setFont(QFont("Arial", 11))
        l1_title.setStyleSheet("QLabel { color: #ff69b4; }") # Hot pink for L1
        layout.addWidget(l1_title)

        # L1 Cache blocks (2 sets x 2 blocks)
        self.l1_blocks = {}
        l1_grid = QVBoxLayout()
        l1_grid.setSpacing(6)  # Increased spacing between sets
        for set_idx in range(2):
            set_layout = QHBoxLayout()
            set_layout.setSpacing(8)  # Increased spacing between blocks
            set_label = QLabel(f"Set {set_idx}:")
            set_label.setFont(QFont("Courier", 10))
            set_label.setStyleSheet("QLabel { color: #888888; }")
            set_label.setFixedWidth(60)  # Fixed width for set labels
            set_layout.addWidget(set_label)

            for block_idx in range(2):
                block = QFrame()
                block.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
                block.setStyleSheet("""
                    QFrame {
                        background-color: #1e1e1e;
                        border: 2px solid #ff69b4;
                        border-radius: 4px;
                        padding: 4px;
                    }
                """)
                block_layout = QVBoxLayout(block)
                block_layout.setContentsMargins(6, 6, 6, 6)
                block_layout.setSpacing(4)

                tag_label = QLabel("Tag: None")
                tag_label.setFont(QFont("Courier", 10))
                tag_label.setStyleSheet("QLabel { color: #888888; }")
                block_layout.addWidget(tag_label)

                data_label = QLabel("Data: None")
                data_label.setFont(QFont("Courier", 10))
                data_label.setStyleSheet("QLabel { color: #ff69b4; }")
                block_layout.addWidget(data_label)

                self.l1_blocks[f"{set_idx}_{block_idx}"] = (tag_label, data_label)
                set_layout.addWidget(block)

            l1_grid.addLayout(set_layout)
        layout.addLayout(l1_grid)

        # Add spacing between caches
        layout.addSpacing(12)

        # L2 Cache (Slower)
        l2_title = QLabel("L2 Cache (Slower)")
        l2_title.setFont(QFont("Arial", 11))
        l2_title.setStyleSheet("QLabel { color: #9370db; }") # Medium purple for L2
        layout.addWidget(l2_title)

        # L2 Cache blocks (4 sets x 4 blocks)
        self.l2_blocks = {}
        l2_grid = QVBoxLayout()
        l2_grid.setSpacing(6)  # Increased spacing between sets
        for set_idx in range(4):
            set_layout = QHBoxLayout()
            set_layout.setSpacing(8)  # Increased spacing between blocks
            set_label = QLabel(f"Set {set_idx}:")
            set_label.setFont(QFont("Courier", 10))
            set_label.setStyleSheet("QLabel { color: #888888; }")
            set_label.setFixedWidth(60)  # Fixed width for set labels
            set_layout.addWidget(set_label)

            for block_idx in range(4):
                block = QFrame()
                block.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
                block.setStyleSheet("""
                    QFrame {
                        background-color: #1e1e1e;
                        border: 2px solid #9370db;
                        border-radius: 4px;
                        padding: 4px;
                    }
                """)
                block_layout = QVBoxLayout(block)
                block_layout.setContentsMargins(6, 6, 6, 6)
                block_layout.setSpacing(4)

                tag_label = QLabel("Tag: None")
                tag_label.setFont(QFont("Courier", 10))
                tag_label.setStyleSheet("QLabel { color: #888888; }")
                block_layout.addWidget(tag_label)

                data_label = QLabel("Data: None")
                data_label.setFont(QFont("Courier", 10))
                data_label.setStyleSheet("QLabel { color: #9370db; }")
                block_layout.addWidget(data_label)

                self.l2_blocks[f"{set_idx}_{block_idx}"] = (tag_label, data_label)
                set_layout.addWidget(block)

            l2_grid.addLayout(set_layout)
        layout.addLayout(l2_grid)

        return frame

    def create_ram_section(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)

        # Main Memory (RAM)
        mem_level = QLabel("Main Memory (RAM)")
        mem_level.setFont(QFont("Arial", 11))
        mem_level.setStyleSheet("QLabel { color: #00ff00; }") # Green for RAM
        layout.addWidget(mem_level)

        # Memory array visualization in a grid (2 rows x 5 columns)
        self.memory_labels = {}
        memory_grid = QVBoxLayout()

        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        for i in range(10):
            cell = QFrame()
            cell.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
            cell.setStyleSheet("QFrame { background-color: #1e1e1e; border: 2px solid #00ff00; border-radius: 3px; }")
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(5, 5, 5, 5)

            addr_label = QLabel(f"Addr {i}")
            addr_label.setFont(QFont("Courier", 11))
            addr_label.setStyleSheet("QLabel { color: #888888; }")
            addr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_layout.addWidget(addr_label)

            value_label = QLabel("0")
            value_label.setFont(QFont("Courier", 12, QFont.Weight.Bold))
            value_label.setStyleSheet("QLabel { color: #00ff00; }")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.memory_labels[i] = value_label
            cell_layout.addWidget(value_label)

            cell.setMinimumWidth(100)
            cell.setMinimumHeight(60)

            if i < 5:
                row1.addWidget(cell)
            else:
                row2.addWidget(cell)

        memory_grid.addLayout(row1)
        memory_grid.addLayout(row2)
        layout.addLayout(memory_grid)

        return frame

    def create_array_visualization(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins

        # Array visualization
        self.array_visualization = QLabel()
        self.array_visualization.setFont(QFont("Courier", 12))
        self.array_visualization.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.array_visualization)

        return frame

    def create_controls(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        layout = QHBoxLayout(frame)

        # Control buttons
        self.step_button = QPushButton("Step")
        self.step_button.clicked.connect(self.step_execution)
        layout.addWidget(self.step_button)

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.toggle_run)
        layout.addWidget(self.run_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_simulation)
        layout.addWidget(self.reset_button)

        # Speed control
        speed_label = QLabel("Speed:")
        layout.addWidget(speed_label)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(2000)
        self.speed_slider.setValue(1000)
        self.speed_slider.valueChanged.connect(self.update_speed)
        layout.addWidget(self.speed_slider)

        return frame

    def load_instructions(self, filename):
        """Load instructions from file"""
        try:
            with open(filename, 'r') as f:
                self.instructions = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            self.current_instruction = 0
            self.update_display()
        except Exception as e:
            self.status_label.setText("Status: Error loading instructions")

    def step_execution(self):
        """Execute one instruction and update display"""
        if self.current_instruction < len(self.instructions):
            instruction = self.instructions[self.current_instruction]
            self.instruction_label.setText(f"Current Instruction: {instruction}")
            self.pc_label.setText(f"Program Counter: 0x{self.current_instruction:02x}")
            self.status_label.setText("Status: Executing...")

            # Execute instruction
            result = self.isa.parse_line(instruction)
            if result:
                self.status_label.setText("Status: Instruction Complete")
            else:
                self.status_label.setText("Status: Execution Failed")

            self.current_instruction += 1
            self.update_display()
        else:
            self.timer.stop()
            self.is_running = False
            self.run_button.setText("Run")
            self.status_label.setText("Status: Program Complete")

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
        self.isa = ISA()
        self.isa.set_memory(self.l1_cache)
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
        for i in range(32):
            reg_name = f"R{i}"
            value = self.isa.registers.read(reg_name)
            self.register_labels[reg_name].setText(f"{value if value is not None else 0}")

        # Update memory
        for i in range(10):
            value = self.isa.memory.read(i)
            self.memory_labels[i].setText(f"{value if value is not None else 0}")

        # Update L1 Cache blocks
        l1_info = self.l1_cache.debug_info()
        if 'blocks' in l1_info:
            for set_idx in range(2):
                for block_idx in range(2):
                    block_key = f"{set_idx}_{block_idx}"
                    block_info = l1_info['blocks'].get(block_key, {})
                    tag_label, data_label = self.l1_blocks[block_key]

                    tag = block_info.get('tag', 'None')
                    data = block_info.get('data', 'None')
                    tag_label.setText(f"Tag: {tag}")
                    data_label.setText(f"Data: {data}")

        # Update L2 Cache blocks
        l2_info = self.l2_cache.debug_info()
        if 'blocks' in l2_info:
            for set_idx in range(4):
                for block_idx in range(4):
                    block_key = f"{set_idx}_{block_idx}"
                    block_info = l2_info['blocks'].get(block_key, {})
                    tag_label, data_label = self.l2_blocks[block_key]

                    tag = block_info.get('tag', 'None')
                    data = block_info.get('data', 'None')
                    tag_label.setText(f"Tag: {tag}")
                    data_label.setText(f"Data: {data}")

        # Update array visualization
        array_data = [self.isa.memory.read(i) for i in range(10)]
        array_str = " ".join(f"{x if x is not None else 0:3}" for x in array_data)
        self.array_visualization.setText(array_str)

    def toggle_memory_view(self):
        if self.memory_window.isVisible():
            self.memory_window.hide()
            self.memory_view_button.setText("Show Memory View")
        else:
            self.memory_window.show()
            self.memory_view_button.setText("Hide Memory View")

def main():
    print("Starting main application...")
    app = QApplication(sys.argv)
    print("Created QApplication...")
    window = SimulatorGUI()
    print("Created main window...")
    window.load_instructions("ex9_instructions")
    print("Loaded instructions...")
    window.show()
    print("Showing window...")
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
