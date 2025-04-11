from .policies import ReplacementPolicy
from utils.logger import CacheLogger
from colorama import Fore, Style
from time import time

class Cache:
    def __init__(self, name, size, block_size, policy, access_time, next_level=None, logger=None):
        self._name = name
        self._size = size
        self._block_size = block_size
        self._policy = policy
        self._access_time = access_time
        self._exec_time = 0
        self._entries = []
        self._lru_order = []  # Track order of access for LRU policy
        self._next_level = next_level  # Next level of memory (Cache or MainMemory)
        self._policies = {
            "random": ReplacementPolicy.random,
            "fifo": ReplacementPolicy.fifo,
            "lru": ReplacementPolicy.lru
        }
        self._logger = logger
        self._access_patterns = {
            "sequential": 0,
            "random": 0,
            "repeated": 0
        }
        self._last_access = None
        self._access_history = []
        # New attributes
        self._write_back_buffer = []  # Track pending write-back operations
        self._coherence_state = {}  # Track cache line states (MESI protocol)
        self._prefetch_buffer = []  # For future prefetching implementation

    # Accessors
    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._size

    @property
    def block_size(self):
        return self._block_size

    @property
    def policy(self):
        return self._policy

    @property
    def access_time(self):
        return self._access_time

    @property
    def exec_time(self):
        return self._exec_time

    @property
    def entries(self):
        return self._entries

    @property
    def lru_order(self):
        return self._lru_order

    @property
    def next_level(self):
        return self._next_level

    @property
    def logger(self):
        return self._logger

    # Mutators
    @name.setter
    def name(self, value):
        self._name = value

    @size.setter
    def size(self, value):
        self._size = value

    @block_size.setter
    def block_size(self, value):
        self._block_size = value

    @policy.setter
    def policy(self, value):
        if value in self._policies:
            self._policy = value
        else:
            raise ValueError(f"Invalid policy. Must be one of: {list(self._policies.keys())}")

    @access_time.setter
    def access_time(self, value):
        if value >= 0:
            self._access_time = value
        else:
            raise ValueError("Access time must be non-negative")

    @next_level.setter
    def next_level(self, value):
        self._next_level = value

    @logger.setter
    def logger(self, value):
        self._logger = value

    def _update_access_pattern(self, address):
        """Track and analyze memory access patterns"""
        if self._last_access is not None:
            # Check if access is sequential
            if address == self._last_access + 1:
                self._access_patterns["sequential"] += 1
            # Check if access is repeated
            elif address == self._last_access:
                self._access_patterns["repeated"] += 1
            else:
                self._access_patterns["random"] += 1

        self._last_access = address
        self._access_history.append({
            "address": address,
            "timestamp": time()
        })

    def get_access_patterns(self):
        """Return statistics about memory access patterns"""
        total_accesses = sum(self._access_patterns.values())
        if total_accesses == 0:
            return {
                "sequential": 0,
                "random": 0,
                "repeated": 0,
                "percentages": {
                    "sequential": 0,
                    "random": 0,
                    "repeated": 0
                }
            }

        return {
            "counts": self._access_patterns,
            "percentages": {
                pattern: (count / total_accesses * 100)
                for pattern, count in self._access_patterns.items()
            }
        }

    def get_access_history(self, limit=100):
        """Return recent access history"""
        return self._access_history[-limit:] if limit else self._access_history

    def write(self, address, data):
        """Write data to cache and handle cache misses"""
        self._update_access_pattern(address)
        self._exec_time += self._access_time
        entry = self.get_entry(address)

        if entry is not None:
            entry["data"] = data
            entry["dirty"] = True
            if self._policy == "lru":
                self._lru_order.remove(entry)
                self._lru_order.append(entry)
            if self._logger:
                self._logger.log_cache_write(self._name, hit=True, data=data)
        else:
            if self._logger:
                self._logger.log_cache_write(self._name, hit=False, data=data)
            if len(self._entries) >= self._size:
                self.replace_entry(address)
            else:
                self._entries.append({"address": address, "data": data, "dirty": True})
                if self._policy == "lru":
                    self._lru_order.append(self._entries[-1])

        # Write through to next level
        if self._next_level:
            self._next_level.write(address, data)

    def read(self, address):
        """Read data from cache and handle cache misses"""
        self._update_access_pattern(address)
        self._exec_time += self._access_time
        entry = self.get_entry(address)

        if entry is not None:
            if self._policy == "lru":
                self._lru_order.remove(entry)
                self._lru_order.append(entry)
            if self._logger:
                self._logger.log_cache_read(self._name, hit=True, data=entry["data"])
            return entry["data"]
        else:
            if self._logger:
                self._logger.log_cache_read(self._name, hit=False)
            if len(self._entries) >= self._size:
                self.replace_entry(address)
            else:
                self._entries.append({"address": address, "data": None, "dirty": False})
                if self._policy == "lru":
                    self._lru_order.append(self._entries[-1])

            # Read from next level
            data = None
            if self._next_level:
                data = self._next_level.read(address)
                self._entries[-1]["data"] = data
                if self._logger:
                    self._logger.log_cache_read(self._name, hit=False, data=data)
            return data

    def replace_entry(self, address):
        """Replace a cache entry using the specified policy"""
        if self._policy in self._policies:
            # Write back dirty data before replacement
            old_entry = self._entries[0] if self._policy == "fifo" else self._lru_order[0]
            if old_entry.get("dirty", False) and self._next_level:
                self._next_level.write(old_entry["address"], old_entry["data"])

            # Apply replacement policy
            self._policies[self._policy](self, address)

    def get_entry(self, address):
        """Get cache entry for given address"""
        for entry in self._entries:
            if entry["address"] == address:
                return entry
        return None

    def get_exec_time(self):
        """Get total execution time including next level memory"""
        total_time = self._exec_time
        if self._next_level:
            total_time += self._next_level.get_exec_time()
        return total_time

    # Debugging methods
    def debug_info(self):
        """Return detailed debug information about the cache state"""
        info = {
            "name": self._name,
            "size": self._size,
            "block_size": self._block_size,
            "policy": self._policy,
            "access_time": self._access_time,
            "exec_time": self._exec_time,
            "num_entries": len(self._entries),
            "entries": self._entries,
            "lru_order": [entry["address"] for entry in self._lru_order] if self._policy == "lru" else None,
            "next_level": self._next_level.name if self._next_level else None,
            "write_back_buffer": self._write_back_buffer,
            "coherence_states": self._coherence_state,
            "prefetch_buffer": self._prefetch_buffer,
            "access_patterns": self._access_patterns,
            "last_access": self._last_access,
            "access_history_size": len(self._access_history)
        }
        return info

    def print_debug_info(self):
        """Print formatted debug information about the cache state"""
        info = self.debug_info()
        print(f"\n{Fore.CYAN}=== Cache Debug Info: {self._name} ==={Style.RESET_ALL}")
        print(f"Size: {info['size']} bytes")
        print(f"Block Size: {info['block_size']} bytes")
        print(f"Policy: {info['policy']}")
        print(f"Access Time: {info['access_time']} ns")
        print(f"Execution Time: {info['exec_time']} ns")
        print(f"Number of Entries: {info['num_entries']}")

        print("\nEntries:")
        for entry in info['entries']:
            print(f"  Address: {entry['address']}, Data: {entry['data']}, Dirty: {entry['dirty']}")

        if info['lru_order']:
            print(f"\nLRU Order: {info['lru_order']}")

        print(f"Next Level: {info['next_level']}")

        print("\nWrite-Back Buffer:")
        for wb in info['write_back_buffer']:
            print(f"  {wb}")

        print("\nCoherence States:")
        for addr, state in info['coherence_states'].items():
            print(f"  Address {addr}: {state}")

        print("\nPrefetch Buffer:")
        for prefetch in info['prefetch_buffer']:
            print(f"  {prefetch}")

        print("\nAccess Patterns:")
        for pattern, count in info['access_patterns'].items():
            print(f"  {pattern}: {count}")

    def validate_state(self):
        """Validate the cache state and return any issues found"""
        issues = []

        # Check if number of entries exceeds size
        if len(self._entries) > self._size:
            issues.append(f"Number of entries ({len(self._entries)}) exceeds cache size ({self._size})")

        # Check LRU order consistency
        if self._policy == "lru":
            if len(self._lru_order) != len(self._entries):
                issues.append(f"LRU order length ({len(self._lru_order)}) doesn't match entries length ({len(self._entries)})")
            for entry in self._lru_order:
                if entry not in self._entries:
                    issues.append(f"LRU order contains entry not in cache: {entry}")

        # Check for duplicate addresses
        addresses = [entry["address"] for entry in self._entries]
        if len(addresses) != len(set(addresses)):
            issues.append("Duplicate addresses found in cache entries")

        # Check write-back buffer consistency
        for wb in self._write_back_buffer:
            if wb["address"] not in addresses:
                issues.append(f"Write-back buffer contains address not in cache: {wb['address']}")

        # Check coherence state consistency
        for addr in self._coherence_state:
            if addr not in addresses:
                issues.append(f"Coherence state exists for address not in cache: {addr}")

        return issues

    def get_entry_stats(self):
        """Return statistics about cache entries"""
        stats = {
            "total_entries": len(self._entries),
            "dirty_entries": sum(1 for entry in self._entries if entry["dirty"]),
            "clean_entries": sum(1 for entry in self._entries if not entry["dirty"]),
            "address_range": {
                "min": min(entry["address"] for entry in self._entries) if self._entries else None,
                "max": max(entry["address"] for entry in self._entries) if self._entries else None
            },
            "write_back_buffer_size": len(self._write_back_buffer),
            "coherence_states": {
                state: sum(1 for s in self._coherence_state.values() if s == state)
                for state in set(self._coherence_state.values())
            },
            "prefetch_buffer_size": len(self._prefetch_buffer)
        }
        return stats
