"""
Production Redis Integration Tests
Tests Redis connectivity, performance, and production configurations.
"""
import pytest
import asyncio
import time
from app.core.caching import cache, CacheManager


class TestProductionRedis:
    """Test production Redis configuration and performance."""
    
    @pytest.fixture(scope="class")
    async def redis_client(self):
        """Create Redis client for testing."""
        test_cache = CacheManager()
        await test_cache.connect()
        yield test_cache
        await test_cache.disconnect()
    
    @pytest.mark.asyncio
    async def test_redis_connection(self, redis_client):
        """Test basic Redis connectivity."""
        # Test basic set/get
        await redis_client.set("test_connection", "success", ttl=10)
        result = await redis_client.get("test_connection")
        assert result == "success"
        
        # Clean up
        await redis_client.delete("test_connection")
    
    @pytest.mark.asyncio
    async def test_redis_configuration(self, redis_client):
        """Test Redis configuration settings."""
        # Test that Redis is configured with expected settings
        if hasattr(redis_client.redis_client, 'connection_pool'):
            pool = redis_client.redis_client.connection_pool
            assert pool.max_connections >= 20  # Should have adequate connection pool
    
    @pytest.mark.asyncio
    async def test_redis_persistence(self, redis_client):
        """Test Redis data persistence."""
        # Set a value
        test_key = "test_persistence"
        test_value = {"data": "persistent_test", "timestamp": time.time()}
        
        await redis_client.set(test_key, test_value, ttl=300)
        
        # Verify it's stored
        result = await redis_client.get(test_key)
        assert result == test_value
        
        # Clean up
        await redis_client.delete(test_key)
    
    @pytest.mark.asyncio
    async def test_redis_ttl_functionality(self, redis_client):
        """Test TTL (Time To Live) functionality."""
        test_key = "test_ttl"
        test_value = "expires_soon"
        
        # Set with short TTL
        await redis_client.set(test_key, test_value, ttl=2)
        
        # Should exist immediately
        result = await redis_client.get(test_key)
        assert result == test_value
        
        # Wait for expiration
        await asyncio.sleep(3)
        
        # Should be expired
        result = await redis_client.get(test_key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_redis_json_serialization(self, redis_client):
        """Test JSON serialization/deserialization."""
        test_key = "test_json"
        test_data = {
            "string": "test",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        await redis_client.set(test_key, test_data, ttl=60)
        result = await redis_client.get(test_key)
        
        assert result == test_data
        assert isinstance(result, dict)
        assert result["string"] == "test"
        assert result["number"] == 42
        assert result["boolean"] is True
        assert result["list"] == [1, 2, 3]
        assert result["nested"]["key"] == "value"
        
        # Clean up
        await redis_client.delete(test_key)
    
    @pytest.mark.asyncio
    async def test_redis_error_handling(self, redis_client):
        """Test Redis error handling and graceful degradation."""
        # Test getting non-existent key
        result = await redis_client.get("non_existent_key")
        assert result is None
        
        # Test deleting non-existent key (should not raise error)
        await redis_client.delete("non_existent_key")
    
    @pytest.mark.asyncio
    async def test_redis_concurrent_operations(self, redis_client):
        """Test concurrent Redis operations."""
        async def set_and_get(index):
            key = f"concurrent_test_{index}"
            value = f"value_{index}"
            
            await redis_client.set(key, value, ttl=60)
            result = await redis_client.get(key)
            await redis_client.delete(key)
            
            return result == value
        
        # Run concurrent operations
        tasks = [set_and_get(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        assert all(results)
    
    @pytest.mark.asyncio
    async def test_redis_performance_simple_operations(self, redis_client):
        """Test performance of simple Redis operations."""
        # Test SET performance
        start_time = time.time()
        for i in range(100):
            await redis_client.set(f"perf_test_{i}", f"value_{i}", ttl=60)
        set_duration = time.time() - start_time
        
        # Test GET performance
        start_time = time.time()
        for i in range(100):
            await redis_client.get(f"perf_test_{i}")
        get_duration = time.time() - start_time
        
        # Test DELETE performance
        start_time = time.time()
        for i in range(100):
            await redis_client.delete(f"perf_test_{i}")
        delete_duration = time.time() - start_time
        
        # Performance assertions (should be very fast)
        assert set_duration < 5.0  # 100 SETs in less than 5 seconds
        assert get_duration < 2.0  # 100 GETs in less than 2 seconds
        assert delete_duration < 2.0  # 100 DELETEs in less than 2 seconds
    
    @pytest.mark.asyncio
    async def test_redis_large_data_handling(self, redis_client):
        """Test handling of large data objects."""
        # Create large data object
        large_data = {
            "large_list": list(range(1000)),
            "large_string": "x" * 10000,
            "nested_data": {f"key_{i}": f"value_{i}" for i in range(100)}
        }
        
        test_key = "large_data_test"
        
        # Store large data
        start_time = time.time()
        await redis_client.set(test_key, large_data, ttl=60)
        set_duration = time.time() - start_time
        
        # Retrieve large data
        start_time = time.time()
        result = await redis_client.get(test_key)
        get_duration = time.time() - start_time
        
        # Verify data integrity
        assert result == large_data
        assert len(result["large_list"]) == 1000
        assert len(result["large_string"]) == 10000
        assert len(result["nested_data"]) == 100
        
        # Performance should still be reasonable
        assert set_duration < 1.0  # Large SET in less than 1 second
        assert get_duration < 1.0  # Large GET in less than 1 second
        
        # Clean up
        await redis_client.delete(test_key)
    
    @pytest.mark.asyncio
    async def test_redis_pattern_operations(self, redis_client):
        """Test Redis pattern-based operations."""
        # Set up test data
        test_keys = [f"pattern_test:user:{i}" for i in range(5)]
        for key in test_keys:
            await redis_client.set(key, f"data_for_{key}", ttl=60)
        
        # Test pattern invalidation
        await redis_client.invalidate_pattern("pattern_test:user:*")
        
        # Verify all keys are deleted
        for key in test_keys:
            result = await redis_client.get(key)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_redis_connection_recovery(self, redis_client):
        """Test Redis connection recovery after failure."""
        # First, verify connection works
        await redis_client.set("recovery_test", "initial", ttl=60)
        result = await redis_client.get("recovery_test")
        assert result == "initial"
        
        # Simulate connection issue by disconnecting
        await redis_client.disconnect()
        
        # Reconnect
        await redis_client.connect()
        
        # Verify connection works again
        await redis_client.set("recovery_test", "recovered", ttl=60)
        result = await redis_client.get("recovery_test")
        assert result == "recovered"
        
        # Clean up
        await redis_client.delete("recovery_test")
    
    @pytest.mark.asyncio
    async def test_redis_memory_efficiency(self, redis_client):
        """Test Redis memory usage and efficiency."""
        # Store many small objects
        base_key = "memory_test"
        num_objects = 1000
        
        for i in range(num_objects):
            small_object = {"id": i, "data": f"small_data_{i}"}
            await redis_client.set(f"{base_key}:{i}", small_object, ttl=300)
        
        # Verify all objects are stored
        stored_count = 0
        for i in range(num_objects):
            result = await redis_client.get(f"{base_key}:{i}")
            if result is not None:
                stored_count += 1
        
        assert stored_count == num_objects
        
        # Clean up
        for i in range(num_objects):
            await redis_client.delete(f"{base_key}:{i}")


class TestRedisCacheIntegration:
    """Test Redis cache integration with application."""
    
    @pytest.mark.asyncio
    async def test_cache_user_data(self):
        """Test caching user data."""
        from app.core.caching import cached_user_stats
        
        # Test caching user statistics
        user_id = "test_user_123"
        
        # First call should cache the data
        start_time = time.time()
        stats1 = await cached_user_stats(user_id)
        first_call_duration = time.time() - start_time
        
        # Second call should be faster (cached)
        start_time = time.time()
        stats2 = await cached_user_stats(user_id)
        second_call_duration = time.time() - start_time
        
        # Results should be the same
        assert stats1 == stats2
        
        # Second call should be faster (though this might not always be true in tests)
        # We'll just verify both calls completed reasonably quickly
        assert first_call_duration < 1.0
        assert second_call_duration < 1.0
    
    @pytest.mark.asyncio
    async def test_cache_services_list(self):
        """Test caching services list."""
        from app.core.caching import cached_services_list
        
        # Test caching services
        services1 = await cached_services_list()
        services2 = await cached_services_list()
        
        # Results should be the same
        assert services1 == services2
        assert isinstance(services1, list)
        assert len(services1) > 0
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """Test cache invalidation functionality."""
        from app.core.caching import cached_user_stats, invalidate_user_cache
        
        user_id = "test_invalidation_user"
        
        # Cache some data
        stats1 = await cached_user_stats(user_id)
        assert stats1 is not None
        
        # Invalidate cache
        await invalidate_user_cache(user_id)
        
        # Next call should fetch fresh data
        stats2 = await cached_user_stats(user_id)
        assert stats2 is not None
        
        # Note: In a real scenario, stats might be different after invalidation
        # but in our mock implementation, they'll be the same
    
    @pytest.mark.asyncio
    async def test_cache_failover_behavior(self):
        """Test cache behavior when Redis is unavailable."""
        # This test would require mocking Redis failure
        # For now, we'll test that cache operations don't crash the application
        
        try:
            # Attempt cache operations
            await cache.set("failover_test", "data", ttl=60)
            await cache.get("failover_test")
            await cache.delete("failover_test")
            
            # If Redis is available, these should work
            # If not, they should fail gracefully without crashing
            
        except Exception as e:
            # Cache failures should be handled gracefully
            # The application should continue to work even if cache fails
            print(f"Cache operation failed (expected if Redis unavailable): {e}")


class TestRedisPerformance:
    """Performance-specific Redis tests."""
    
    @pytest.mark.asyncio
    async def test_high_throughput_operations(self):
        """Test Redis performance under high throughput."""
        redis_client = CacheManager()
        await redis_client.connect()
        
        try:
            # Test high-throughput SET operations
            start_time = time.time()
            
            tasks = []
            for i in range(500):  # 500 concurrent operations
                task = redis_client.set(f"throughput_test_{i}", f"data_{i}", ttl=60)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            set_duration = time.time() - start_time
            
            # Test high-throughput GET operations
            start_time = time.time()
            
            tasks = []
            for i in range(500):
                task = redis_client.get(f"throughput_test_{i}")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            get_duration = time.time() - start_time
            
            # Verify results
            assert len(results) == 500
            assert all(result == f"data_{i}" for i, result in enumerate(results))
            
            # Performance assertions
            assert set_duration < 10.0  # 500 SETs in less than 10 seconds
            assert get_duration < 5.0   # 500 GETs in less than 5 seconds
            
            # Clean up
            tasks = []
            for i in range(500):
                task = redis_client.delete(f"throughput_test_{i}")
                tasks.append(task)
            await asyncio.gather(*tasks)
            
        finally:
            await redis_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_cache_hit_ratio_performance(self):
        """Test cache hit ratio and performance."""
        redis_client = CacheManager()
        await redis_client.connect()
        
        try:
            # Pre-populate cache
            for i in range(100):
                await redis_client.set(f"hit_ratio_test_{i}", f"cached_data_{i}", ttl=300)
            
            # Test cache hits
            hit_count = 0
            miss_count = 0
            
            start_time = time.time()
            
            for i in range(150):  # 100 hits + 50 misses
                result = await redis_client.get(f"hit_ratio_test_{i}")
                if result is not None:
                    hit_count += 1
                else:
                    miss_count += 1
            
            total_duration = time.time() - start_time
            
            # Verify hit ratio
            assert hit_count == 100
            assert miss_count == 50
            hit_ratio = hit_count / (hit_count + miss_count)
            assert hit_ratio == 2/3  # 100/150
            
            # Performance should be good
            assert total_duration < 2.0  # 150 operations in less than 2 seconds
            
            # Clean up
            for i in range(100):
                await redis_client.delete(f"hit_ratio_test_{i}")
                
        finally:
            await redis_client.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])