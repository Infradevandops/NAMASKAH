"""
Production Database Integration Tests
Tests database connectivity, performance, and production configurations.
"""
import pytest
import asyncio
import time
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


class TestProductionDatabase:
    """Test production database configuration and performance."""
    
    @pytest.fixture(scope="class")
    def db_engine(self):
        """Create test database engine with production settings."""
        if "sqlite" in settings.database_url:
            pytest.skip("Production database tests require PostgreSQL")
        
        test_engine = create_engine(
            settings.database_url,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        yield test_engine
        test_engine.dispose()
    
    @pytest.fixture
    def db_session(self, db_engine):
        """Create database session for testing."""
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    @staticmethod
    def test_database_connection(db_engine):
        """Test basic database connectivity."""
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    @staticmethod
    def test_connection_pool_configuration(db_engine):
        """Test connection pool is properly configured."""
        pool = db_engine.pool
        assert pool.size() == 20  # pool_size
        assert pool._max_overflow == 30  # max_overflow
        assert pool._pre_ping is True
        assert pool._recycle == 3600
    
    @staticmethod
    def test_concurrent_connections(db_engine):
        """Test handling of concurrent database connections."""
        def create_connection():
            with db_engine.connect() as conn:
                result = conn.execute(text("SELECT pg_sleep(0.1), 1"))
                return result.scalar()
        
        # Test multiple concurrent connections
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_connection) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        assert len(results) == 10
        assert all(result == 1 for result in results)
    
    @staticmethod
    def test_connection_pool_exhaustion_handling(db_engine):
        """Test behavior when connection pool is exhausted."""
        connections = []
        
        try:
            # Create connections up to pool limit
            for _ in range(25):  # pool_size + some overflow
                conn = db_engine.connect()
                connections.append(conn)
            
            # This should still work due to overflow
            with db_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
                
        finally:
            # Clean up connections
            for conn in connections:
                conn.close()
    
    @staticmethod
    def test_database_performance_simple_query(db_session):
        """Test simple query performance."""
        start_time = time.time()
        
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        
        duration = time.time() - start_time
        assert duration < 0.1  # Should complete in less than 100ms
    
    @staticmethod
    def test_database_performance_complex_query(db_session):
        """Test complex query performance."""
        start_time = time.time()
        
        # Test a more complex query
        query = text("""
            SELECT 
                COUNT(*) as total,
                AVG(EXTRACT(EPOCH FROM created_at)) as avg_timestamp
            FROM users 
            WHERE created_at > NOW() - INTERVAL '30 days'
        """)
        
        result = db_session.execute(query)
        row = result.fetchone()
        
        duration = time.time() - start_time
        assert duration < 1.0  # Should complete in less than 1 second
        assert row is not None
    
    @staticmethod
    def test_transaction_handling(db_session):
        """Test transaction handling and rollback."""
        # Start transaction
        db_session.begin()
        
        try:
            # Create a test user
            test_user = User(
                email="test_transaction@example.com",
                username="test_transaction",
                password_hash="test_hash"
            )
            db_session.add(test_user)
            db_session.flush()  # Get ID without committing
            
            user_id = test_user.id
            assert user_id is not None
            
            # Rollback transaction
            db_session.rollback()
            
            # Verify user was not actually saved
            user_check = db_session.query(User).filter(User.id == user_id).first()
            assert user_check is None
            
        except Exception:
            db_session.rollback()
            raise
    
    @staticmethod
    def test_connection_recovery_after_failure(db_engine):
        """Test connection recovery after database failure simulation."""
        # First, establish that connection works
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        
        # Simulate connection failure by trying invalid query
        try:
            with db_engine.connect() as conn:
                conn.execute(text("SELECT * FROM nonexistent_table"))
        except Exception:
            pass  # Expected to fail
        
        # Verify connection recovery
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    @staticmethod
    def test_database_schema_validation(db_session):
        """Test that required database schema exists."""
        # Check that main tables exist
        tables_to_check = ['users', 'verifications', 'transactions', 'api_keys']
        
        for table_name in tables_to_check:
            query = text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                )
            """)
            result = db_session.execute(query)
            exists = result.scalar()
            assert exists, f"Table {table_name} does not exist"
    
    @staticmethod
    def test_database_indexes_exist(db_session):
        """Test that important database indexes exist."""
        # Check for important indexes
        index_queries = [
            "SELECT indexname FROM pg_indexes WHERE tablename = 'users' AND indexname LIKE '%email%'",
            "SELECT indexname FROM pg_indexes WHERE tablename = 'verifications' AND indexname LIKE '%user_id%'",
        ]
        
        for query in index_queries:
            result = db_session.execute(text(query))
            indexes = result.fetchall()
            assert len(indexes) > 0, f"No indexes found for query: {query}"
    
    @staticmethod
    def test_database_constraints(db_session):
        """Test database constraints are properly enforced."""
        # Test unique constraint on email
        user1 = User(
            email="constraint_test@example.com",
            username="constraint_test1",
            password_hash="test_hash"
        )
        db_session.add(user1)
        db_session.commit()
        
        # Try to create another user with same email
        user2 = User(
            email="constraint_test@example.com",  # Same email
            username="constraint_test2",
            password_hash="test_hash"
        )
        db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()
        
        db_session.rollback()
        
        # Clean up
        db_session.delete(user1)
        db_session.commit()
    
    @staticmethod
    def test_connection_timeout_handling(db_engine):
        """Test connection timeout handling."""
        start_time = time.time()
        
        try:
            with db_engine.connect() as conn:
                # Set a short statement timeout
                conn.execute(text("SET statement_timeout = '1s'"))
                
                # Try a long-running query (should timeout)
                conn.execute(text("SELECT pg_sleep(2)"))
                
        except Exception as e:
            # Should timeout within reasonable time
            duration = time.time() - start_time
            assert duration < 5.0  # Should timeout quickly
            assert "timeout" in str(e).lower() or "cancel" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_async_database_operations(self):
        """Test asynchronous database operations."""
        async def async_query():
            try:
                db = next(get_db())
            except StopIteration:
                return
            try:
                # Simulate async database operation
                await asyncio.sleep(0.01)  # Simulate async work
                result = db.execute(text("SELECT 1"))
                return result.scalar()
            finally:
                db.close()
        
        # Run multiple async operations
        tasks = [async_query() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(result == 1 for result in results)
    
    @staticmethod
    def test_database_migration_state(db_session):
        """Test that database is in expected migration state."""
        # Check alembic version table exists
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'alembic_version'
            )
        """)
        result = db_session.execute(query)
        assert result.scalar(), "Alembic version table not found"
        
        # Check that we have a current version
        version_query = text("SELECT version_num FROM alembic_version")
        result = db_session.execute(version_query)
        version = result.scalar()
        assert version is not None, "No migration version found"
        assert len(version) > 0, "Empty migration version"


