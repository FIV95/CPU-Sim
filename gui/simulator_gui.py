from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QPushButton, QFrame, QSlider,
                            QTextEdit, QScrollArea, QTabWidget, QGridLayout, QDialog)
from PyQt6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QPen, QBrush
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

class FlowLine(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_point = QPoint(0, 0)
        self.end_point = QPoint(0, 0)
        self.active = False
        self.color = QColor("#00ff00")  # Default green color
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_points(self, start, end):
        self.start_point = start
        self.end_point = end
        self.update()

    def set_active(self, active, operation_type="read"):
        self.active = active
        self.color = QColor("#00ff00") if operation_type == "read" else QColor("#ff69b4")
        self.update()

    def paintEvent(self, event):
        if not self.active:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(self.color, 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        # Draw flow line with arrow
        painter.drawLine(self.start_point, self.end_point)

        # Draw arrow head
        arrow_size = 10
        angle = 30  # degrees

        # Calculate arrow head points
        dx = self.end_point.x() - self.start_point.x()
        dy = self.end_point.y() - self.start_point.y()
        length = (dx * dx + dy * dy) ** 0.5

        if length == 0:
            return

        dx /= length
        dy /= length

        # Calculate arrow points
        x1 = self.end_point.x() - arrow_size * (dx * 0.866 + dy * 0.5)
        y1 = self.end_point.y() - arrow_size * (dy * 0.866 - dx * 0.5)
        x2 = self.end_point.x() - arrow_size * (dx * 0.866 - dy * 0.5)
        y2 = self.end_point.y() - arrow_size * (dy * 0.866 + dx * 0.5)

        # Draw arrow head
        points = [self.end_point, QPoint(int(x1), int(y1)), QPoint(int(x2), int(y2))]
        painter.setBrush(QBrush(self.color))
        painter.drawPolygon(*points)

class SimulatorGUI(QMainWindow):
    def __init__(self, main_memory=None, l1_cache=None, l2_cache=None):
        print("Initializing GUI...")
        super().__init__()
        self.setWindowTitle("CPU & Cache Simulator")
        self.setMinimumSize(1200, 400)
        print("Window created...")

        # Initialize dictionaries for UI elements
        self.register_labels = {}
        self.memory_labels = {}

        # Initialize ISA and components
        self.logger = Logger()
        self.logger.log_level = LogLevel.INFO

        # Use provided memory hierarchy or create new one
        if main_memory and l1_cache and l2_cache:
            self.main_memory = main_memory
            self.l1_cache = l1_cache
            self.l2_cache = l2_cache
        else:
            # Create memory hierarchy with correct sizes
            print("Setting up memory hierarchy...")
            self.main_memory = MainMemory("MainMemory", 1024)  # 1KB memory

            # Initialize memory with test values
            self.main_memory.write(100, 168)  # 42 shifted left by 2
            self.main_memory.write(104, 61)   # 123 shifted right by 1
            self.main_memory.write(108, 265)  # 255 + 10
            self.main_memory.write(112, -5)   # 0 - 5
            self.main_memory.write(116, 16)   # 16 AND 240
            self.main_memory.write(120, 111)  # 99 OR 15
            self.main_memory.write(124, 200)
            self.main_memory.write(128, 300)
            self.main_memory.write(132, 400)
            self.main_memory.write(136, 500)
            self.main_memory.write(140, 600)
            self.main_memory.write(144, 700)
            self.main_memory.write(148, 800)
            self.main_memory.write(152, 900)

            # Create L2 cache (slower, larger)
            self.l2_cache = Cache(
                name="L2Cache",
                size=64,         # 64 bytes
                line_size=1,     # 1 byte per line for simplicity
                associativity=4, # 4-way set associative
                access_time=30,  # 30ns access time
                write_policy="write-back",
                next_level=self.main_memory,
                logger=self.logger
            )

            # Create L1 cache (faster, smaller)
            self.l1_cache = Cache(
                name="L1Cache",
                size=32,         # 32 bytes
                line_size=1,     # 1 byte per line for simplicity
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

        self.used_memory_blocks = set([100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, 148, 152])
        self.memory_window = None  # Store reference to memory window

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Create all sections first
        self.system_info_section = self.create_system_info_section()
        self.cpu_section = self.create_cpu_section()
        self.register_section = self.create_register_section()
        self.memory_section = self.create_memory_section()
        self.control_section = self.create_controls()

        # Create left side layout for system info, CPU status, and registers
        left_layout = QVBoxLayout()
        left_layout.setSpacing(2)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Add sections to left layout
        self.system_info_section.setFixedWidth(300)
        left_layout.addWidget(self.system_info_section)

        self.cpu_section.setFixedWidth(300)
        left_layout.addWidget(self.cpu_section)

        left_layout.addWidget(self.register_section)

        # Create main horizontal layout
        main_horizontal = QHBoxLayout()
        main_horizontal.setSpacing(4)

        # Add left side layout
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        main_horizontal.addWidget(left_widget)

        # Add memory section
        main_horizontal.addWidget(self.memory_section, 1)

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
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        # Create grid layout for tightly grouped labels
        grid = QGridLayout()
        grid.setSpacing(2)

        # Title with smaller width
        title = QLabel("CPU & Instruction Status")
        title.setFont(QFont("Arial", 9))
        grid.addWidget(title, 0, 0, 1, 2)

        # Program Counter label and value
        pc_title = QLabel("PC:")  # Shortened
        pc_title.setFont(QFont("Courier", 9))  # Smaller font
        grid.addWidget(pc_title, 1, 0)

        self.pc_label = QLabel("0x00")
        self.pc_label.setFont(QFont("Courier", 9))  # Smaller font
        self.pc_label.setStyleSheet("QLabel { color: #0099ff; }")
        grid.addWidget(self.pc_label, 1, 1)

        # Current Instruction label and value
        instr_title = QLabel("Instr:")  # Shortened
        instr_title.setFont(QFont("Courier", 9))  # Smaller font
        grid.addWidget(instr_title, 0, 2)

        self.instruction_label = QLabel("None")
        self.instruction_label.setFont(QFont("Courier", 9))  # Smaller font
        self.instruction_label.setStyleSheet("QLabel { color: #00ff00; }")
        grid.addWidget(self.instruction_label, 0, 3)

        # Status label and value
        status_title = QLabel("Status:")
        status_title.setFont(QFont("Courier", 9))  # Smaller font
        grid.addWidget(status_title, 1, 2)

        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Courier", 9))  # Smaller font
        self.status_label.setStyleSheet("QLabel { color: #ffaa00; }")
        grid.addWidget(self.status_label, 1, 3)

        # Add grid to main layout
        layout.addLayout(grid)

        frame.setFixedWidth(300)  # Reduced from 400
        frame.setFixedHeight(45)  # Reduced from 50
        return frame

    def create_register_section(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        frame.setFixedWidth(300)  # Reduced from 400
        frame.setFixedHeight(90)  # Reduced from 100
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 2, 4, 2)  # Minimal margins
        layout.setSpacing(2)  # Minimal spacing

        # Header layout for title
        title = QLabel("Registers")
        title.setFont(QFont("Arial", 10))  # Smaller font
        layout.addWidget(title)

        # Create register grid
        register_grid = QGridLayout()
        register_grid.setSpacing(2)  # Minimal spacing
        register_grid.setContentsMargins(2, 2, 2, 2)  # Minimal margins

        # Define registers
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
            reg_layout.setContentsMargins(4, 2, 4, 2)  # Minimal margins
            reg_layout.setSpacing(4)  # Minimal spacing

            reg_label = QLabel(reg_name)
            reg_label.setFont(QFont("Courier", 9))  # Smaller font
            reg_label.setStyleSheet("QLabel { color: #888888; }")
            reg_layout.addWidget(reg_label)

            value_label = QLabel("0")
            value_label.setFont(QFont("Courier", 9))  # Smaller font
            value_label.setStyleSheet("QLabel { color: #ffaa00; }")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.register_labels[reg_name] = value_label
            reg_layout.addWidget(value_label)

            reg_frame.setFixedHeight(24)  # Match cache block height
            register_grid.addWidget(reg_frame, row, col)

        # Add the grid to the layout
        layout.addLayout(register_grid)
        return frame

    def create_memory_section(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        frame.setMinimumWidth(900)
        frame.setMaximumHeight(180)

        main_layout = QVBoxLayout(frame)
        main_layout.setContentsMargins(4, 2, 4, 2)
        main_layout.setSpacing(2)

        # Ultra-compact header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        title = QLabel("Cache Status")
        title.setFont(QFont("Arial", 11))
        header_layout.addWidget(title)

        # Stats in single compact line
        self.l1_stats_label = QLabel("L1: H:0 M:0 R:0%")  # Shortened stats
        self.l1_stats_label.setFont(QFont("Arial", 10))
        self.l1_stats_label.setStyleSheet("color: #ff69b4;")
        header_layout.addWidget(self.l1_stats_label)

        self.l2_stats_label = QLabel("L2: H:0 M:0 R:0%")  # Shortened stats
        self.l2_stats_label.setFont(QFont("Arial", 10))
        self.l2_stats_label.setStyleSheet("color: #9370db;")
        header_layout.addWidget(self.l2_stats_label)

        main_layout.addWidget(header)

        # Cache container
        cache_container = QWidget()
        cache_layout = QHBoxLayout(cache_container)
        cache_layout.setSpacing(16)
        cache_layout.setContentsMargins(0, 0, 0, 0)

        # L1 Cache
        l1_widget = QWidget()
        l1_layout = QVBoxLayout(l1_widget)
        l1_layout.setSpacing(1)
        l1_layout.setContentsMargins(0, 0, 0, 0)
        l1_widget.setFixedWidth(240)  # Adjusted for 75px blocks

        l1_title = QLabel("L1 (2-way)")
        l1_title.setFont(QFont("Arial", 9))  # Smaller font
        l1_title.setStyleSheet("color: #ff69b4;")
        l1_layout.addWidget(l1_title)

        l1_grid = QGridLayout()
        l1_grid.setSpacing(1)
        l1_grid.setHorizontalSpacing(1)
        l1_grid.setVerticalSpacing(1)
        self.l1_blocks = {}

        for row, set_idx in enumerate([0, 4, 8, 12]):
            set_label = QLabel(f"S{set_idx}")
            set_label.setStyleSheet("color: #aaaaaa; font-size: 9pt;")
            set_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            set_label.setFixedWidth(20)
            l1_grid.addWidget(set_label, row, 0)

            for way in range(2):
                block = QFrame()
                block.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
                block.setFixedSize(75, 20)  # Set to 75px width
                block.setStyleSheet("""
                    QFrame {
                        background-color: #1e1e1e;
                        border: 1px solid #ff69b4;
                        border-radius: 2px;
                    }
                """)

                layout = QHBoxLayout(block)
                layout.setContentsMargins(2, 1, 2, 1)  # Minimal margins
                layout.setSpacing(0)

                value_label = QLabel("Empty")
                value_label.setStyleSheet("color: #666666; font-size: 9pt;")
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(value_label)

                self.l1_blocks[f"{set_idx}_{way}"] = value_label
                l1_grid.addWidget(block, row, way + 1)

        l1_layout.addLayout(l1_grid)
        cache_layout.addWidget(l1_widget)

        # Thin separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("background-color: #333333;")
        separator.setFixedWidth(1)
        cache_layout.addWidget(separator)

        # L2 Cache
        l2_widget = QWidget()
        l2_layout = QVBoxLayout(l2_widget)
        l2_layout.setSpacing(1)
        l2_layout.setContentsMargins(0, 0, 0, 0)
        l2_widget.setFixedWidth(460)  # Adjusted for 75px blocks

        l2_title = QLabel("L2 (4-way)")
        l2_title.setFont(QFont("Arial", 9))  # Smaller font
        l2_title.setStyleSheet("color: #9370db;")
        l2_layout.addWidget(l2_title)

        l2_grid = QGridLayout()
        l2_grid.setSpacing(1)
        l2_grid.setHorizontalSpacing(1)
        l2_grid.setVerticalSpacing(1)
        self.l2_blocks = {}

        for row, set_idx in enumerate([0, 4, 8, 12]):
            set_label = QLabel(f"S{set_idx}")
            set_label.setStyleSheet("color: #aaaaaa; font-size: 9pt;")
            set_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            set_label.setFixedWidth(20)
            l2_grid.addWidget(set_label, row, 0)

            for way in range(4):
                block = QFrame()
                block.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
                block.setFixedSize(75, 20)  # Set to 75px width
                block.setStyleSheet("""
                    QFrame {
                        background-color: #1e1e1e;
                        border: 1px solid #9370db;
                        border-radius: 2px;
                    }
                """)

                layout = QHBoxLayout(block)
                layout.setContentsMargins(2, 1, 2, 1)  # Minimal margins
                layout.setSpacing(0)

                value_label = QLabel("Empty")
                value_label.setStyleSheet("color: #666666; font-size: 9pt;")
                value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(value_label)

                self.l2_blocks[f"{set_idx}_{way}"] = value_label
                l2_grid.addWidget(block, row, way + 1)

        l2_layout.addLayout(l2_grid)
        cache_layout.addWidget(l2_widget)

        main_layout.addWidget(cache_container)

        # Flow visualization layer
        self.flow_layer = QWidget(frame)
        self.flow_layer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.flow_layer.setStyleSheet("background: transparent;")
        self.flow_lines = []

        return frame

    def create_controls(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        frame.setFixedHeight(40)  # Set fixed compact height

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(4, 2, 4, 2)  # Minimal margins
        layout.setSpacing(8)  # Spacing between controls

        # Control buttons with compact styling
        button_style = """
            QPushButton {
                background-color: #2b2b2b;
                color: #00ff00;
                border: 1px solid #00ff00;
                border-radius: 2px;
                padding: 4px 12px;
                font-size: 10pt;
                min-width: 60px;
                max-height: 24px;
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

        # Add small spacer
        layout.addSpacing(8)

        # Speed control with compact layout
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("QLabel { color: #00ff00; font-size: 10pt; }")
        speed_label.setFixedWidth(45)
        layout.addWidget(speed_label)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(100)
        self.speed_slider.setMaximum(2000)
        self.speed_slider.setValue(1000)
        self.speed_slider.valueChanged.connect(self.update_speed)
        self.speed_slider.setFixedWidth(200)  # Limit slider width
        self.speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #00ff00;
                height: 4px;
                background: #2b2b2b;
                margin: 1px 0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #00ff00;
                border: 1px solid #00ff00;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.speed_slider)

        # Add stretch to push everything to the left
        layout.addStretch()

        # Add Show Used Memory button
        show_memory_button = QPushButton("Show Used Memory")
        show_memory_button.clicked.connect(self.show_used_memory)
        layout.addWidget(show_memory_button)

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

        # Update L1 Cache blocks
        used_sets = [0, 4, 8, 12]
        for set_idx in used_sets:
            for block_idx in range(2):  # 2-way associative
                block_key = f"{set_idx}_{block_idx}"
                if block_key in self.l1_blocks:
                    value_label = self.l1_blocks[block_key]
                    if (set_idx, block_idx) in l1_info:
                        tag, value = l1_info[(set_idx, block_idx)]
                        display_text = f"T:{tag} V:{value}"
                        value_label.setText(display_text)
                        value_label.setStyleSheet("QLabel { color: #ff69b4; font-weight: bold; }")
                    else:
                        value_label.setText("Empty")
                        value_label.setStyleSheet("QLabel { color: #666666; }")

        # Update L2 Cache blocks
        used_sets_l2 = [0, 4, 8, 12]
        for set_idx in used_sets_l2:
            for block_idx in range(4):  # 4-way associative
                block_key = f"{set_idx}_{block_idx}"
                if block_key in self.l2_blocks:
                    value_label = self.l2_blocks[block_key]
                    if (set_idx, block_idx) in l2_info:
                        tag, value = l2_info[(set_idx, block_idx)]
                        display_text = f"T:{tag} V:{value}"
                        value_label.setText(display_text)
                        value_label.setStyleSheet("QLabel { color: #9370db; font-weight: bold; }")
                    else:
                        value_label.setText("Empty")
                        value_label.setStyleSheet("QLabel { color: #666666; }")

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

        # Update flow visualization
        self._update_flow_visualization()

        # Update memory window if it exists
        self.update_memory_display()

        # Force immediate update
        self.repaint()
        QApplication.processEvents()

    def _highlight_component(self, widget, color, duration=500):
        """Highlight a component with a glowing effect"""
        original_style = widget.styleSheet()
        glow_style = original_style + f"""
            QFrame {{
                border: 2px solid {color};
                box-shadow: 0 0 10px {color};
            }}
        """
        widget.setStyleSheet(glow_style)
        QTimer.singleShot(duration, lambda: widget.setStyleSheet(original_style))

    def _create_flow_animation(self, source_pos, dest_pos, color="#00ff00"):
        """Create an animated flow line between two points"""
        flow = FlowLine(self.flow_layer)
        flow.set_points(source_pos, dest_pos)
        flow.set_active(True)

        # Create fade-out animation
        fade = QPropertyAnimation(flow, b"opacity")
        fade.setDuration(1000)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.Type.OutQuad)
        fade.finished.connect(lambda: self.flow_lines.remove(flow))

        self.flow_lines.append(flow)
        fade.start()

    def _update_flow_visualization(self):
        """Update the flow visualization based on current operation"""
        if not hasattr(self, 'current_instruction') or self.current_instruction >= len(self.instructions):
            return

        instruction = self.instructions[self.current_instruction]
        parts = instruction.split()

        if len(parts) < 2:
            return

        op = parts[0]
        source = parts[1]
        dest = parts[2] if len(parts) > 2 else None

        # Find affected components
        source_widget = None
        dest_widget = None
        intermediate_widgets = []

        if source in self.register_labels:
            source_widget = self.register_labels[source]
        elif source.startswith("["):
            addr = int(source.strip("[]"))
            set_idx = (addr // 4) * 4
            if set_idx in [0, 4, 8, 12]:
                # Check L1 cache first
                for way in range(2):
                    key = f"{set_idx}_{way}"
                    if key in self.l1_blocks:
                        source_widget = self.l1_blocks[key]
                        break

                # If not in L1, check L2
                if not source_widget:
                    for way in range(4):
                        key = f"{set_idx}_{way}"
                        if key in self.l2_blocks:
                            source_widget = self.l2_blocks[key]
                            intermediate_widgets.append(self.l1_blocks[f"{set_idx}_0"])
                            break

        if dest:
            if dest in self.register_labels:
                dest_widget = self.register_labels[dest]
            elif dest.startswith("["):
                addr = int(dest.strip("[]"))
                set_idx = (addr // 4) * 4
                if set_idx in [0, 4, 8, 12]:
                    dest_widget = self.l1_blocks[f"{set_idx}_0"]
                    # For writes, we need to update L2 as well
                    intermediate_widgets.append(self.l2_blocks[f"{set_idx}_0"])

        # Create flow visualizations
        if source_widget and dest_widget:
            # Highlight source
            self._highlight_component(source_widget, "#00ff00")

            # Create flow animations
            prev_widget = source_widget
            for widget in intermediate_widgets + [dest_widget]:
                source_pos = prev_widget.mapTo(self.flow_layer,
                    QPoint(prev_widget.width()//2, prev_widget.height()//2))
                dest_pos = widget.mapTo(self.flow_layer,
                    QPoint(widget.width()//2, widget.height()//2))
                self._create_flow_animation(source_pos, dest_pos)
                self._highlight_component(widget, "#ff69b4")
                prev_widget = widget

    def show_used_memory(self):
        if self.memory_window is None:
            self.memory_window = QWidget(None)  # Create as independent window
            self.memory_window.setWindowTitle("Memory Block Details")
            self.memory_window.setMinimumWidth(400)  # Increased width for more info

            layout = QVBoxLayout()

            # Add description
            description = QLabel("Memory blocks and their cache references:")
            description.setFont(QFont("Courier", 10))
            layout.addWidget(description)

            # Create a grid for memory blocks
            self.memory_grid = QGridLayout()
            self.memory_grid.setSpacing(4)  # Add some spacing between blocks
            layout.addLayout(self.memory_grid)

            self.memory_window.setLayout(layout)

            # Update the memory display initially
            self.update_memory_display()

            # Show the window
            self.memory_window.show()
        else:
            # If window exists, just show it
            self.memory_window.show()
            self.memory_window.raise_()

    def update_memory_display(self):
        """Update the memory display window with just address and value"""
        if self.memory_window is None or not self.memory_window.isVisible():
            return

        # Clear existing widgets from grid
        while self.memory_grid.count():
            item = self.memory_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add memory blocks to grid
        sorted_blocks = sorted(self.used_memory_blocks)
        for i, addr in enumerate(sorted_blocks):
            row = i // 3  # 3 columns for wider blocks
            col = i % 3

            # Create frame for each memory block
            block_frame = QFrame()
            block_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
            block_frame.setStyleSheet("""
                QFrame {
                    background-color: #1e1e1e;
                    border: 1px solid #666666;
                    border-radius: 2px;
                }
            """)

            block_layout = QVBoxLayout()
            block_layout.setSpacing(2)
            block_layout.setContentsMargins(4, 4, 4, 4)

            # Add address header
            addr_label = QLabel(f"Address [{addr}]")
            addr_label.setFont(QFont("Courier", 9, QFont.Weight.Bold))
            addr_label.setStyleSheet("color: #00ff00;")
            addr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            block_layout.addWidget(addr_label)

            # Add memory value
            value = self.main_memory.read(addr)
            value_label = QLabel(f"Value: {value}")
            value_label.setFont(QFont("Courier", 9))
            value_label.setStyleSheet("color: #ffffff;")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            block_layout.addWidget(value_label)

            block_frame.setLayout(block_layout)
            self.memory_grid.addWidget(block_frame, row, col)

        # Update window title and description
        self.memory_window.setWindowTitle("Memory Values")

        # Force layout update
        self.memory_window.adjustSize()

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
