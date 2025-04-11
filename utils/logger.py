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
    op_type: str
    description: str
    data: Optional[Dict] = None
    timestamp: float = field(default_factory=time)

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
    step_name: str
    op_type: str
    description: str
    success: bool = True
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
        self._log_level = LogLevel.INFO
        self._operation_timestamps = []
        self._cache_transitions = []
        self._initialized = True

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
        colors = {
            "L1Cache": Fore.GREEN,
            "L2Cache": Fore.BLUE,
            "L3Cache": Fore.MAGENTA
        }
        return colors.get(cache_name, Fore.WHITE)

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
        """Log cache operations"""
        if self.should_log(LogLevel.DEBUG):
            cache_color = self._get_cache_color(cache_name)
            status = f"{Fore.GREEN}HIT" if hit else f"{Fore.RED}MISS"
            print(f"{cache_color}[{cache_name}]{Style.RESET_ALL} {op_type}: {status}{Style.RESET_ALL}")
            if details is not None:
                if isinstance(details, dict):
                    for key, value in details.items():
                        print(f"  {key}: {value}")
                else:
                    print(f" - Data: {details}")

        # Convert non-dict details to dict format
        details_dict = details if isinstance(details, dict) else {"data": details} if details is not None else None

        self._operations.append(
            CacheOperation(
                cache_name=cache_name,
                op_type=op_type,
                description=f"{cache_name} {op_type}",
                hit=hit,
                data=details_dict
            )
        )

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
        """Log register operations"""
        if self.should_log(LogLevel.DEBUG):
            print(f"\n{Fore.MAGENTA}=== Register {op_type} ==={Style.RESET_ALL}")
            for key, value in details.items():
                print(f"{key}: {value}")
        self._operations.append(
            Operation("register", op_type, details)
        )

    def log_memory_operation(self, op_type: str, details: Dict[str, Any]):
        """Log memory operations"""
        if self.should_log(LogLevel.DEBUG):
            print(f"\n{Fore.BLUE}=== Memory {op_type} ==={Style.RESET_ALL}")
            for key, value in details.items():
                print(f"{key}: {value}")
        self._operations.append(
            Operation("memory", op_type, details)
        )

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
    def log_algorithm_step(self, step_type: str, description: str, details: Dict[str, Any] = None):
        """Log an algorithm step"""
        if self.should_log(LogLevel.INFO):
            print(f"\n{Fore.CYAN}{step_type}:{Style.RESET_ALL} {description}")
            if details:
                for key, value in details.items():
                    print(f"  {key}: {value}")
        self._operations.append(
            AlgorithmStep(
                step_name=step_type,
                op_type="algorithm",
                description=description,
                data=details
            )
        )

    def log_array_state(self, array: List, prefix: str = ""):
        """Log the current state of an array"""
        if self.should_log(LogLevel.INFO):
            print(f"\n{Fore.CYAN}{prefix}:{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'-' * 40}{Style.RESET_ALL}")
            for i, value in enumerate(array):
                print(f"[{i}] = {value}")
            print(f"{Fore.CYAN}{'-' * 40}{Style.RESET_ALL}")
        self._operations.append(
            AlgorithmStep(
                op_type="array_state",
                description=prefix,
                data={"array": array},
                step_name="array_display"
            )
        )

    def log_comparison(self, index1: int, value1: Any, index2: int, value2: Any):
        """Log a comparison between two array elements"""
        if self.should_log(LogLevel.DEBUG):
            print(f"\n{Fore.YELLOW}Comparing elements:{Style.RESET_ALL}")
            print(f"[{index1}] = {value1}  vs  [{index2}] = {value2}")
        self._operations.append(
            AlgorithmStep(
                op_type="comparison",
                description=f"Compare [{index1}]={value1} with [{index2}]={value2}",
                data={"index1": index1, "value1": value1,
                      "index2": index2, "value2": value2},
                step_name="comparison"
            )
        )

    def log_swap(self, index1: int, value1: Any, index2: int, value2: Any):
        """Log a swap operation between two array elements"""
        if self.should_log(LogLevel.INFO):
            print(f"\n{Fore.GREEN}>>> SWAP <<<{Style.RESET_ALL}")
            print(f"[{index1}] = {value1}  <->  [{index2}] = {value2}")
        self._operations.append(
            AlgorithmStep(
                op_type="swap",
                description=f"Swap [{index1}]={value1} with [{index2}]={value2}",
                data={"index1": index1, "value1": value1,
                      "index2": index2, "value2": value2},
                step_name="swap"
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
            op_type = op.op_type
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
    def log_cache_transitions(self, cache_name: str, stats: Dict[str, Any]):
        """Log cache transition statistics"""
        if not self.should_log(LogLevel.INFO):
            return

        print(f"\n=== Cache Transition Stats: {cache_name} ===")
        print(f"Total Operations: {stats['total_ops']}")
        print(f"Upward Transitions: {stats['upward_transitions']}")
        print(f"Downward Transitions: {stats['downward_transitions']}")
        print(f"Upward Transition Rate: {(stats['upward_transitions']/stats['total_ops']*100 if stats['total_ops'] > 0 else 0):.2f}%")
        print(f"Downward Transition Rate: {(stats['downward_transitions']/stats['total_ops']*100 if stats['total_ops'] > 0 else 0):.2f}%")

        self._operations.append(
            Operation("cache_transitions", f"Cache transitions for {cache_name}", stats)
        )

    def log_cache_state_issues(self, cache_name: str, issues: List[str]):
        """Log cache state issues"""
        if not self.should_log(LogLevel.WARNING):
            return

        print(f"\n=== {cache_name} State Issues ===")
        for issue in issues:
            print(f"- {issue}")

        self._operations.append(
            Operation("cache_state_issues", f"State issues for {cache_name}", {"issues": issues})
        )

    def log_cache_entry_stats(self, cache_name: str, stats: Dict[str, int]):
        """Log cache entry statistics"""
        if not self.should_log(LogLevel.INFO):
            return

        print(f"\n=== {cache_name} Entry Stats ===")
        print(f"Total entries: {stats['total_entries']}")
        print(f"Dirty entries: {stats['dirty_entries']}")
        print(f"Clean entries: {stats['clean_entries']}")

        self._operations.append(
            Operation("cache_entry_stats", f"Entry stats for {cache_name}", stats)
        )

    def log_cache_access_patterns(self, cache_name: str, patterns: Dict[str, Any]):
        """Log cache access patterns"""
        if not self.should_log(LogLevel.INFO):
            return

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
