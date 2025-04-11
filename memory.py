from time import sleep
from colorama import Fore, Style

# Memory class used to create different
# memory types within the simulation
class Memory():
    def __init__(self, name="", access_time=0):
        self._name = name
        self._access_time = access_time
        self._exec_time = 0
        # New attributes
        self._bandwidth = 0  # Track memory bandwidth usage
        self._latency_stats = {
            "min": float('inf'),
            "max": 0,
            "total": 0,
            "count": 0
        }

    # Accessors
    @property
    def name(self):
        return self._name

    @property
    def access_time(self):
        return self._access_time

    @property
    def exec_time(self):
        return self._exec_time

    # Mutators
    @name.setter
    def name(self, value):
        self._name = value

    @access_time.setter
    def access_time(self, value):
        if value >= 0:
            self._access_time = value
        else:
            raise ValueError("Access time must be non-negative")

    # Output read message and update
    # process execution time
    def read(self, output=True):
        if output:
            print(f" - {self._name} read: ", end="")
        self._exec_time += self._access_time

    # Output write message and update
    # process execution time
    def write(self, output=True):
        if output:
            print(f" - {self._name} write: ", end="")
        self._exec_time += self._access_time

    # placeholder method
    def get_exec_time(self):
        return 0

    # Debugging methods
    def debug_info(self):
        """Return detailed debug information about the memory state"""
        info = {
            "name": self._name,
            "access_time": self._access_time,
            "exec_time": self._exec_time,
            "type": self.__class__.__name__,
            "bandwidth": self._bandwidth,
            "latency_stats": self._latency_stats
        }
        return info

    def print_debug_info(self):
        """Print formatted debug information about the memory state"""
        info = self.debug_info()
        print(f"\n{Fore.CYAN}=== Memory Debug Info: {self._name} ==={Style.RESET_ALL}")
        print(f"Type: {info['type']}")
        print(f"Access Time: {info['access_time']} ns")
        print(f"Execution Time: {info['exec_time']} ns")
        print(f"Bandwidth: {info['bandwidth']} bytes/ns")
        print("\nLatency Statistics:")
        print(f"  Minimum: {info['latency_stats']['min']} ns")
        print(f"  Maximum: {info['latency_stats']['max']} ns")
        print(f"  Average: {info['latency_stats']['total'] / info['latency_stats']['count'] if info['latency_stats']['count'] > 0 else 0} ns")
        print(f"  Total Operations: {info['latency_stats']['count']}")

    def validate_state(self):
        """Validate the memory state and return any issues found"""
        issues = []

        # Check access time
        if self._access_time < 0:
            issues.append(f"Invalid access time: {self._access_time}")

        # Check execution time
        if self._exec_time < 0:
            issues.append(f"Invalid execution time: {self._exec_time}")

        # Check bandwidth
        if self._bandwidth < 0:
            issues.append(f"Invalid bandwidth: {self._bandwidth}")

        # Check latency stats
        if self._latency_stats["min"] > self._latency_stats["max"]:
            issues.append("Invalid latency statistics: min > max")
        if self._latency_stats["count"] < 0:
            issues.append("Invalid latency count")

        return issues

    def get_performance_stats(self):
        """Return performance statistics for the memory"""
        stats = {
            "total_accesses": self._exec_time / self._access_time if self._access_time > 0 else 0,
            "total_time": self._exec_time,
            "average_access_time": self._access_time,
            "bandwidth_usage": self._bandwidth,
            "latency": {
                "min": self._latency_stats["min"],
                "max": self._latency_stats["max"],
                "average": self._latency_stats["total"] / self._latency_stats["count"] if self._latency_stats["count"] > 0 else 0,
                "total_operations": self._latency_stats["count"]
            }
        }
        return stats

# Memory class used for the main
# memory data storage
class MainMemory(Memory):
    def __init__(self):
        super().__init__(name="MainMemory", access_time=100)
        self._data = [None] * 1000
        # New attributes
        self._memory_map = {}  # Track which addresses are mapped to which regions
        self._access_pattern = {
            "sequential": 0,
            "random": 0,
            "repeated": 0
        }

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
        data = self._data[address]
        super().read()
        return data

    # Write data to main memory address
    def write(self, address, data):
        self._data[address] = data
        super().write()

    # Return total execution time
    def get_exec_time(self):
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
        print(f"\nData Size: {info['data_size']} bytes")
        print("\nData Contents:")
        for addr, value in enumerate(info['data']):
            if value is not None:
                print(f"  Address {addr}: {value}")

        print("\nMemory Map:")
        for addr, region in info['memory_map'].items():
            print(f"  Address {addr}: {region}")

        print("\nAccess Pattern:")
        for pattern, count in info['access_pattern'].items():
            print(f"  {pattern}: {count}")

    def validate_state(self):
        """Validate the main memory state and return any issues found"""
        issues = super().validate_state()

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
