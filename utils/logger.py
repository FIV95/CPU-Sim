from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from time import time
from enum import Enum
from colorama import init, Fore, Back, Style

# Initialize colorama
init()

class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4

@dataclass
class Operation:
    """Base class for all loggable operations"""
    type: str  # Unified field for operation type
    description: str
    data: Optional[Dict] = None
    timestamp: float = field(default_factory=time)
    category: str = "general"  # To categorize different types of operations

@dataclass
class CacheOperation:
    """Cache-specific operation details"""
    cache_name: str
    op_type: str
    description: str
    hit: bool = False
    data: Optional[Dict] = None
    timestamp: float = field(default_factory=time)

@dataclass
class AlgorithmStep:
    """Algorithm-specific step details"""
    step_type: str
    description: str
    data: Optional[Dict] = None
    timestamp: float = field(default_factory=time)

class Logger:
    """Unified logging system for the entire application"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._operations: List[Operation] = []
        self._cache_stats: Dict[str, Dict[str, int]] = {}
        self.log_level = LogLevel.INFO
        self._operation_timestamps = []
        self._cache_transitions = []
        self._initialized = True

        # Enhanced color scheme for memory hierarchy
        self._cache_colors = {
            'L1Cache': Fore.CYAN,      # Bright cyan for L1
            'L2Cache': Fore.MAGENTA,   # Magenta for L2
            'MainMemory': Fore.GREEN,  # Green for main memory
            'Register': Fore.YELLOW,   # Yellow for registers
            'DataFlow': Fore.WHITE     # White for data flow indicators
        }

        # Symbols for data flow
        self._flow_symbols = {
            'read': '↓',
            'write': '↑',
            'hit': '✓',
            'miss': '✗',
            'through': '↕'
        }

    @property
    def log_level(self) -> LogLevel:
        return self._log_level

    @log_level.setter
    def log_level(self, value: LogLevel):
        if isinstance(value, LogLevel):
            self._log_level = value
        else:
            raise ValueError("Log level must be a LogLevel enum")

    def should_log(self, level: LogLevel) -> bool:
        """Check if message at given level should be logged"""
        return level.value >= self._log_level.value

    def _get_level_color(self, level: LogLevel) -> str:
        """Get color for log level"""
        colors = {
            LogLevel.DEBUG: Fore.CYAN,
            LogLevel.INFO: Fore.WHITE,
            LogLevel.WARNING: Fore.YELLOW,
            LogLevel.ERROR: Fore.RED
        }
        return colors.get(level, Fore.WHITE)

    def _get_cache_color(self, cache_name: str) -> str:
        """Get color for cache level"""
        return self._cache_colors.get(cache_name, Fore.WHITE)

    def _init_cache_stats(self, cache_name: str):
        """Initialize stats for a cache if not already initialized"""
        if cache_name not in self._cache_stats:
            self._cache_stats[cache_name] = {
                "reads": 0,
                "read_hits": 0,
                "read_misses": 0,
                "writes": 0,
                "write_hits": 0,
                "write_misses": 0
            }

    def _track_cache_transition(self, cache_name: str, operation: str, hit: bool):
        """Track transitions between cache levels"""
        if len(self._operations) > 0:
            last_op = self._operations[-1]
            if isinstance(last_op, CacheOperation) and last_op.cache_name != cache_name:
                self._cache_transitions.append({
                    "from_cache": last_op.cache_name,
                    "to_cache": cache_name,
                    "operation": operation,
                    "timestamp": time()
                })

    # Core logging methods
    def log(self, level: LogLevel, message: str, data: Dict = None):
        """Core logging method"""
        if self.should_log(level):
            color = self._get_level_color(level)
            print(f"{color}{message}{Style.RESET_ALL}")
        self._operations.append(
            Operation(level.name.lower(), message, data)
        )

    # Cache logging methods
    def log_cache_operation(self, cache_name: str, op_type: str, hit: bool, details: Any = None):
        """Enhanced cache operation logging with data flow visualization"""
        if not self.should_log(LogLevel.INFO):
            return

        # Get appropriate colors
        cache_color = self._get_cache_color(cache_name)
        flow_color = self._cache_colors['DataFlow']

        # Build the operation string
        op_symbol = self._flow_symbols[op_type]
        hit_symbol = self._flow_symbols['hit'] if hit else self._flow_symbols['miss']

        # Format the base message
        message = (
            f"{flow_color}{op_symbol} {cache_color}{cache_name}{Style.RESET_ALL} "
            f"{flow_color}{hit_symbol}{Style.RESET_ALL}"
        )

        # Add details if provided
        if details:
            if isinstance(details, dict):
                for key, value in details.items():
                    message += f" {key}={cache_color}{value}{Style.RESET_ALL}"
            else:
                message += f" {cache_color}{details}{Style.RESET_ALL}"

        print(message)

        # Add human-readable explanation
        explanation = ""
        if op_type == "read":
            if hit:
                explanation = f"✨ Found the value in {cache_name} (cache hit)"
            else:
                explanation = f"🔍 Value not in {cache_name} (cache miss), need to check next level"
        elif op_type == "write":
            if hit:
                explanation = f"✍️  Updated existing value in {cache_name}"
            else:
                explanation = f"📝 Adding new value to {cache_name}"
        elif op_type == "through":
            explanation = f"⚡ Propagating value through {cache_name}"

        if explanation:
            print(f"  {explanation}")

        # Track cache transitions
        self._track_cache_transition(cache_name, op_type, hit)

        # Update cache stats
        self._init_cache_stats(cache_name)
        if hit:
            self._cache_stats[cache_name]["read_hits" if op_type == "read" else "write_hits"] += 1
        else:
            self._cache_stats[cache_name]["read_misses" if op_type == "read" else "write_misses"] += 1
        self._cache_stats[cache_name]["reads" if op_type == "read" else "writes"] += 1

    def log_cache_stats(self, cache_name: str):
        """Log cache statistics"""
        if not self.should_log(LogLevel.INFO):
            return

        stats = self._cache_stats.get(cache_name, {})
        if not stats:
            return

        cache_color = self._get_cache_color(cache_name)
        print(f"\n{cache_color}=== {cache_name} Statistics ==={Style.RESET_ALL}")

        # Read stats
        total_reads = stats["reads"]
        read_hit_rate = (stats["read_hits"] / total_reads * 100) if total_reads > 0 else 0
        print(f"\n{Fore.WHITE}Reads:{Style.RESET_ALL}")
        print(f"  Total: {total_reads}")
        print(f"  Hits: {Fore.GREEN}{stats['read_hits']}{Style.RESET_ALL}")
        print(f"  Misses: {Fore.RED}{stats['read_misses']}{Style.RESET_ALL}")
        print(f"  Hit Rate: {read_hit_rate:.1f}%")

        # Write stats
        total_writes = stats["writes"]
        write_hit_rate = (stats["write_hits"] / total_writes * 100) if total_writes > 0 else 0
        print(f"\n{Fore.WHITE}Writes:{Style.RESET_ALL}")
        print(f"  Total: {total_writes}")
        print(f"  Hits: {Fore.GREEN}{stats['write_hits']}{Style.RESET_ALL}")
        print(f"  Misses: {Fore.RED}{stats['write_misses']}{Style.RESET_ALL}")
        print(f"  Hit Rate: {write_hit_rate:.1f}%")

    # ISA logging methods
    def log_register_operation(self, op_type: str, details: Dict[str, Any]):
        """Enhanced register operation logging with data flow visualization"""
        if not self.should_log(LogLevel.INFO):
            return

        dest = details.get('dest', '')
        value = details.get('value', 0)
        source = details.get('source', '')

        # Get appropriate colors
        reg_color = self._cache_colors['Register']
        flow_color = self._cache_colors['DataFlow']

        # Build the operation string
        op_symbol = self._flow_symbols['write'] if op_type in ['mov', 'load'] else '→'

        # Format the message with colors and symbols
        message = (
            f"{flow_color}{op_symbol} {reg_color}{dest}{Style.RESET_ALL} = "
            f"{reg_color}{value}{Style.RESET_ALL} "
            f"from {reg_color}{source}{Style.RESET_ALL}"
        )

        print(message)

    def log_memory_operation(self, op_type: str, details: Dict[str, Any]):
        """Enhanced memory operation logging with data flow visualization"""
        if not self.should_log(LogLevel.INFO):
            return

        cache_name = details.get('cache_name', 'MainMemory')
        address = details.get('address', 0)
        value = details.get('value', 0)
        hit = details.get('hit', False)

        # Get appropriate colors
        cache_color = self._get_cache_color(cache_name)
        flow_color = self._cache_colors['DataFlow']

        # Build the operation string
        op_symbol = self._flow_symbols[op_type]
        hit_symbol = self._flow_symbols['hit'] if hit else self._flow_symbols['miss']

        # Format the message with colors and symbols
        message = (
            f"{flow_color}{op_symbol} {cache_color}{cache_name}{Style.RESET_ALL} "
            f"at address {Fore.WHITE}[{address}]{Style.RESET_ALL} = "
            f"{cache_color}{value}{Style.RESET_ALL} "
            f"{flow_color}{hit_symbol}{Style.RESET_ALL}"
        )

        print(message)

        # Add human-readable explanation
        if op_type == "read":
            print(f"  📖 Reading value {value} from memory address {address}")
        elif op_type == "write":
            print(f"  📝 Writing value {value} to memory address {address}")

        # Add memory hierarchy explanation
        if cache_name == "MainMemory":
            print("  💾 This operation goes directly to main memory (slowest, but largest storage)")
        elif "L2" in cache_name:
            print("  🔄 Using L2 cache (medium speed, medium size)")
        elif "L1" in cache_name:
            print("  ⚡ Using L1 cache (fastest, but smallest)")

        # Track cache transitions
        self._track_cache_transition(cache_name, op_type, hit)

        # Update cache stats
        self._init_cache_stats(cache_name)
        if hit:
            self._cache_stats[cache_name]["read_hits" if op_type == "read" else "write_hits"] += 1
        else:
            self._cache_stats[cache_name]["read_misses" if op_type == "read" else "write_misses"] += 1
        self._cache_stats[cache_name]["reads" if op_type == "read" else "writes"] += 1

    def log_instruction(self, instruction: str, details: Dict[str, Any] = None):
        """Log instruction execution"""
        if self.should_log(LogLevel.DEBUG):
            print(f"\n{Fore.MAGENTA}Executing:{Style.RESET_ALL} {instruction}")
            if details:
                for key, value in details.items():
                    print(f"  {key}: {value}")
        self._operations.append(
            Operation("instruction", instruction, details)
        )

    def log_jump(self, op_type: str, target: str, details: Dict[str, Any]):
        """Log jump operations"""
        if self.should_log(LogLevel.DEBUG):
            print(f"\n{Fore.YELLOW}=== Jump {op_type} ==={Style.RESET_ALL}")
            print(f"Target: {target}")
            if details:
                for key, value in details.items():
                    print(f"{key}: {value}")
        self._operations.append(
            Operation("jump", f"Jump to {target}", details)
        )

    # Algorithm logging methods
    def log_algorithm_step(self, step_type: str, description: str, data: Optional[Dict] = None):
        """Log algorithm step details"""
        if self.should_log(LogLevel.INFO):
            print(f"\n{Fore.YELLOW}=== {step_type} ==={Style.RESET_ALL}")
            print(f"{description}")
            if data:
                for key, value in data.items():
                    print(f"  {key}: {value}")
        self._operations.append(
            Operation(
                type=step_type,
                description=description,
                data=data,
                category="algorithm"
            )
        )

    def log_array_state(self, array_name: str, elements: List[Any], title: str = "Array State"):
        """Log array state with pretty formatting"""
        if self.should_log(LogLevel.INFO):
            print(f"\n{Fore.CYAN}=== {title} ==={Style.RESET_ALL}")
            print("----------------------------------------")
            for i, elem in enumerate(elements):
                print(f"[{i}] = {elem}")
            print("----------------------------------------")
        self._operations.append(
            Operation(
                type="array_display",
                description=title,
                data={"array": elements},
                category="algorithm"
            )
        )

    def log_comparison(self, pos1: int, pos2: int, val1: Any, val2: Any, result: int):
        """Log array element comparison"""
        if self.should_log(LogLevel.INFO):
            print("\nComparing Elements:")
            print(f"Position {pos1} and {pos2}")
            print(f"Values: {val1} and {val2}")
            print(f"Result: {result}")
        self._operations.append(
            Operation(
                type="comparison",
                description=f"Compare elements at positions {pos1} and {pos2}",
                data={
                    "pos1": pos1,
                    "pos2": pos2,
                    "val1": val1,
                    "val2": val2,
                    "result": result
                },
                category="algorithm"
            )
        )

    def log_swap(self, pos1: int, pos2: int, val1: Any, val2: Any):
        """Log array element swap"""
        if self.should_log(LogLevel.INFO):
            print("\nSwapping Elements:")
            print(f"Position {pos1} and {pos2}")
            print(f"Values: {val1} and {val2}")
        self._operations.append(
            Operation(
                type="swap",
                description=f"Swap elements at positions {pos1} and {pos2}",
                data={
                    "pos1": pos1,
                    "pos2": pos2,
                    "val1": val1,
                    "val2": val2
                },
                category="algorithm"
            )
        )

    # Error and performance logging
    def log_error(self, error_type: str, message: str, details: Dict[str, Any] = None):
        """Log an error"""
        if self.should_log(LogLevel.ERROR):
            print(f"\n{Fore.RED}ERROR - {error_type}: {message}{Style.RESET_ALL}")
            if details:
                for key, value in details.items():
                    print(f"  {key}: {value}")
        self._operations.append(
            Operation("error", error_type,
                     {"message": message, **details} if details else {"message": message})
        )

    def log_performance(self, metrics: Dict[str, Any]):
        """Log performance metrics"""
        if self.should_log(LogLevel.INFO):
            print(f"\n{Fore.BLUE}=== Performance Metrics ==={Style.RESET_ALL}")
            for key, value in metrics.items():
                print(f"{key}: {value}")
        self._operations.append(
            Operation("performance", "Performance metrics", metrics)
        )

    # Analysis and reporting methods
    def get_operation_stats(self):
        """Get statistics about all operations"""
        stats = {
            "total_operations": len(self._operations),
            "operation_types": {},
            "cache_stats": self._cache_stats,
            "transitions": len(self._cache_transitions)
        }

        # Count operation types
        for op in self._operations:
            op_type = op.type
            stats["operation_types"][op_type] = stats["operation_types"].get(op_type, 0) + 1

        return stats

    def get_performance_metrics(self):
        """Get detailed performance metrics"""
        if not self._operation_timestamps:
            return {}

        intervals = [t2 - t1 for t1, t2 in zip(self._operation_timestamps[:-1], self._operation_timestamps[1:])]
        return {
            "total_operations": len(self._operations),
            "total_time": self._operation_timestamps[-1] - self._operation_timestamps[0],
            "min_interval": min(intervals) if intervals else 0,
            "max_interval": max(intervals) if intervals else 0,
            "avg_interval": sum(intervals) / len(intervals) if intervals else 0
        }

    def print_summary(self):
        """Print a summary of all operations"""
        if not self.should_log(LogLevel.INFO):
            return

        print(f"\n{Fore.BLUE}{'='*60}")
        print(f"OPERATION SUMMARY")
        print(f"{'='*60}{Style.RESET_ALL}")

        # Print operation counts
        stats = self.get_operation_stats()
        print(f"\n{Fore.CYAN}Operation Counts:{Style.RESET_ALL}")
        for op_type, count in stats["operation_types"].items():
            print(f"  {op_type}: {count}")

        # Print cache statistics
        print(f"\n{Fore.CYAN}Cache Statistics:{Style.RESET_ALL}")
        for cache_name in self._cache_stats:
            self.log_cache_stats(cache_name)

        # Print performance metrics
        metrics = self.get_performance_metrics()
        print(f"\n{Fore.CYAN}Performance Metrics:{Style.RESET_ALL}")
        for key, value in metrics.items():
            print(f"  {key}: {value}")

    # New methods for cache transitions and stats
    def log_cache_transitions(self, cache_name: str, stats: Dict[str, int]):
        """Log cache transition statistics"""
        if self.should_log(LogLevel.INFO):
            print(f"\n=== Cache Transition Stats: {cache_name} ===")
            print(f"Total Operations: {stats['total_ops']}")
            print(f"Upward Transitions: {stats['upward_transitions']}")
            print(f"Downward Transitions: {stats['downward_transitions']}")
            if stats['total_ops'] > 0:
                upward_rate = (stats['upward_transitions'] / stats['total_ops']) * 100
                downward_rate = (stats['downward_transitions'] / stats['total_ops']) * 100
                print(f"Upward Transition Rate: {upward_rate:.2f}%")
                print(f"Downward Transition Rate: {downward_rate:.2f}%")

        self._operations.append(
            Operation("cache_transitions", f"Cache transitions for {cache_name}", stats)
        )

    def log_cache_issues(self, cache_name: str, issues: List[str]):
        """Log cache state issues"""
        if self.should_log(LogLevel.WARNING):
            print(f"\n=== {cache_name} State Issues ===")
            for issue in issues:
                print(f"- {issue}")

        self._operations.append(
            Operation("cache_state_issues", f"State issues for {cache_name}", {"issues": issues})
        )

    def log_cache_entries(self, cache_name: str, stats: Dict[str, int]):
        """Log cache entry statistics"""
        if self.should_log(LogLevel.INFO):
            print(f"\n=== {cache_name} Entry Stats ===")
            print(f"Total entries: {stats['total_entries']}")
            print(f"Dirty entries: {stats['dirty_entries']}")
            print(f"Clean entries: {stats['clean_entries']}")

        self._operations.append(
            Operation("cache_entry_stats", f"Entry stats for {cache_name}", stats)
        )

    def log_cache_patterns(self, cache_name: str, patterns: Dict[str, float]):
        """Log cache access pattern statistics"""
        if self.should_log(LogLevel.INFO):
            print(f"\n=== {cache_name} Access Patterns ===")
            print(f"Total accesses: {patterns['total_accesses']}")
            print(f"Sequential access rate: {patterns['sequential_rate']:.2f}%")
            print(f"Random access rate: {patterns['random_rate']:.2f}%")
            print(f"Repeated access rate: {patterns['repeated_rate']:.2f}%")

        self._operations.append(
            Operation("cache_access_patterns", f"Access patterns for {cache_name}", patterns)
        )

    # New methods for memory debug info
    def log_memory_debug(self, memory_name: str, info: Dict[str, Any]):
        """Log memory debug information"""
        if not self.should_log(LogLevel.DEBUG):
            return

        print(f"\n{Fore.CYAN}=== Memory Debug Info: {memory_name} ==={Style.RESET_ALL}")
        print(f"Type: {info['type']}")
        print(f"Access Time: {info['access_time']} ns")
        print(f"Execution Time: {info['exec_time']} ns")
        print(f"Bandwidth: {info['bandwidth']} bytes/ns")
        print("\nLatency Statistics:")
        print(f"  Minimum: {info['latency_stats']['min']} ns")
        print(f"  Maximum: {info['latency_stats']['max']} ns")
        print(f"  Average: {info['latency_stats']['total'] / info['latency_stats']['count'] if info['latency_stats']['count'] > 0 else 0} ns")
        print(f"  Total Operations: {info['latency_stats']['count']}")

        self._operations.append(
            Operation("memory_debug", f"Debug info for {memory_name}", info)
        )

    def log_memory_contents(self, memory_name: str, info: Dict[str, Any]):
        """Log memory contents and map"""
        if not self.should_log(LogLevel.DEBUG):
            return

        print(f"\nData Size: {info['data_size']} bytes")
        print("\nData Contents:")
        for addr, value in info['contents'].items():
            print(f"  Address {addr}: {value}")
        print("\nMemory Map:")
        for addr, region in info['map'].items():
            print(f"  Address {addr}: {region}")
        print("\nAccess Pattern:")
        for pattern, count in info['access_pattern'].items():
            print(f"  {pattern}: {count}")

        self._operations.append(
            Operation("memory_contents", f"Contents for {memory_name}", info)
        )

    # New methods for ISA debug info
    def log_isa_debug(self, info: Dict[str, Any]):
        """Log ISA debug information"""
        if not self.should_log(LogLevel.DEBUG):
            return

        print(f"\n{Fore.CYAN}=== ISA Debug Info ==={Style.RESET_ALL}")
        if not info.get('memory'):
            print(f"{Fore.RED}No memory attached{Style.RESET_ALL}")
            return

        print(f"\nAvailable Instructions: {', '.join(info['instructions'].keys())}")
        print(f"Output: {info['output']}")
        print(f"Execution Time: {info['exec_time']} ns")

        print("\nPipeline State:")
        for stage, instruction in info['pipeline'].items():
            print(f"  {stage}: {instruction if instruction else 'Empty'}")

        print("\nBranch Prediction:")
        total_predictions = info['branch_prediction']['correct'] + info['branch_prediction']['incorrect']
        accuracy = (info['branch_prediction']['correct'] / total_predictions * 100) if total_predictions > 0 else 0
        print(f"  Total Predictions: {total_predictions}")
        print(f"  Correct: {info['branch_prediction']['correct']}")
        print(f"  Incorrect: {info['branch_prediction']['incorrect']}")
        print(f"  Accuracy: {accuracy:.2f}%")

        self._operations.append(
            Operation("isa_debug", "ISA debug information", info)
        )

    def log_jump_debug(self, info: Dict[str, Any]):
        """Log jump operation debug information"""
        if not self.should_log(LogLevel.DEBUG):
            return

        print(f"\n=== Jump Debug ===")
        print(f"Jump target: {info['target']}")
        print(f"Jump condition register: {info['condition']}")
        print(f"Current instruction: {info['instruction_pointer']}")
        for reg, value in info['registers'].items():
            print(f"{reg}: {value}")

        self._operations.append(
            Operation("jump_debug", "Jump operation debug", info)
        )

    # New methods for cache debug info
    def log_cache_debug(self, cache_name: str, info: Dict[str, Any]):
        """Log cache debug information"""
        if not self.should_log(LogLevel.DEBUG):
            return

        print(f"\n{Fore.CYAN}=== Cache Debug Info: {cache_name} ==={Style.RESET_ALL}")
        print(f"Size: {info['size']} bytes")
        print(f"Block Size: {info['block_size']} bytes")
        print(f"Policy: {info['policy']}")
        print(f"Access Time: {info['access_time']} ns")
        print(f"Execution Time: {info['exec_time']} ns")
        print(f"Number of Entries: {info['num_entries']}")
        print("\nEntries:")
        for entry in info['entries']:
            print(f"  Address: {entry['address']}, Data: {entry['data']}, Dirty: {entry['dirty']}")
        print(f"\nLRU Order: {info['lru_order']}")
        print(f"Next Level: {info['next_level']}")

        self._operations.append(
            Operation("cache_debug", f"Debug info for {cache_name}", info)
        )

    def log_cache_config(self, cache_name: str, config: Dict[str, Any]):
        """Log cache configuration"""
        if not self.should_log(LogLevel.INFO):
            return

        print(f"\n{Fore.CYAN}=== Cache Level: {cache_name} ==={Style.RESET_ALL}")
        print(f"Configuration:")
        print(f"  Size: {config['size']} bytes")
        print(f"  Block Size: {config['block_size']} bytes")
        print(f"  Associativity: {config['associativity']}")
        print(f"  Write Policy: {config['write_policy']}")
        print(f"  Access Time: {config['access_time']} ns")
        print(f"  Total Execution Time: {config['exec_time']} ns")

        self._operations.append(
            Operation("cache_config", f"Configuration for {cache_name}", config)
        )

    def log_verification(self, pos: Optional[int] = None, val1: Optional[Any] = None, val2: Optional[Any] = None, is_sorted: bool = False):
        """Log array verification result with optional step details"""
        if self.should_log(LogLevel.INFO):
            if pos is not None and val1 is not None and val2 is not None:
                print(f"\nVerifying position {pos}:")
                print(f"Values: {val1} and {val2}")
                print(f"Order is {'correct' if val1 <= val2 else 'incorrect'}")
            else:
                print("\nVerification:")
                print(f"Array is {'sorted' if is_sorted else 'not sorted'}")

        data = {
            "is_sorted": is_sorted
        }
        if pos is not None:
            data.update({
                "position": pos,
                "value1": val1,
                "value2": val2,
                "is_valid": val1 <= val2 if val1 is not None and val2 is not None else None
            })

        self._operations.append(
            Operation(
                type="verification",
                description="Verify array sorting",
                data=data,
                category="algorithm"
            )
        )
