import random

class ReplacementPolicy:
    @staticmethod
    def random(cache, address):
        """Random replacement policy"""
        index = random.randint(0, len(cache.entries) - 1)
        cache.entries[index] = {"address": address, "data": None, "dirty": False}
        return index

    @staticmethod
    def fifo(cache, address):
        """First-in First-out replacement policy"""
        cache.entries.pop(0)
        cache.entries.append({"address": address, "data": None, "dirty": False})
        if cache.policy == "lru":
            cache.lru_order.pop(0)
            cache.lru_order.append(cache.entries[-1])
        return len(cache.entries) - 1

    @staticmethod
    def lru(cache, address):
        """Least Recently Used replacement policy"""
        lru_entry = cache.lru_order.pop(0)
        for i, entry in enumerate(cache.entries):
            if entry == lru_entry:
                cache.entries[i] = {"address": address, "data": None, "dirty": False}
                cache.lru_order.append(cache.entries[i])
                return i
        return None
