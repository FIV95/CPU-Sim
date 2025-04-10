from .policies import ReplacementPolicy
from utils.logger import CacheLogger

class Cache:
    def __init__(self, name, size, block_size, policy, access_time, next_level=None, logger=None):
        self.name = name
        self.size = size
        self.block_size = block_size
        self.policy = policy
        self.access_time = access_time
        self.exec_time = 0
        self.entries = []
        self.lru_order = []  # Track order of access for LRU policy
        self.next_level = next_level  # Next level of memory (Cache or MainMemory)
        self.policies = {
            "random": ReplacementPolicy.random,
            "fifo": ReplacementPolicy.fifo,
            "lru": ReplacementPolicy.lru
        }
        self.logger = logger

    def write(self, address, data):
        """Write data to cache and handle cache misses"""
        self.exec_time += self.access_time
        entry = self.get_entry(address)

        if entry is not None:
            entry["data"] = data
            entry["dirty"] = True
            if self.policy == "lru":
                self.lru_order.remove(entry)
                self.lru_order.append(entry)
            if self.logger:
                self.logger.log_cache_write(self.name, hit=True, data=data)
        else:
            if self.logger:
                self.logger.log_cache_write(self.name, hit=False, data=data)
            if len(self.entries) >= self.size:
                self.replace_entry(address)
            else:
                self.entries.append({"address": address, "data": data, "dirty": True})
                if self.policy == "lru":
                    self.lru_order.append(self.entries[-1])

        # Write through to next level
        if self.next_level:
            self.next_level.write(address, data)

    def read(self, address):
        """Read data from cache and handle cache misses"""
        self.exec_time += self.access_time
        entry = self.get_entry(address)

        if entry is not None:
            if self.policy == "lru":
                self.lru_order.remove(entry)
                self.lru_order.append(entry)
            if self.logger:
                self.logger.log_cache_read(self.name, hit=True, data=entry["data"])
            return entry["data"]
        else:
            if self.logger:
                self.logger.log_cache_read(self.name, hit=False)
            if len(self.entries) >= self.size:
                self.replace_entry(address)
            else:
                self.entries.append({"address": address, "data": None, "dirty": False})
                if self.policy == "lru":
                    self.lru_order.append(self.entries[-1])

            # Read from next level
            data = None
            if self.next_level:
                data = self.next_level.read(address)
                self.entries[-1]["data"] = data
                if self.logger:
                    self.logger.log_cache_read(self.name, hit=False, data=data)
            return data

    def replace_entry(self, address):
        """Replace a cache entry using the specified policy"""
        if self.policy in self.policies:
            # Write back dirty data before replacement
            old_entry = self.entries[0] if self.policy == "fifo" else self.lru_order[0]
            if old_entry.get("dirty", False) and self.next_level:
                self.next_level.write(old_entry["address"], old_entry["data"])

            # Apply replacement policy
            self.policies[self.policy](self, address)

    def get_entry(self, address):
        """Get cache entry for given address"""
        for entry in self.entries:
            if entry["address"] == address:
                return entry
        return None

    def get_exec_time(self):
        """Get total execution time including next level memory"""
        total_time = self.exec_time
        if self.next_level:
            total_time += self.next_level.get_exec_time()
        return total_time
