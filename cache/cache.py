from .policies import ReplacementPolicy
from utils.logger import Logger, LogLevel
from colorama import Fore, Style

class Cache:
    def __init__(self, name, size, associativity, block_size, access_time, policy, next_level=None, logger=None):
        """Initialize a cache with the given parameters.

        Args:
            name (str): Name of the cache (e.g., 'L1Cache', 'L2Cache')
            size (int): Total size of the cache in bytes
            associativity (int): Number of ways in each set
            block_size (int): Size of each cache block in bytes
            access_time (float): Time taken to access this cache
            policy (str): Cache write policy ('write-through' or 'write-back')
            next_level (Cache or MainMemory, optional): Next level in memory hierarchy
            logger (Logger, optional): Logger instance for debugging
        """
        self._name = name
        self._size = size
        self._associativity = associativity
        self._block_size = block_size
        self._access_time = access_time
        self._policy = policy
        self._write_policy = policy  # Set write policy from input
        self._write_allocate = True if policy == 'write-back' else False  # Write-back implies write-allocate
        self._next_level = next_level
        self._logger = logger or Logger()  # Use provided logger or create new one
        self._exec_time = 0
        self._entries = []
        self._lru_order = []  # Track order of access for LRU policy
        self._data_flow = []  # Track data flow history
        self._policies = {
            "random": ReplacementPolicy.random,
            "fifo": ReplacementPolicy.fifo,
            "lru": ReplacementPolicy.lru
        }

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

    def write(self, address, data):
        """Write data to cache and handle cache misses"""
        self._exec_time += self._access_time
        entry = self.get_entry(address)
        next_level_data = None

        if entry is not None:
            entry["data"] = data
            entry["dirty"] = True
            if self._policy == "lru":
                self._lru_order.remove(entry)
                self._lru_order.append(entry)
            self._logger.log_cache_operation(self._name, "write", True, data)
        else:
            self._logger.log_cache_operation(self._name, "write", False, data)
            if len(self._entries) >= self._size:
                self.replace_entry(address)
            else:
                self._entries.append({"address": address, "data": data, "dirty": True})
                if self._policy == "lru":
                    self._lru_order.append(self._entries[-1])

        # Write through to next level
        if self._next_level:
            next_level_data = data
            self._next_level.write(address, data)

        # Track data flow
        self.track_data_flow('write', address, data, next_level_data)

    def read(self, address):
        """Read data from cache and handle cache misses"""
        self._exec_time += self._access_time
        entry = self.get_entry(address)
        next_level_data = None

        if entry is not None:
            if self._policy == "lru":
                self._lru_order.remove(entry)
                self._lru_order.append(entry)
            self._logger.log_cache_operation(self._name, "read", True, entry["data"])
            self.track_data_flow('read', address, entry["data"], None)
            return entry["data"]
        else:
            self._logger.log_cache_operation(self._name, "read", False)
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
                next_level_data = data
                self._logger.log_cache_operation(self._name, "read", False, data)

            # Track data flow
            self.track_data_flow('read', address, data, next_level_data)
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
            "next_level": self._next_level.name if self._next_level else None
        }
        return info

    def print_debug_info(self):
        """Print formatted debug information about the cache state"""
        info = self.debug_info()
        self._logger.log(LogLevel.DEBUG, f"\n=== Cache Debug Info: {self._name} ===")
        self._logger.log(LogLevel.DEBUG, f"Size: {info['size']} bytes")
        self._logger.log(LogLevel.DEBUG, f"Block Size: {info['block_size']} bytes")
        self._logger.log(LogLevel.DEBUG, f"Policy: {info['policy']}")
        self._logger.log(LogLevel.DEBUG, f"Access Time: {info['access_time']} ns")
        self._logger.log(LogLevel.DEBUG, f"Execution Time: {info['exec_time']} ns")
        self._logger.log(LogLevel.DEBUG, f"Number of Entries: {info['num_entries']}")
        self._logger.log(LogLevel.DEBUG, "\nEntries:")
        for entry in info['entries']:
            self._logger.log(LogLevel.DEBUG, f"  Address: {entry['address']}, Data: {entry['data']}, Dirty: {entry['dirty']}")
        if info['lru_order']:
            self._logger.log(LogLevel.DEBUG, f"\nLRU Order: {info['lru_order']}")
        self._logger.log(LogLevel.DEBUG, f"Next Level: {info['next_level']}")

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
            }
        }
        return stats

    def print_hierarchy_info(self):
        """Print information about the cache hierarchy"""
        self._logger.log(LogLevel.INFO, f"\n=== Cache Hierarchy Analysis ===")
        self._logger.log(LogLevel.INFO, f"\n=== Cache Level: {self._name} ===")
        self._logger.log(LogLevel.INFO, "Configuration:")
        self._logger.log(LogLevel.INFO, f"  Size: {self._size} bytes")
        self._logger.log(LogLevel.INFO, f"  Block Size: {self._block_size} bytes")
        self._logger.log(LogLevel.INFO, f"  Associativity: {self._associativity}")
        self._logger.log(LogLevel.INFO, f"  Write Policy: {self._write_policy}")
        self._logger.log(LogLevel.INFO, f"  Access Time: {self._access_time} ns")
        self._logger.log(LogLevel.INFO, f"  Total Execution Time: {self._exec_time} ns")
        self._logger.log(LogLevel.INFO, "\nEntry Statistics:")
        stats = self.get_entry_stats()
        self._logger.log(LogLevel.INFO, f"  Total Entries: {stats['total_entries']}")
        self._logger.log(LogLevel.INFO, f"  Dirty Entries: {stats['dirty_entries']}")
        self._logger.log(LogLevel.INFO, f"  Clean Entries: {stats['clean_entries']}")
        self._logger.log(LogLevel.INFO, f"  Address Range: {stats['address_range']['min']} - {stats['address_range']['max']}")

        if self._next_level:
            self._logger.log(LogLevel.INFO, f"\n=== {self._next_level.name} ===")
            self._logger.log(LogLevel.INFO, f"Access Time: {self._next_level.access_time} ns")
            self._logger.log(LogLevel.INFO, f"Total Execution Time: {self._next_level.get_exec_time()} ns")

    def validate_hierarchy(self):
        """
        Validates the entire cache hierarchy by checking data consistency and coherence.

        Returns:
            list: A list of validation issues found in the hierarchy.
        """
        issues = []

        # First validate this cache's state
        state_issues = self.validate_state()
        issues.extend(state_issues)

        # Check data consistency with next level if it exists and is a cache
        if self._next_level and isinstance(self._next_level, Cache):
            # For each entry in this cache
            for entry in self._entries:
                if entry.get("data") is not None:
                    address = entry["address"]
                    data = entry["data"]

                    # Find corresponding data in next level
                    next_level_data = self._next_level.read(address)

                    if next_level_data is None:
                        issues.append(f"Data at address {address} in {self._name} not found in {self._next_level._name}")
                    elif data != next_level_data:
                        issues.append(f"Data inconsistency at address {address} between {self._name} and {self._next_level._name}")

            # Recursively validate next level
            next_level_issues = self._next_level.validate_hierarchy()
            issues.extend(next_level_issues)

        return issues

    def track_data_flow(self, operation, address, data=None, next_level_data=None):
        """
        Track data flow through the cache hierarchy.

        Args:
            operation (str): The operation being performed ('read' or 'write')
            address (int): The memory address being accessed
            data (int, optional): The data being written or read
            next_level_data (int, optional): Data from the next level cache/memory
        """
        # Calculate block address and offset
        block_addr = address // self._block_size
        offset = address % self._block_size

        # Calculate set index and tag
        set_index = block_addr % (self._size // (self._block_size * self._associativity))
        tag = block_addr // (self._size // (self._block_size * self._associativity))

        # Create flow entry
        flow_entry = {
            'operation': operation,
            'address': address,
            'data': data,
            'block_addr': block_addr,
            'set_index': set_index,
            'tag': tag,
            'offset': offset,
            'cache_name': self._name,
            'next_level_data': next_level_data
        }

        # Add to data flow history
        self._data_flow.append(flow_entry)

        # Track in next level if it exists and is a cache
        if self._next_level and isinstance(self._next_level, Cache):
            self._next_level.track_data_flow(operation, address, data, next_level_data)

    def get_access_patterns(self):
        patterns = {
            'total_accesses': len(self._data_flow),
            'sequential_accesses': 0,
            'random_accesses': 0,
            'repeated_accesses': 0,
            'sequential_rate': 0.0,
            'random_rate': 0.0,
            'repeated_rate': 0.0
        }

        if len(self._data_flow) > 1:
            seen_addresses = set()

            for i in range(len(self._data_flow)):
                curr_addr = self._data_flow[i]['address']

                # Check for repeated access
                if curr_addr in seen_addresses:
                    patterns['repeated_accesses'] += 1
                seen_addresses.add(curr_addr)

                # Check for sequential vs random access
                if i > 0:
                    prev_addr = self._data_flow[i-1]['address']
                    if curr_addr == prev_addr + 1:
                        patterns['sequential_accesses'] += 1
                    else:
                        patterns['random_accesses'] += 1

            # Calculate rates
            total_transitions = len(self._data_flow) - 1
            if total_transitions > 0:
                patterns['sequential_rate'] = (patterns['sequential_accesses'] / total_transitions) * 100
                patterns['random_rate'] = (patterns['random_accesses'] / total_transitions) * 100
                patterns['repeated_rate'] = (patterns['repeated_accesses'] / len(self._data_flow)) * 100

        return patterns
