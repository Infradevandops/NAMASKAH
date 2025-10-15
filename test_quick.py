"""Quick test to verify the app works"""
import sys

try:
    # Test imports
    print("Testing imports...")
    import main
    from fastapi.testclient import TestClient
    
    # Create test client
    print("Creating test client...")
    client = TestClient(main.app)
    
    # Test health endpoint
    print("Testing /health endpoint...")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")
    
    # Test root endpoint
    print("Testing / endpoint...")
    response = client.get("/")
    assert response.status_code == 200
    print("✅ Root endpoint passed")
    
    # Test API docs
    print("Testing /docs endpoint...")
    response = client.get("/docs")
    assert response.status_code == 200
    print("✅ API docs passed")
    
    print("\n🎉 All tests passed! App is ready to use.")
    print("Run: ./start.sh")
    print("Visit: http://localhost:8000")
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    sys.exit(1)
