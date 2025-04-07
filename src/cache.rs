use std::collections::HashMap;

// Cache tags (6 bits) and indexes (2 bits)
pub const CACHE_ACCESS_COST: u32 = 2;

pub struct CacheBlock {
    pub tag: u8,
    pub data: u32,
    pub valid: bool,
    pub last_used: u64, // For LRU replacement policy
}

pub struct CacheSet {
    pub blocks: Vec<CacheBlock>,
    pub capacity: usize,
}

pub struct Cache {
    pub sets: HashMap<u8, CacheSet>,
    pub num_sets: usize,
    pub blocks_per_set: usize,
    pub access_counter: u64,
    pub hits: u32,
    pub misses: u32,
}

impl Cache {
    pub fn new(num_sets: usize, blocks_per_set: usize) -> Self {
        let mut sets = HashMap::new();
        for i in 0..num_sets {
            sets.insert(i as u8, CacheSet {
                blocks: Vec::with_capacity(blocks_per_set),
                capacity: blocks_per_set,
            });
        }
        
        Cache {
            sets,
            num_sets,
            blocks_per_set,
            access_counter: 0,
            hits: 0,
            misses: 0,
        }
    }
    
    // Extract tag and set index from memory address
    fn get_tag_and_set(&self, addr: u8) -> (u8, u8) {
        let set_idx = (addr % self.num_sets as u8) as u8;
        let tag = addr / self.num_sets as u8;
        (tag, set_idx)
    }
    
    // Read data from cache
    pub fn read(&mut self, addr: u8) -> (u32, bool) {
      self.access_counter += 1;
      let (tag, set_idx) = self.get_tag_and_set(addr);
      
      // Check if the set exists and has the block
      if let Some(set) = self.sets.get_mut(&set_idx) {
          for block in &mut set.blocks {
              if block.valid && block.tag == tag {
                  // Cache hit
                  block.last_used = self.access_counter;
                  self.hits += 1; // This line is crucial
                  println!("Cache HIT: Address 0x{:02X}, Tag 0x{:02X}, Set {}", addr, tag, set_idx);
                  return (block.data, true);
              }
          }
      }
      
      // Cache miss
      self.misses += 1; // This line is crucial
      println!("Cache MISS: Address 0x{:02X}, Tag 0x{:02X}, Set {}", addr, tag, set_idx);
      (0, false)
  }
    
    // Write data to cache
    pub fn write(&mut self, addr: u8, data: u32) {
        self.access_counter += 1;
        let (tag, set_idx) = self.get_tag_and_set(addr);
        
        // Get or create the set
        let set = self.sets.entry(set_idx).or_insert_with(|| {
            CacheSet {
                blocks: Vec::with_capacity(self.blocks_per_set),
                capacity: self.blocks_per_set,
            }
        });
        
        // Check if the block already exists
        for block in &mut set.blocks {
            if block.valid && block.tag == tag {
                // Update existing block
                block.data = data;
                block.last_used = self.access_counter;
                return;
            }
        }
        
        // Block doesn't exist, need to add or replace
        if set.blocks.len() < set.capacity {
            // Set has space, add a new block
            set.blocks.push(CacheBlock {
                tag,
                data,
                valid: true,
                last_used: self.access_counter,
            });
        } else {
            // Set is full, replace using LRU policy
            let mut lru_idx = 0;
            let mut min_last_used = u64::MAX;
            
            for (idx, block) in set.blocks.iter().enumerate() {
                if block.last_used < min_last_used {
                    min_last_used = block.last_used;
                    lru_idx = idx;
                }
            }
            
            // Replace the LRU block
            set.blocks[lru_idx] = CacheBlock {
                tag,
                data,
                valid: true,
                last_used: self.access_counter,
            };
        }
    }
    
    // Get hit rate
    pub fn get_hit_rate(&self) -> f32 {
        let total = self.hits + self.misses;
        if total > 0 {
            self.hits as f32 / total as f32
        } else {
            0.0
        }
    }
}