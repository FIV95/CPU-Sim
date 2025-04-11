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
class LogOperation:
    """Base class for all loggable operations"""
    op_type: str
    description: str
    data: Optional[Dict] = None
    timestamp: float = field(default_factory=time)

@dataclass
class CacheOperation:
    """Cache-specific operation details"""
    op_type: str
    description: str
    cache_name: str
    hit: bool
    data: Optional[Dict] = None
    timestamp: float = field(default_factory=time)

@dataclass
class AlgorithmStep:
    """Algorithm-specific step details"""
    op_type: str
    description: str
    step_name: str
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

        self._operations: List[LogOperation] = []
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
        """Get color for cache name"""
        return Fore.BLUE if cache_name == "L2Cache" else Fore.CYAN

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
            LogOperation(level.name.lower(), message, data)
        )

    # Cache logging methods
    def log_cache_operation(self, cache_name: str, op_type: str, hit: bool, data: Any = None):
        """Log cache operations (read/write)"""
        # Update stats
        self._init_cache_stats(cache_name)
        stats = self._cache_stats[cache_name]
        if op_type == "read":
            stats["reads"] += 1
            if hit:
                stats["read_hits"] += 1
            else:
                stats["read_misses"] += 1
        else:  # write
            stats["writes"] += 1
            if hit:
                stats["write_hits"] += 1
            else:
                stats["write_misses"] += 1

        # Track transition
        self._track_cache_transition(cache_name, op_type, hit)

        # Log operation
        if self.should_log(LogLevel.DEBUG):
            cache_color = self._get_cache_color(cache_name)
            status = f"{Fore.GREEN}HIT" if hit else f"{Fore.RED}MISS"
            data_str = f" - Data: {data}" if data is not None else ""
            print(f"{cache_color}[{cache_name}]{Style.RESET_ALL} {op_type.upper()}: {status}{data_str}")

        # Store operation
        self._operations.append(
            CacheOperation(
                op_type=op_type,
                description=f"{cache_name} {op_type}",
                data={"hit": hit, "data": data} if data else {"hit": hit},
                cache_name=cache_name,
                hit=hit
            )
        )
        self._operation_timestamps.append(time())

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
            LogOperation("register", op_type, details)
        )

    def log_memory_operation(self, op_type: str, details: Dict[str, Any]):
        """Log memory operations"""
        if self.should_log(LogLevel.DEBUG):
            print(f"\n{Fore.BLUE}=== Memory {op_type} ==={Style.RESET_ALL}")
            for key, value in details.items():
                print(f"{key}: {value}")
        self._operations.append(
            LogOperation("memory", op_type, details)
        )

    def log_instruction(self, instruction: str, details: Dict[str, Any] = None):
        """Log instruction execution"""
        if self.should_log(LogLevel.DEBUG):
            print(f"\n{Fore.MAGENTA}Executing:{Style.RESET_ALL} {instruction}")
            if details:
                for key, value in details.items():
                    print(f"  {key}: {value}")
        self._operations.append(
            LogOperation("instruction", instruction, details)
        )

    def log_jump(self, target: str, condition: str, details: Dict[str, Any]):
        """Log jump operations"""
        if self.should_log(LogLevel.DEBUG):
            print(f"\n{Fore.YELLOW}=== Jump Operation ==={Style.RESET_ALL}")
            print(f"Target: {target}")
            print(f"Condition: {condition}")
            for key, value in details.items():
                print(f"{key}: {value}")
        self._operations.append(
            LogOperation("jump", f"Jump to {target}", details)
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
                op_type="algorithm",
                description=description,
                data=details,
                step_name=step_type
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
            LogOperation("error", error_type,
                     {"message": message, **details} if details else {"message": message})
        )

    def log_performance(self, metrics: Dict[str, Any]):
        """Log performance metrics"""
        if self.should_log(LogLevel.INFO):
            print(f"\n{Fore.BLUE}=== Performance Metrics ==={Style.RESET_ALL}")
            for key, value in metrics.items():
                print(f"{key}: {value}")
        self._operations.append(
            LogOperation("performance", "Performance metrics", metrics)
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