class TestDatabasePerformance:
    """Performance-specific database tests."""
    
    @pytest.fixture
    def db_session(self):
        """Create database session for performance testing."""
        try:
            db = next(get_db())
        except StopIteration:
            return
        try:
            yield db
        finally:
            db.close()
    
    @staticmethod
    def test_bulk_insert_performance(db_session):
        """Test bulk insert performance."""
        start_time = time.time()
        
        # Create multiple users in bulk
        users = []
        for i in range(100):
            user = User(
                email=f"bulk_test_{i}@example.com",
                username=f"bulk_test_{i}",
                password_hash="test_hash"
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        duration = time.time() - start_time
        assert duration < 5.0  # Should complete in less than 5 seconds
        
        # Clean up
        for user in users:
            db_session.delete(user)
        db_session.commit()
    
    @staticmethod
    def test_query_with_joins_performance(db_session):
        """Test performance of queries with joins."""
        start_time = time.time()
        
        # Query with joins
        query = text("""
            SELECT u.id, u.email, COUNT(v.id) as verification_count
            FROM users u
            LEFT JOIN verifications v ON u.id = v.user_id
            GROUP BY u.id, u.email
            LIMIT 100
        """)
        
        result = db_session.execute(query)
        _ = result.fetchall()
        
        duration = time.time() - start_time
        assert duration < 2.0  # Should complete in less than 2 seconds
    
    @staticmethod
    def test_concurrent_read_performance(db_session):
        """Test concurrent read performance."""
        def read_operation():
            try:
                db = next(get_db())
            except StopIteration:
                return
            try:
                start_time = time.time()
                result = db.execute(text("SELECT COUNT(*) FROM users"))
                count = result.scalar()
                duration = time.time() - start_time
                return duration, count
            finally:
                db.close()
        
        # Run concurrent reads
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(read_operation) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Check that all operations completed reasonably quickly
        durations = [result[0] for result in results]
        avg_duration = sum(durations) / len(durations)
        assert avg_duration < 1.0  # Average should be less than 1 second
        assert max(durations) < 3.0  # No single operation should take more than 3 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])