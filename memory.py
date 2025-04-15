from time import sleep, time
from colorama import Fore, Style
from utils.logger import Logger, LogLevel

# Memory class used to create different
# memory types within the simulation
class Memory():
    def __init__(self, name="Memory", size=1024):
        """Initialize memory with name and size"""
        self._name = name
        self._size = int(size)  # Ensure size is an integer
        self._data = [0] * self._size
        self._logger = Logger()
        self._access_time = 100  # Default access time in ns
        self._exec_time = 0
        self._access_count = 0
        self._total_access_time = 0
        self._min_access_time = float('inf')
        self._max_access_time = 0
        self._bytes_transferred = 0
        self._latency_stats = {
            "min": float('inf'),
            "max": 0,
            "total": 0,
            "count": 0
        }
        # Track stack operations
        self._stack_accesses = 0
        self._stack_region = (size - 512, size)  # Reserve last 512B for stack (enough for Python objects)
        self._reads = 0
        self._writes = 0

    def read(self, address, output=True):
        """Read a value from memory"""
        start_time = time()

        if not self._validate_address(address):
            raise ValueError(f"Invalid memory address: {address}")

        # Track if this is a stack access
        if self._stack_region[0] <= address <= self._stack_region[1]:
            self._stack_accesses += 1
            # Stack accesses might be slightly faster due to locality
            self._access_time = 90  # 10% faster
        else:
            self._access_time = 100

        # Get value and ensure it's an integer
        value = int(self._data[address])
        access_time = self._access_time

        # Update statistics
        self._access_count += 1
        self._exec_time += access_time
        self._total_access_time += access_time
        self._min_access_time = min(self._min_access_time, access_time)
        self._max_access_time = max(self._max_access_time, access_time)
        self._bytes_transferred += 32  # Python objects are ~32 bytes
        self._reads += 1

        # Log operation details
        if output:
            self._logger.log_memory_operation("read", {
                "address": address,
                "value": value,
                "access_time": access_time,
                "total_exec_time": self._exec_time
            })

        return value

    def write(self, address, data, output=True, propagate=None):
        """Write a value to memory
        Args:
            address: Memory address to write to
            data: Data to write
            output: Whether to output debug information
            propagate: Ignored parameter for compatibility with cache interface
        """
        start_time = time()

        if not self._validate_address(address):
            raise ValueError(f"Invalid memory address: {address}")

        # Track if this is a stack access
        if self._stack_region[0] <= address <= self._stack_region[1]:
            self._stack_accesses += 1
            # Stack accesses might be slightly faster due to locality
            self._access_time = 90  # 10% faster
        else:
            self._access_time = 100

        # Ensure data is an integer
        data = int(data)

        # Write value
        self._data[address] = data
        access_time = self._access_time

        # Update statistics
        self._access_count += 1
        self._exec_time += access_time
        self._total_access_time += access_time
        self._min_access_time = min(self._min_access_time, access_time)
        self._max_access_time = max(self._max_access_time, access_time)
        self._bytes_transferred += 32  # Python objects are ~32 bytes
        self._writes += 1

        # Log operation details
        if output:
            self._logger.log_memory_operation("write", {
                "address": address,
                "value": data,
                "access_time": access_time,
                "total_exec_time": self._exec_time
            })

        return True

    def _validate_address(self, address):
        """Validate a memory address"""
        if not isinstance(address, int):
            return False
        if address < 0 or address >= self._size:
            return False
        return True

    def get_performance_stats(self):
        """Return performance statistics about the memory"""
        return {
            "access_count": self._access_count,
            "total_access_time": self._total_access_time,
            "min_access_time": self._min_access_time,
            "max_access_time": self._max_access_time,
            "avg_access_time": self._total_access_time / self._access_count if self._access_count > 0 else 0,
            "exec_time": self._exec_time,
            "bytes_transferred": self._bytes_transferred,
            "stack_accesses": self._stack_accesses,
            "reads": self._reads,
            "writes": self._writes,
            "total_accesses": self._reads + self._writes
        }

    def get_exec_time(self):
        """Get total execution time"""
        return self._exec_time

    def debug_info(self):
        """Get debug information about memory state"""
        return {
            "name": self._name,
            "size": self._size,
            "access_count": self._access_count,
            "exec_time": self._exec_time,
            "bytes_transferred": self._bytes_transferred,
            "performance_stats": self.get_performance_stats()
        }

    def print_debug_info(self):
        """Print formatted debug information"""
        info = self.debug_info()
        self._logger.log(LogLevel.DEBUG, f"\n=== {self._name} Debug Info ===")
        self._logger.log(LogLevel.DEBUG, f"Size: {info['size']} bytes")
        self._logger.log(LogLevel.DEBUG, f"Access Count: {info['access_count']}")
        self._logger.log(LogLevel.DEBUG, f"Execution Time: {info['exec_time']:.6f}s")
        self._logger.log(LogLevel.DEBUG, f"Bytes Transferred: {info['bytes_transferred']} bytes")

        perf_stats = info['performance_stats']
        self._logger.log(LogLevel.DEBUG, "\nPerformance Statistics:")
        self._logger.log(LogLevel.DEBUG, f"  Min Access Time: {perf_stats['min_access_time']:.6f}s")
        self._logger.log(LogLevel.DEBUG, f"  Max Access Time: {perf_stats['max_access_time']:.6f}s")
        self._logger.log(LogLevel.DEBUG, f"  Avg Access Time: {perf_stats['avg_access_time']:.6f}s")
        self._logger.log(LogLevel.DEBUG, f"  Bandwidth: {perf_stats['bytes_transferred'] / perf_stats['exec_time']:.2f} bytes/s")

    # New memory inspection methods
    def dump_memory_region(self, start_addr, size, logger):
        """Dump a region of memory for inspection"""
        if not self._validate_address(start_addr) or not self._validate_address(start_addr + size - 1):
            logger.log(LogLevel.ERROR, f"Invalid memory region: [{start_addr}, {start_addr + size})")
            return

        logger.log(LogLevel.DEBUG, f"\nMemory Dump [{self._name}] - Region: {start_addr} to {start_addr + size - 1}")
        logger.log(LogLevel.DEBUG, "Addr  | Value | ASCII")
        logger.log(LogLevel.DEBUG, "-" * 30)

        for addr in range(start_addr, start_addr + size):
            value = self._data[addr]
            ascii_char = chr(value) if 32 <= value <= 126 else '.'
            logger.log(LogLevel.DEBUG, f"{addr:04x} | {value:5d} | {ascii_char}")

    def analyze_memory_usage(self, logger):
        """Analyze memory usage patterns"""
        used_regions = []
        start = None

        # Find contiguous used regions
        for addr in range(self._size):
            if self._data[addr] != 0:
                if start is None:
                    start = addr
            elif start is not None:
                used_regions.append((start, addr - 1))
                start = None

        if start is not None:
            used_regions.append((start, self._size - 1))

        logger.log(LogLevel.DEBUG, f"\nMemory Usage Analysis [{self._name}]")
        logger.log(LogLevel.DEBUG, f"Total Size: {self._size} bytes")
        logger.log(LogLevel.DEBUG, "Used Regions:")

        total_used = 0
        for start, end in used_regions:
            size = end - start + 1
            total_used += size
            logger.log(LogLevel.DEBUG, f"  [{start:04x} - {end:04x}] Size: {size} bytes")

        usage_percent = (total_used / self._size) * 100
        logger.log(LogLevel.DEBUG, f"Total Used: {total_used} bytes ({usage_percent:.2f}%)")
        logger.log(LogLevel.DEBUG, f"Total Free: {self._size - total_used} bytes ({100 - usage_percent:.2f}%)")

    def find_pattern(self, pattern, logger):
        """Search for a specific pattern in memory"""
        if not pattern:
            return

        logger.log(LogLevel.DEBUG, f"\nSearching for pattern in {self._name}")

        for addr in range(self._size - len(pattern) + 1):
            found = True
            for i, val in enumerate(pattern):
                if self._data[addr + i] != val:
                    found = False
                    break

            if found:
                logger.log(LogLevel.DEBUG, f"Pattern found at address: {addr:04x}")
                self.dump_memory_region(max(0, addr - 8), min(16, self._size - addr), logger)

