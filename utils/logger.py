from typing import Dict, List
from dataclasses import dataclass, field
from time import time

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
            if hit:
                print(f"[{cache_name}] Write: HIT")
            else:
                print(f"[{cache_name}] Write: MISS - Data: {data}")

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
            if hit:
                print(f"[{cache_name}] Read: HIT - Data: {data}")
            else:
                print(f"[{cache_name}] Read: MISS")

    def log_instruction(self, instruction):
        """Log instruction being executed"""
        if self.verbose:
            print(f"\nExecuting: {instruction}")

    def log_result(self, output_string, exec_time):
        """Log final results with statistics"""
        # Print cache operation summary
        print("\n" + "="*60)
        print("CACHE OPERATIONS SUMMARY")
        print("="*60)

        # Print detailed operation log
        print("\nOPERATION SEQUENCE:")
        print("-" * 60)
        for op in self.operations:
            hit_str = "HIT" if op.hit else "MISS"
            data_str = f" - Data: {op.data}" if op.data is not None else ""
            print(f"[{op.timestamp:.6f}] [{op.cache_name}] {op.operation.upper()}: {hit_str}{data_str}")

        # Print statistics
        print("\nCACHE STATISTICS:")
        print("-" * 60)
        for cache_name, stats in self.stats.items():
            print(f"\n{cache_name}:")
            print("  " + "-" * 20)

            # Read stats
            total_reads = stats["reads"]
            hits = stats["read_hits"]
            misses = stats["read_misses"]
            hit_rate = (hits / total_reads * 100) if total_reads > 0 else 0
            print(f"  Reads:")
            print(f"    Total: {total_reads}")
            print(f"    Hits: {hits}")
            print(f"    Misses: {misses}")
            print(f"    Hit Rate: {hit_rate:.1f}%")

            # Write stats
            total_writes = stats["writes"]
            hits = stats["write_hits"]
            misses = stats["write_misses"]
            hit_rate = (hits / total_writes * 100) if total_writes > 0 else 0
            print(f"  Writes:")
            print(f"    Total: {total_writes}")
            print(f"    Hits: {hits}")
            print(f"    Misses: {misses}")
            print(f"    Hit Rate: {hit_rate:.1f}%")

        # Print final output
        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60)
        print(f"Output String: {output_string}")
        print(f"Execution Time: {exec_time:.2f} nanoseconds")
