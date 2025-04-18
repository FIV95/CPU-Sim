from .policies import ReplacementPolicy
from utils.logger import Logger, LogLevel
from colorama import Fore, Style
import random
from time import time

class DEBUG:
    ENABLED = True  # Enable cache debug messages
    VERBOSE = True  # Enable verbose mode for detailed debugging

    @staticmethod
    def log(msg, verbose=False):
        """Log message if enabled and either verbose mode is on or message is marked as not verbose"""
        if DEBUG.ENABLED and (DEBUG.VERBOSE or not verbose):
            print(f"[CACHE DEBUG] {msg}")

    @staticmethod
    def set_enabled(enabled):
        """Enable or disable debug logging"""
        DEBUG.ENABLED = enabled

    @staticmethod
    def set_verbose(verbose):
        """Enable or disable verbose logging"""
        DEBUG.VERBOSE = verbose

class Cache:
    def __init__(self, name, size, line_size, associativity, access_time=10, write_policy="write-back", next_level=None, logger=None):
        """Initialize cache with given parameters"""
        self._name = name
        self._size = size
        self._line_size = line_size
        self._associativity = associativity
        self._access_time = access_time
        self._write_policy = write_policy
        self._next_level = next_level
        self._logger = logger if logger else Logger()
        self._sets = size // (line_size * associativity)
        self._entries = [[] for _ in range(self._sets)]
        self._stats = {
            'hits': 0,
            'misses': 0,
            'reads': 0,
            'writes': 0,
            'total_access_time': 0,
            'min_access_time': float('inf'),
            'max_access_time': 0
        }
        self._exec_time = 0
        self._data_flow = []
        self._last_access_time = 0
        self._object_size = 32  # Size of Python objects in bytes

    def set_next_level(self, next_level):
        """Set the next level in the memory hierarchy"""
        self._next_level = next_level

    def _calculate_cache_indices(self, address):
        """Calculate set index and tag for a given address

        For Python integers, we'll use a 32-bit addressing scheme:
        - Offset bits = log2(line_size)
        - Index bits = log2(num_sets)
        - Tag bits = 32 - offset_bits - index_bits
        """
        # Calculate required bits for each field
        offset_bits = (self._line_size - 1).bit_length()  # Number of bits needed for byte offset
        index_bits = (self._sets - 1).bit_length()        # Number of bits needed for set index

        # Create masks for extracting fields
        offset_mask = (1 << offset_bits) - 1
        index_mask = ((1 << index_bits) - 1) << offset_bits

        # Extract fields using masks
        offset = address & offset_mask
        set_index = (address & index_mask) >> offset_bits
        tag = address >> (offset_bits + index_bits)

        # Debug output
        self._logger.log(LogLevel.DEBUG, f"\nAddress Breakdown for {self._name}:")
        self._logger.log(LogLevel.DEBUG, f"Address: {address} (0x{address:x})")
        self._logger.log(LogLevel.DEBUG, f"Line Size: {self._line_size} (offset bits: {offset_bits})")
        self._logger.log(LogLevel.DEBUG, f"Sets: {self._sets} (index bits: {index_bits})")
        self._logger.log(LogLevel.DEBUG, f"Offset: {offset} (0x{offset:x})")
        self._logger.log(LogLevel.DEBUG, f"Set Index: {set_index} (0x{set_index:x})")
        self._logger.log(LogLevel.DEBUG, f"Tag: {tag} (0x{tag:x})")

        return set_index, tag

    def read(self, address, output=True):
        """Read data from cache"""
        start_time = time()

        # Debug log for every read attempt
        self._logger.log(LogLevel.DEBUG, f"\n=== Cache Read Operation ===")
        self._logger.log(LogLevel.DEBUG, f"Address: {address}")
        self._logger.log(LogLevel.DEBUG, f"Current Stats - Hits: {self._stats['hits']}, Misses: {self._stats['misses']}")

        # Track data flow
        self._data_flow.append({
            'operation': 'read',
            'address': address,
            'time': start_time
        })

        # Calculate set index and tag using bit masking
        set_index, tag = self._calculate_cache_indices(address)

        self._logger.log(LogLevel.DEBUG, f"Set Index: {set_index}, Tag: {tag}")
        self._logger.log(LogLevel.DEBUG, f"Current Set Contents: {self._entries[set_index]}")

        # Check for hit
        for entry in self._entries[set_index]:
            if entry["tag"] == tag and entry["valid"]:
                # Cache hit
                self._stats['hits'] += 1
                self._stats['reads'] += 1
                value = int(entry["data"])

                self._logger.log(LogLevel.DEBUG, f"Cache HIT - Value: {value}")

                # Log the hit with enhanced visualization
                if output:
                    self._logger.log_cache_operation(
                        self._name,
                        'read',
                        True,
                        {
                            'address': address,
                            'value': value,
                            'set': set_index,
                            'tag': tag,
                            'associativity': self._associativity,
                            'entries': len(self._entries[set_index]),
                            'dirty': entry["dirty"]
                        }
                    )

                # Update LRU order
                self._update_lru(set_index, entry)

                # Calculate access time and update statistics
                access_time = time() - start_time
                self._exec_time += access_time
                self._update_stats(access_time)

                return value

        # Cache miss
        self._stats['misses'] += 1
        self._stats['reads'] += 1

        # Get value from next level
        if self._next_level:
            value = self._next_level.read(address)

            # Log the miss with enhanced visualization
            if output:
                self._logger.log_cache_operation(
                    self._name,
                    'read',
                    False,
                    {
                        'address': address,
                        'value': value,
                        'set': set_index,
                        'tag': tag,
                        'associativity': self._associativity,
                        'entries': len(self._entries[set_index]),
                        'eviction_needed': len(self._entries[set_index]) >= self._associativity
                    }
                )

            # Create new entry
            new_entry = {
                "tag": tag,
                "data": value,
                "valid": True,
                "dirty": False,
                "lru": 0
            }

            # Handle set full condition
            if len(self._entries[set_index]) >= self._associativity:
                # Find LRU entry to replace
                lru_entry = min(self._entries[set_index], key=lambda x: x["lru"])
                if lru_entry["dirty"] and self._write_policy == "write-back":
                    # Write back dirty data
                    old_address = lru_entry["tag"] * (self._line_size * self._sets) + (set_index * self._line_size)
                    self._next_level.write(old_address, lru_entry["data"])
                self._entries[set_index].remove(lru_entry)

            # Add new entry
            self._entries[set_index].append(new_entry)
            self._update_lru(set_index, new_entry)

            # Calculate access time and update statistics
            access_time = time() - start_time
            self._exec_time += access_time
            self._update_stats(access_time)

            return value
        else:
            raise ValueError("No next level cache/memory available")

    def write(self, address, data, output=True, propagate=True):
        """Write data to cache
        Args:
            address: Memory address to write to
            data: Data to write
            output: Whether to output debug information
            propagate: Whether to propagate writes to next level (used internally)
        """
        start_time = time()

        # Debug log for every write attempt
        self._logger.log(LogLevel.DEBUG, f"\n=== Cache Write Operation ({self._name}) ===")
        self._logger.log(LogLevel.DEBUG, f"Address: {address}, Data: {data}")
        self._logger.log(LogLevel.DEBUG, f"Write Policy: {self._write_policy}")
        self._logger.log(LogLevel.DEBUG, f"Current Stats - Hits: {self._stats['hits']}, Misses: {self._stats['misses']}")

        # Ensure data is integer
        data = int(data)

        # Track data flow
        self._data_flow.append({
            'operation': 'write',
            'address': address,
            'data': data,
            'time': start_time
        })

        # Calculate set index and tag using bit masking
        set_index, tag = self._calculate_cache_indices(address)

        self._logger.log(LogLevel.DEBUG, f"Set Index: {set_index}, Tag: {tag}")
        self._logger.log(LogLevel.DEBUG, f"Current Set Contents: {self._entries[set_index]}")

        # Check for hit
        hit_entry = None
        for entry in self._entries[set_index]:
            if entry["tag"] == tag and entry["valid"]:
                hit_entry = entry
                break

        if hit_entry:
            # Cache hit
            self._stats['hits'] += 1
            self._stats['writes'] += 1

            # Log the hit
            if output:
                self._logger.log_cache_operation(
                    self._name,
                    'write',
                    True,
                    {
                        'address': address,
                        'value': data,
                        'set': set_index,
                        'tag': tag,
                        'associativity': self._associativity,
                        'entries': len(self._entries[set_index]),
                        'dirty': hit_entry["dirty"]
                    }
                )

            # Update data
            hit_entry["data"] = data

            # Handle write policy
            if self._write_policy == "write-through" and self._next_level and propagate:
                # Propagate to next level for write-through
                self._next_level.write(address, data, output, propagate=True)
            else:
                # Mark as dirty for write-back
                hit_entry["dirty"] = True

            # Update LRU order
            self._update_lru(set_index, hit_entry)

        else:
            # Cache miss
            self._stats['misses'] += 1
            self._stats['writes'] += 1

            # Log the miss
            if output:
                self._logger.log_cache_operation(
                    self._name,
                    'write',
                    False,
                    {
                        'address': address,
                        'value': data,
                        'set': set_index,
                        'tag': tag,
                        'associativity': self._associativity,
                        'entries': len(self._entries[set_index]),
                        'eviction_needed': len(self._entries[set_index]) >= self._associativity
                    }
                )

            # Create new entry
            new_entry = {
                "tag": tag,
                "data": data,
                "valid": True,
                "dirty": self._write_policy == "write-back",  # Only mark dirty for write-back
                "lru": 0
            }

            # Handle set full condition
            if len(self._entries[set_index]) >= self._associativity:
                # Find LRU entry to replace
                lru_entry = min(self._entries[set_index], key=lambda x: x["lru"])
                if lru_entry["dirty"] and self._write_policy == "write-back" and self._next_level:
                    # Calculate original address using bit fields
                    offset_bits = (self._line_size - 1).bit_length()
                    index_bits = (self._sets - 1).bit_length()
                    old_address = (lru_entry["tag"] << (offset_bits + index_bits)) | (set_index << offset_bits)

                    # Debug log address reconstruction
                    self._logger.log(LogLevel.DEBUG, f"\n=== Write-Back Address Reconstruction ===")
                    self._logger.log(LogLevel.DEBUG, f"Tag: {lru_entry['tag']}, Set Index: {set_index}")
                    self._logger.log(LogLevel.DEBUG, f"Offset bits: {offset_bits}, Index bits: {index_bits}")
                    self._logger.log(LogLevel.DEBUG, f"Reconstructed address: {old_address}")

                    # Write back dirty data before eviction
                    self._next_level.write(old_address, lru_entry["data"], output, propagate=True)
                self._entries[set_index].remove(lru_entry)

            # Add new entry
            self._entries[set_index].append(new_entry)
            self._update_lru(set_index, new_entry)

            # Handle write policy for new entries
            if self._write_policy == "write-through" and self._next_level and propagate:
                # Propagate to next level for write-through
                self._next_level.write(address, data, output, propagate=True)

        # Calculate access time and update statistics
        access_time = time() - start_time
        self._exec_time += access_time
        self._update_stats(access_time)

        return True

    def _update_lru(self, set_index, entry):
        """Update LRU counters for a set"""
        # Decrease all other entries' LRU values
        for e in self._entries[set_index]:
            if e != entry:
                e["lru"] = max(0, e["lru"] - 1)

        # Set the accessed entry to the highest LRU value
        entry["lru"] = self._associativity - 1

    def _update_stats(self, access_time):
        """Update cache statistics"""
        self._stats['total_access_time'] += access_time
        self._stats['min_access_time'] = min(self._stats['min_access_time'], access_time)
        self._stats['max_access_time'] = max(self._stats['max_access_time'], access_time)
        self._last_access_time = access_time

    def _log_stats(self):
        """Log cache statistics"""
        self._logger.log(LogLevel.DEBUG, f"Cache stats: hits={self._stats['hits']}, misses={self._stats['misses']}, "
                        f"hit_rate={self._stats['hits']/self._stats['reads'] if self._stats['reads'] > 0 else 0:.2%}")

    def get_cache_state(self):
        """Return the current state of the cache as a dictionary mapping (set_index, block_index) to (tag, data)"""
        state = {}
        for set_idx in range(len(self._entries)):
            for block_idx, entry in enumerate(self._entries[set_idx]):
                if entry["valid"]:
                    state[(set_idx, block_idx)] = (entry["tag"], entry["data"])
        return state

    def get_performance_stats(self):
        """Get cache performance statistics"""
        total_accesses = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_accesses * 100) if total_accesses > 0 else 0
        return {
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'hit_rate': hit_rate
        }

    def debug_info(self):
        """Get debug information about cache state"""
        return {
            "name": self._name,
            "size": self._size,
            "line_size": self._line_size,
            "associativity": self._associativity,
            "sets": self._sets,
            "write_policy": self._write_policy,
            "performance_stats": self.get_performance_stats(),
            "entries": len([entry for entries in self._entries for entry in entries]),
            "dirty_entries": len([entry for entries in self._entries for entry in entries if entry["dirty"]])
        }

    def print_debug_info(self):
        """Print formatted debug information"""
        info = self.debug_info()
        self._logger.log(LogLevel.DEBUG, f"\n=== {self._name} Debug Info ===")
        self._logger.log(LogLevel.DEBUG, f"Size: {info['size']} bytes")
        self._logger.log(LogLevel.DEBUG, f"Line Size: {info['line_size']} bytes")
        self._logger.log(LogLevel.DEBUG, f"Associativity: {info['associativity']}-way")
        self._logger.log(LogLevel.DEBUG, f"Sets: {info['sets']}")
        self._logger.log(LogLevel.DEBUG, f"Write Policy: {info['write_policy']}")
        self._logger.log(LogLevel.DEBUG, f"Total Entries: {info['entries']}")
        self._logger.log(LogLevel.DEBUG, f"Dirty Entries: {info['dirty_entries']}")

        perf_stats = info['performance_stats']
        self._logger.log(LogLevel.DEBUG, "\nPerformance Statistics:")
        self._logger.log(LogLevel.DEBUG, f"  Access Count: {total_accesses}")
        self._logger.log(LogLevel.DEBUG, f"  Hit Rate: {perf_stats['hit_rate']:.2%}")
        self._logger.log(LogLevel.DEBUG, f"  Execution Time: {self._exec_time:.6f}s")

    def get_exec_time(self):
        """Get total execution time"""
        return self._exec_time

    def replace_entry(self, address):
        """Replace a cache entry using the specified policy"""
        DEBUG.log(f"{self._name} replacing entry for addr={address}")
        if self._policy in self._policies:
            # Write back dirty data before replacement if using write-back policy
            old_entry = self._entries[0] if self._policy == "fifo" else self._lru_order[0]
            if self._write_policy == "write-back" and old_entry.get("dirty", False) and self._next_level:
                DEBUG.log(f"{self._name} writing back dirty entry: addr={old_entry['address']}, data={old_entry['data']}")
                self._next_level.write(old_entry["address"], old_entry["data"])
                old_entry["dirty"] = False

            # Apply replacement policy
            self._policies[self._policy](self, address)
            DEBUG.log(f"{self._name} replacement complete")

    def get_entry(self, address):
        """Get cache entry for given address"""
        for entry in self._entries:
            if entry["address"] == address:
                return entry
        return None

    def get_access_patterns(self):
        """Analyze access patterns from data flow"""
        if not self._data_flow:
            return {
                'total_accesses': 0,
                'sequential_accesses': 0,
                'random_accesses': 0,
                'repeated_accesses': 0,
                'sequential_rate': 0.0,
                'random_rate': 0.0,
                'repeated_rate': 0.0
            }

        total = len(self._data_flow)
        sequential = 0
        random = 0
        repeated = set()
        prev_addr = None

        for i, access in enumerate(self._data_flow):
            curr_addr = access['address']

            # Check for repeated accesses
            if curr_addr in repeated:
                repeated.add(curr_addr)

            # Check for sequential vs random access
            if prev_addr is not None:
                if curr_addr == prev_addr + 1:
                    sequential += 1
                else:
                    random += 1

            prev_addr = curr_addr

        return {
            'total_accesses': total,
            'sequential_accesses': sequential,
            'random_accesses': random,
            'repeated_accesses': len(repeated),
            'sequential_rate': (sequential / (total - 1)) * 100 if total > 1 else 0.0,
            'random_rate': (random / (total - 1)) * 100 if total > 1 else 0.0,
            'repeated_rate': (len(repeated) / total) * 100
        }

    def write_back_all(self):
        """Write back all dirty entries to the next level"""
        self._logger.log(LogLevel.DEBUG, f"\n=== Write-back operation for {self._name} ===")
        self._logger.log(LogLevel.DEBUG, "Cache state before write-back:")
        self._logger.log(LogLevel.DEBUG, f"Total entries: {sum(len(entries) for entries in self._entries)}")
        dirty_count = sum(1 for entries in self._entries for entry in entries if entry.get("dirty", False))
        self._logger.log(LogLevel.DEBUG, f"Dirty entries: {dirty_count}")
        self._logger.log(LogLevel.DEBUG, f"Clean entries: {sum(len(entries) for entries in self._entries) - dirty_count}")

        # Write back all dirty entries
        for set_index, entries in enumerate(self._entries):
            for entry in entries:
                if entry.get("dirty", False):
                    # Calculate address from tag and set index
                    address = entry["tag"] * (self._line_size * self._sets) + (set_index * self._line_size)

                    self._logger.log(LogLevel.DEBUG, f"\nWriting back dirty entry:")
                    self._logger.log(LogLevel.DEBUG, f"  Address: {address}")
                    self._logger.log(LogLevel.DEBUG, f"  Data: {entry['data']}")
                    self._logger.log(LogLevel.DEBUG, f"  Dirty: {entry['dirty']}")

                    try:
                        # Write to next level
                        if self._next_level:
                            self._logger.log(LogLevel.DEBUG, f"  Writing to next level: {self._next_level._name}")
                            self._next_level.write(address, entry["data"])
                            self._logger.log(LogLevel.DEBUG, "  Write successful")
                        else:
                            # If no next level, write directly to main memory
                            self._logger.log(LogLevel.DEBUG, "  No next level, writing to main memory")
                            # Get main memory from the memory hierarchy
                            memory = self._get_main_memory()
                            if memory:
                                memory.write(address, entry["data"])
                                self._logger.log(LogLevel.DEBUG, "  Write successful")
                            else:
                                self._logger.log(LogLevel.ERROR, "  No main memory found in hierarchy")

                        # Mark as clean
                        entry["dirty"] = False
                        self._logger.log(LogLevel.DEBUG, "  Entry marked as clean")
                    except Exception as e:
                        self._logger.log(LogLevel.ERROR, f"  Error writing back entry: {str(e)}")
                        import traceback
                        self._logger.log(LogLevel.ERROR, f"  Stack trace: {traceback.format_exc()}")

        # Log final cache state
        self._logger.log(LogLevel.DEBUG, "\nCache state after write-back:")
        self._logger.log(LogLevel.DEBUG, f"Total entries: {sum(len(entries) for entries in self._entries)}")
        dirty_count = sum(1 for entries in self._entries for entry in entries if entry.get("dirty", False))
        self._logger.log(LogLevel.DEBUG, f"Dirty entries: {dirty_count}")
        self._logger.log(LogLevel.DEBUG, f"Clean entries: {sum(len(entries) for entries in self._entries) - dirty_count}")
        self._logger.log(LogLevel.DEBUG, "=== Write-back operation complete ===\n")

    def _get_main_memory(self):
        """Traverse the cache hierarchy to find the main memory"""
        current = self._next_level
        while current:
            if not current._next_level:
                return current
            current = current._next_level
        return None

    def get_addresses(self):
        """Return a list of all valid addresses currently in the cache."""
        addresses = []
        for entry in self._entries:
            if isinstance(entry, list):  # Handle set-associative entries
                for line in entry:
                    if line and line.get('valid', False):
                        addresses.append(line.get('address'))
            elif entry and entry.get('valid', False):  # Handle direct-mapped entries
                addresses.append(entry.get('address'))
        return addresses
