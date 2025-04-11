from typing import Dict, List
from dataclasses import dataclass, field
from time import time
from colorama import init, Fore, Back, Style

# Initialize colorama
init()

@dataclass
class CacheOperation:
    cache_name: str
    operation: str
    hit: bool
    data: str = None
    timestamp: float = field(default_factory=time)

class CacheLogger:
    def __init__(self):
        self._operations: List[CacheOperation] = []
        self._stats: Dict[str, Dict[str, int]] = {}
        self._verbose = True  # Set to False to suppress detailed operation logs
        self._operation_timestamps = []
        self._cache_transitions = []

    # Accessors
    @property
    def operations(self) -> List[CacheOperation]:
        return self._operations

    @property
    def stats(self) -> Dict[str, Dict[str, int]]:
        return self._stats

    @property
    def verbose(self) -> bool:
        return self._verbose

    # Mutators
    @operations.setter
    def operations(self, value: List[CacheOperation]):
        if isinstance(value, list):
            self._operations = value
        else:
            raise ValueError("Operations must be a list")

    @stats.setter
    def stats(self, value: Dict[str, Dict[str, int]]):
        if isinstance(value, dict):
            self._stats = value
        else:
            raise ValueError("Stats must be a dictionary")

    @verbose.setter
    def verbose(self, value: bool):
        if isinstance(value, bool):
            self._verbose = value
        else:
            raise ValueError("Verbose must be a boolean")

    def _get_cache_color(self, cache_name):
        """Get the appropriate color for a cache name"""
        return Fore.BLUE if cache_name == "L2Cache" else Fore.CYAN

    def _init_stats(self, cache_name):
        """Initialize stats for a cache if not already initialized"""
        if cache_name not in self._stats:
            self._stats[cache_name] = {
                "reads": 0,
                "read_hits": 0,
                "read_misses": 0,
                "writes": 0,
                "write_hits": 0,
                "write_misses": 0
            }

    def _track_cache_transition(self, cache_name, operation, hit):
        """Track transitions between cache levels"""
        if len(self._operations) > 0:
            last_op = self._operations[-1]
            if last_op.cache_name != cache_name:
                self._cache_transitions.append({
                    "from_cache": last_op.cache_name,
                    "to_cache": cache_name,
                    "operation": operation,
                    "timestamp": time()
                })

    def log_cache_write(self, cache_name, hit, data=None):
        """Log cache write operation"""
        op = CacheOperation(cache_name, "write", hit, data)
        self._operations.append(op)
        self._operation_timestamps.append(time())
        self._track_cache_transition(cache_name, "write", hit)

        # Update stats
        self._init_stats(cache_name)
        self._stats[cache_name]["writes"] += 1
        if hit:
            self._stats[cache_name]["write_hits"] += 1
        else:
            self._stats[cache_name]["write_misses"] += 1

        # Print operation details if verbose
        if self._verbose:
            cache_color = self._get_cache_color(cache_name)
            if hit:
                print(f"{cache_color}[{cache_name}]{Style.RESET_ALL} {Fore.GREEN}Write: HIT{Style.RESET_ALL}")
            else:
                print(f"{cache_color}[{cache_name}]{Style.RESET_ALL} {Fore.RED}Write: MISS{Style.RESET_ALL} - Data: {Fore.YELLOW}{data}{Style.RESET_ALL}")

    def log_cache_read(self, cache_name, hit, data=None):
        """Log cache read operation"""
        op = CacheOperation(cache_name, "read", hit, data)
        self._operations.append(op)
        self._operation_timestamps.append(time())
        self._track_cache_transition(cache_name, "read", hit)

        # Update stats
        self._init_stats(cache_name)
        self._stats[cache_name]["reads"] += 1
        if hit:
            self._stats[cache_name]["read_hits"] += 1
        else:
            self._stats[cache_name]["read_misses"] += 1

        # Print operation details if verbose
        if self._verbose:
            cache_color = self._get_cache_color(cache_name)
            if hit:
                print(f"{cache_color}[{cache_name}]{Style.RESET_ALL} {Fore.GREEN}Read: HIT{Style.RESET_ALL} - Data: {Fore.YELLOW}{data}{Style.RESET_ALL}")
            else:
                print(f"{cache_color}[{cache_name}]{Style.RESET_ALL} {Fore.RED}Read: MISS{Style.RESET_ALL}")

    def log_instruction(self, instruction):
        """Log instruction being executed"""
        if self._verbose:
            print(f"\n{Fore.MAGENTA}Executing:{Style.RESET_ALL} {Fore.WHITE}{instruction}{Style.RESET_ALL}")

    def log_result(self, output_string, exec_time):
        """Log final results with statistics"""
        # Print cache operation summary
        print(f"\n{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}CACHE OPERATIONS SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")

        # Print detailed operation log
        print(f"\n{Fore.CYAN}OPERATION SEQUENCE:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")
        for op in self._operations:
            hit_str = f"{Fore.GREEN}HIT{Style.RESET_ALL}" if op.hit else f"{Fore.RED}MISS{Style.RESET_ALL}"
            data_str = f" - Data: {Fore.YELLOW}{op.data}{Style.RESET_ALL}" if op.data is not None else ""
            cache_color = self._get_cache_color(op.cache_name)
            print(f"{Fore.WHITE}[{op.timestamp:.6f}]{Style.RESET_ALL} {cache_color}[{op.cache_name}]{Style.RESET_ALL} {op.operation.upper()}: {hit_str}{data_str}")

        # Print statistics
        print(f"\n{Fore.CYAN}CACHE STATISTICS:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")
        for cache_name, stats in self._stats.items():
            cache_color = self._get_cache_color(cache_name)
            print(f"\n{cache_color}{cache_name}:{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}{'-' * 20}{Style.RESET_ALL}")

            # Read stats
            total_reads = stats["reads"]
            hits = stats["read_hits"]
            misses = stats["read_misses"]
            hit_rate = (hits / total_reads * 100) if total_reads > 0 else 0
            print(f"  {Fore.WHITE}Reads:{Style.RESET_ALL}")
            print(f"    Total: {Fore.YELLOW}{total_reads}{Style.RESET_ALL}")
            print(f"    Hits: {Fore.GREEN}{hits}{Style.RESET_ALL}")
            print(f"    Misses: {Fore.RED}{misses}{Style.RESET_ALL}")
            print(f"    Hit Rate: {Fore.CYAN}{hit_rate:.1f}%{Style.RESET_ALL}")

            # Write stats
            total_writes = stats["writes"]
            hits = stats["write_hits"]
            misses = stats["write_misses"]
            hit_rate = (hits / total_writes * 100) if total_writes > 0 else 0
            print(f"  {Fore.WHITE}Writes:{Style.RESET_ALL}")
            print(f"    Total: {Fore.YELLOW}{total_writes}{Style.RESET_ALL}")
            print(f"    Hits: {Fore.GREEN}{hits}{Style.RESET_ALL}")
            print(f"    Misses: {Fore.RED}{misses}{Style.RESET_ALL}")
            print(f"    Hit Rate: {Fore.CYAN}{hit_rate:.1f}%{Style.RESET_ALL}")

        # Print final output
        print(f"\n{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}FINAL RESULTS{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
        print(f"Output String: {Fore.GREEN}{output_string}{Style.RESET_ALL}")
        print(f"Execution Time: {Fore.YELLOW}{exec_time:.2f}{Style.RESET_ALL} nanoseconds")

    def debug_info(self):
        """Return detailed debug information about the logger state"""
        info = {
            "verbose": self._verbose,
            "total_operations": len(self._operations),
            "stats": self._stats,
            "caches": list(self._stats.keys())
        }
        return info

    def print_debug_info(self):
        """Print formatted debug information about the logger state"""
        info = self.debug_info()
        print(f"\n{Fore.CYAN}=== Cache Logger Debug Info ==={Style.RESET_ALL}")
        print(f"Verbose Mode: {'Enabled' if info['verbose'] else 'Disabled'}")
        print(f"Total Operations: {info['total_operations']}")
        print(f"Monitored Caches: {', '.join(info['caches'])}")

        print("\nCache Statistics:")
        for cache_name, stats in info['stats'].items():
            cache_color = self._get_cache_color(cache_name)
            print(f"\n{cache_color}{cache_name}:{Style.RESET_ALL}")
            print(f"  Reads: {stats['reads']} (Hits: {stats['read_hits']}, Misses: {stats['read_misses']})")
            print(f"  Writes: {stats['writes']} (Hits: {stats['write_hits']}, Misses: {stats['write_misses']})")

    def validate_state(self):
        """Validate the logger state and return any issues found"""
        issues = []

        # Check operations list
        if not isinstance(self._operations, list):
            issues.append("Operations is not a list")

        # Check stats dictionary
        if not isinstance(self._stats, dict):
            issues.append("Stats is not a dictionary")
        else:
            # Check each cache's stats
            for cache_name, stats in self._stats.items():
                required_stats = ["reads", "read_hits", "read_misses", "writes", "write_hits", "write_misses"]
                for stat in required_stats:
                    if stat not in stats:
                        issues.append(f"Missing stat '{stat}' for cache {cache_name}")
                    elif not isinstance(stats[stat], int):
                        issues.append(f"Invalid stat type for '{stat}' in cache {cache_name}")
                    elif stats[stat] < 0:
                        issues.append(f"Negative value for stat '{stat}' in cache {cache_name}")

        return issues

    def get_operation_stats(self):
        """Return detailed statistics about logged operations"""
        stats = {
            "total_operations": len(self._operations),
            "operation_types": {
                "reads": sum(1 for op in self._operations if op.operation == "read"),
                "writes": sum(1 for op in self._operations if op.operation == "write")
            },
            "hit_rates": {}
        }

        # Calculate hit rates for each cache
        for cache_name, cache_stats in self._stats.items():
            read_hit_rate = (cache_stats["read_hits"] / cache_stats["reads"] * 100) if cache_stats["reads"] > 0 else 0
            write_hit_rate = (cache_stats["write_hits"] / cache_stats["writes"] * 100) if cache_stats["writes"] > 0 else 0
            stats["hit_rates"][cache_name] = {
                "read_hit_rate": read_hit_rate,
                "write_hit_rate": write_hit_rate
            }

        return stats

    def get_operation_timeline(self):
        """Return a timeline of operations with timestamps"""
        timeline = []
        for op in self._operations:
            timeline.append({
                "timestamp": op.timestamp,
                "cache": op.cache_name,
                "operation": op.operation,
                "hit": op.hit,
                "data": op.data
            })
        return sorted(timeline, key=lambda x: x["timestamp"])

    def get_cache_transitions(self):
        """Return information about transitions between cache levels"""
        return self._cache_transitions

    def get_operation_intervals(self):
        """Calculate time intervals between operations"""
        intervals = []
        for i in range(1, len(self._operation_timestamps)):
            intervals.append({
                "interval": self._operation_timestamps[i] - self._operation_timestamps[i-1],
                "from_operation": self._operations[i-1],
                "to_operation": self._operations[i]
            })
        return intervals

    def get_performance_metrics(self):
        """Return detailed performance metrics"""
        metrics = {
            "total_operations": len(self._operations),
            "operation_timing": {
                "min_interval": min((t2 - t1) for t1, t2 in zip(self._operation_timestamps[:-1], self._operation_timestamps[1:])) if len(self._operation_timestamps) > 1 else 0,
                "max_interval": max((t2 - t1) for t1, t2 in zip(self._operation_timestamps[:-1], self._operation_timestamps[1:])) if len(self._operation_timestamps) > 1 else 0,
                "average_interval": sum((t2 - t1) for t1, t2 in zip(self._operation_timestamps[:-1], self._operation_timestamps[1:])) / (len(self._operation_timestamps) - 1) if len(self._operation_timestamps) > 1 else 0
            },
            "cache_transitions": len(self._cache_transitions),
            "hit_rates": {}
        }

        # Calculate hit rates for each cache
        for cache_name, stats in self._stats.items():
            total_ops = stats["reads"] + stats["writes"]
            total_hits = stats["read_hits"] + stats["write_hits"]
            metrics["hit_rates"][cache_name] = {
                "overall": (total_hits / total_ops * 100) if total_ops > 0 else 0,
                "reads": (stats["read_hits"] / stats["reads"] * 100) if stats["reads"] > 0 else 0,
                "writes": (stats["write_hits"] / stats["writes"] * 100) if stats["writes"] > 0 else 0
            }

        return metrics
