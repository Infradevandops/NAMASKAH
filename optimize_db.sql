
-- Database optimization queries
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = memory;
PRAGMA mmap_size = 268435456;

-- Analyze tables for query optimization
ANALYZE;

-- Vacuum to reclaim space
VACUUM;
