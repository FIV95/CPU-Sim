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
        self.operations: List[CacheOperation] = []
        self.stats: Dict[str, Dict[str, int]] = {}
        self.verbose = True  # Set to False to suppress detailed operation logs

    def _get_cache_color(self, cache_name):
        """Get the appropriate color for a cache name"""
        return Fore.BLUE if cache_name == "L2Cache" else Fore.CYAN

    def _init_stats(self, cache_name):
        """Initialize stats for a cache if not already initialized"""
        if cache_name not in self.stats:
            self.stats[cache_name] = {
                "reads": 0,
                "read_hits": 0,
                "read_misses": 0,
                "writes": 0,
                "write_hits": 0,
                "write_misses": 0
            }

    def log_cache_write(self, cache_name, hit, data=None):
        """Log cache write operation"""
        op = CacheOperation(cache_name, "write", hit, data)
        self.operations.append(op)

        # Update stats
        self._init_stats(cache_name)
        self.stats[cache_name]["writes"] += 1
        if hit:
            self.stats[cache_name]["write_hits"] += 1
        else:
            self.stats[cache_name]["write_misses"] += 1

        # Print operation details if verbose
        if self.verbose:
            cache_color = self._get_cache_color(cache_name)
            if hit:
                print(f"{cache_color}[{cache_name}]{Style.RESET_ALL} {Fore.GREEN}Write: HIT{Style.RESET_ALL}")
            else:
                print(f"{cache_color}[{cache_name}]{Style.RESET_ALL} {Fore.RED}Write: MISS{Style.RESET_ALL} - Data: {Fore.YELLOW}{data}{Style.RESET_ALL}")

    def log_cache_read(self, cache_name, hit, data=None):
        """Log cache read operation"""
        op = CacheOperation(cache_name, "read", hit, data)
        self.operations.append(op)

        # Update stats
        self._init_stats(cache_name)
        self.stats[cache_name]["reads"] += 1
        if hit:
            self.stats[cache_name]["read_hits"] += 1
        else:
            self.stats[cache_name]["read_misses"] += 1

        # Print operation details if verbose
        if self.verbose:
            cache_color = self._get_cache_color(cache_name)
            if hit:
                print(f"{cache_color}[{cache_name}]{Style.RESET_ALL} {Fore.GREEN}Read: HIT{Style.RESET_ALL} - Data: {Fore.YELLOW}{data}{Style.RESET_ALL}")
            else:
                print(f"{cache_color}[{cache_name}]{Style.RESET_ALL} {Fore.RED}Read: MISS{Style.RESET_ALL}")

    def log_instruction(self, instruction):
        """Log instruction being executed"""
        if self.verbose:
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
        for op in self.operations:
            hit_str = f"{Fore.GREEN}HIT{Style.RESET_ALL}" if op.hit else f"{Fore.RED}MISS{Style.RESET_ALL}"
            data_str = f" - Data: {Fore.YELLOW}{op.data}{Style.RESET_ALL}" if op.data is not None else ""
            cache_color = self._get_cache_color(op.cache_name)
            print(f"{Fore.WHITE}[{op.timestamp:.6f}]{Style.RESET_ALL} {cache_color}[{op.cache_name}]{Style.RESET_ALL} {op.operation.upper()}: {hit_str}{data_str}")

        # Print statistics
        print(f"\n{Fore.CYAN}CACHE STATISTICS:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")
        for cache_name, stats in self.stats.items():
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
