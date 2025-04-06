use std::collections::VecDeque;

pub const CACHE_ACCESS_COST: u32 = 1;

#[derive(Clone)]
pub struct CacheBlock {
    pub tag: u8,
    pub value: u32,
    pub dirty: bool,
    pub last_used: u64,
}

pub struct CacheSet {
    pub blocks: VecDeque<CacheBlock>, // 2-way set associativity
    pub capacity: usize,
}

impl CacheSet {
    pub fn new(capacity: usize) -> Self {
        CacheSet {
            blocks: VecDeque::with_capacity(capacity),
            capacity,
        }
    }

    pub fn get(&mut self, tag: u8, current_cycle: u64) -> Option<u32> {
        for block in self.blocks.iter_mut() {
            if block.tag == tag {
                block.last_used = current_cycle;
                return Some(block.value);
            }
        }
        None
    }

    pub fn insert(&mut self, tag: u8, value: u32, current_cycle: u64) -> Option<CacheBlock> {
        // Check if already in cache and update
        for block in self.blocks.iter_mut() {
            if block.tag == tag {
                block.value = value;
                block.dirty = true;
                block.last_used = current_cycle;
                return None;
            }
        }

        // If not in cache, insert
        if self.blocks.len() >= self.capacity {
            // LRU eviction: remove the block with the oldest `last_used`
            let lru_index = self
                .blocks
                .iter()
                .enumerate()
                .min_by_key(|(_, block)| block.last_used)
                .map(|(idx, _)| idx)
                .unwrap();

            let evicted = self.blocks.remove(lru_index).unwrap();
            self.blocks.push_back(CacheBlock {
                tag,
                value,
                dirty: true,
                last_used: current_cycle,
            });
            return Some(evicted);
        } else {
            self.blocks.push_back(CacheBlock {
                tag,
                value,
                dirty: true,
                last_used: current_cycle,
            });
            return None;
        }
    }
}

pub struct Cache {
    pub sets: Vec<CacheSet>,
    pub num_sets: usize,
    pub associativity: usize,
}

impl Cache {
    pub fn new(num_sets: usize, associativity: usize) -> Self {
        let mut sets = Vec::new();
        for _ in 0..num_sets {
            sets.push(CacheSet::new(associativity));
        }
        Cache {
            sets,
            num_sets,
            associativity,
        }
    }

    pub fn access(&mut self, address: u8, current_cycle: u64) -> Option<u32> {
        let set_index = address as usize % self.num_sets;
        let tag = address / self.num_sets as u8;
        self.sets[set_index].get(tag, current_cycle)
    }

    pub fn write(&mut self, address: u8, value: u32, current_cycle: u64) -> Option<CacheBlock> {
        let set_index = address as usize % self.num_sets;
        let tag = address / self.num_sets as u8;
        self.sets[set_index].insert(tag, value, current_cycle)
    }
}