# Memory class used for the main
# memory data storage
class MainMemory(Memory):
    def __init__(self, name="MainMemory", size=1024):
        super().__init__(name, size)
        self._memory_map = {}  # Track memory mapping
        self._access_patterns = []  # Track access patterns
        self._access_pattern = {
            "sequential": 0,
            "repeated": 0,
            "random": 0,
            "last_address": None
        }  # Current access pattern tracking
        # Initialize latency tracking
        self._min_latency = float('inf')
        self._max_latency = 0
        self._total_latency = 0

    def get_performance_stats(self):
        """Return performance statistics about the main memory"""
        stats = super().get_performance_stats()
        stats.update({
            "memory_map": self._memory_map,
            "access_patterns": self._access_patterns
        })
        return stats

    # Accessors
    @property
    def data(self):
        return self._data

    # Mutators
    @data.setter
    def data(self, value):
        if isinstance(value, list):
            self._data = value
        else:
            raise ValueError("Data must be a list")

    # Return data from main memory address
    def read(self, address):
        """Read a value from main memory"""
        if not self._validate_address(address):
            raise ValueError(f"Invalid memory address: {address}")

        # Track access pattern
        if self._access_pattern["last_address"] is not None:
            if address == self._access_pattern["last_address"] + 1:
                self._access_pattern["sequential"] += 1
            elif address == self._access_pattern["last_address"]:
                self._access_pattern["repeated"] += 1
            else:
                self._access_pattern["random"] += 1
        self._access_pattern["last_address"] = address

        # Ensure we return an integer
        value = int(self._data[address])

        # Update statistics
        access_time = self._calculate_access_time()
        self._exec_time += access_time
        self._update_stats(access_time)

        return value

    # Write data to main memory address
    def write(self, address, data):
        """Write a value to main memory"""
        if not self._validate_address(address):
            raise ValueError(f"Invalid memory address: {address}")

        # Track access pattern
        if self._access_pattern["last_address"] is not None:
            if address == self._access_pattern["last_address"] + 1:
                self._access_pattern["sequential"] += 1
            elif address == self._access_pattern["last_address"]:
                self._access_pattern["repeated"] += 1
            else:
                self._access_pattern["random"] += 1
        self._access_pattern["last_address"] = address

        # Ensure we store an integer
        self._data[address] = int(data)

        # Update statistics
        access_time = self._calculate_access_time()
        self._exec_time += access_time
        self._update_stats(access_time)

        return True

    def _calculate_access_time(self):
        """Calculate memory access time based on access pattern"""
        base_time = self._access_time
        # Sequential access is faster
        if self._access_pattern["last_address"] is not None:
            if self._access_pattern["sequential"] > self._access_pattern["random"]:
                base_time *= 0.8  # 20% faster for sequential access
        return base_time

    def _update_stats(self, access_time):
        """Update latency statistics"""
        self._min_latency = min(self._min_latency, access_time)
        self._max_latency = max(self._max_latency, access_time)
        self._total_latency += access_time
        self._access_count += 1

    def get_exec_time(self):
        """Return total execution time"""
        return self._exec_time

    def debug_info(self):
        """Return detailed debug information about the main memory state"""
        info = super().debug_info()
        info.update({
            "data_size": len(self._data),
            "data": self._data,
            "memory_map": self._memory_map,
            "access_pattern": self._access_pattern
        })
        return info

    def print_debug_info(self):
        """Print formatted debug information about the main memory state"""
        info = self.debug_info()
        super().print_debug_info()
        self._logger.log(LogLevel.DEBUG, f"\nData Size: {info['data_size']} bytes")
        self._logger.log(LogLevel.DEBUG, "\nData Contents:")
        for addr, value in enumerate(info['data']):
            if value is not None:
                self._logger.log(LogLevel.DEBUG, f"  Address {addr}: {value}")

        self._logger.log(LogLevel.DEBUG, "\nMemory Map:")
        for addr, region in info['memory_map'].items():
            self._logger.log(LogLevel.DEBUG, f"  Address {addr}: {region}")

        self._logger.log(LogLevel.DEBUG, "\nAccess Pattern:")
        for pattern, count in info['access_pattern'].items():
            self._logger.log(LogLevel.DEBUG, f"  {pattern}: {count}")

    def validate_state(self):
        """Validate the main memory state and return any issues found"""
        issues = []

        # Check data array
        if not isinstance(self._data, list):
            issues.append("Data is not a list")
        else:
            # Check for None values
            none_count = sum(1 for value in self._data if value is None)
            if none_count > 0:
                issues.append(f"Found {none_count} None values in data array")

        # Check memory map consistency
        for addr in self._memory_map:
            if addr >= len(self._data):
                issues.append(f"Memory map contains address {addr} outside data range")

        return issues

    def get_memory_stats(self):
        """Return statistics about the main memory"""
        stats = super().get_performance_stats()
        stats.update({
            "used_addresses": sum(1 for value in self._data if value is not None),
            "free_addresses": sum(1 for value in self._data if value is None),
            "total_addresses": len(self._data),
            "mapped_regions": len(self._memory_map),
            "access_patterns": self._access_pattern
        })
        return stats
