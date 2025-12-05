"""
QuickAPI vs FastAPI Performance Comparison

Benchmark comparison between QuickAPI and FastAPI frameworks.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any

# Mock ASGI environment for testing
class MockASGIEnv:
    """Mock ASGI environment for testing"""
    
    def __init__(self):
        self.received = []
        self.sent = []
    
    async def receive(self):
        """Mock receive callable"""
        if not self.received:
            return {"type": "http.request", "body": b"", "more_body": False}
        else:
            return self.received.pop(0)
    
    async def send(self, message):
        """Mock send callable"""
        self.sent.append(message)


def run_benchmark(test_name: str, test_func, iterations: int = 1000) -> Dict[str, Any]:
    """Run a benchmark test"""
    print(f"Running {test_name}...")
    
    times = []
    
    for i in range(iterations):
        start_time = time.perf_counter()
        asyncio.run(test_func())
        end_time = time.perf_counter()
        
        elapsed = (end_time - start_time) * 1000  # Convert to milliseconds
        times.append(elapsed)
        
        if (i + 1) % 100 == 0:
            progress = (i + 1) / iterations * 100
            print(f"Progress: {progress:.0f}%")
    
    # Calculate statistics
    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    median_time = statistics.median(times)
    p95_time = sorted(times)[int(iterations * 0.95)]
    
    result = {
        "test_name": test_name,
        "iterations": iterations,
        "avg_ms": avg_time,
        "min_ms": min_time,
        "max_ms": max_time,
        "median_ms": median_time,
        "p95_ms": p95_time,
        "requests_per_second": 1000 / (avg_time / 1000) if avg_time > 0 else 0
    }
    
    print(f"✅ {test_name} completed")
    print(f"   Average: {avg_time:.2f}ms")
    print(f"   Median: {median_time:.2f}ms")
    print(f"   95th percentile: {p95_time:.2f}ms")
    print(f"   RPS: {result['requests_per_second']:.0f}")
    print()
    
    return result


async def test_quickapi_hello():
    """Test QuickAPI hello world"""
    from quickapi import QuickAPI, JSONResponse
    
    app = QuickAPI()
    
    @app.get("/")
    async def hello(request):
        return JSONResponse({"message": "Hello World"})
    
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 8000)
    }
    
    env = MockASGIEnv()
    await app(scope, env.receive, env.send)


async def test_fastapi_hello():
    """Test FastAPI hello world"""
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    
    @app.get("/")
    async def hello():
        return JSONResponse({"message": "Hello World"})
    
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 8000),
        "server": ("127.0.0.1", 8000),
        "scheme": "http",
        "root_path": "",
        "http_version": "1.1",
    }
    
    env = MockASGIEnv()
    await app(scope, env.receive, env.send)


async def test_quickapi_json():
    """Test QuickAPI JSON response"""
    from quickapi import QuickAPI, JSONResponse
    
    app = QuickAPI()
    
    @app.get("/data")
    async def get_data(request):
        return JSONResponse({
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
                {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
            ],
            "total": 3,
            "page": 1
        })
    
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/data",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 8000)
    }
    
    env = MockASGIEnv()
    await app(scope, env.receive, env.send)


async def test_fastapi_json():
    """Test FastAPI JSON response"""
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    
    @app.get("/data")
    async def get_data():
        return JSONResponse({
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
                {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
            ],
            "total": 3,
            "page": 1
        })
    
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/data",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 8000),
        "server": ("127.0.0.1", 8000),
        "scheme": "http",
        "root_path": "",
        "http_version": "1.1",
    }
    
    env = MockASGIEnv()
    await app(scope, env.receive, env.send)


def run_comparison():
    """Run comparison benchmarks"""
    print("🚀 QuickAPI vs FastAPI Performance Comparison")
    print("=" * 60)
    print()
    
    results = {}
    
    # QuickAPI benchmarks
    print("📦 QuickAPI Benchmarks")
    print("-" * 60)
    results['quickapi_hello'] = run_benchmark("QuickAPI Hello World", test_quickapi_hello, iterations=500)
    results['quickapi_json'] = run_benchmark("QuickAPI JSON Response", test_quickapi_json, iterations=500)
    
    # FastAPI benchmarks
    print("📦 FastAPI Benchmarks")
    print("-" * 60)
    results['fastapi_hello'] = run_benchmark("FastAPI Hello World", test_fastapi_hello, iterations=500)
    results['fastapi_json'] = run_benchmark("FastAPI JSON Response", test_fastapi_json, iterations=500)
    
    # Comparison
    print("=" * 60)
    print("📊 Performance Comparison")
    print("=" * 60)
    print()
    
    print("Hello World Endpoint:")
    quickapi_hello_avg = results['quickapi_hello']['avg_ms']
    fastapi_hello_avg = results['fastapi_hello']['avg_ms']
    speedup = fastapi_hello_avg / quickapi_hello_avg if quickapi_hello_avg > 0 else 0
    print(f"  QuickAPI: {quickapi_hello_avg:.2f}ms")
    print(f"  FastAPI:  {fastapi_hello_avg:.2f}ms")
    print(f"  Speedup:  {speedup:.2f}x {'faster' if speedup > 1 else 'slower'}")
    print()
    
    print("JSON Response Endpoint:")
    quickapi_json_avg = results['quickapi_json']['avg_ms']
    fastapi_json_avg = results['fastapi_json']['avg_ms']
    speedup = fastapi_json_avg / quickapi_json_avg if quickapi_json_avg > 0 else 0
    print(f"  QuickAPI: {quickapi_json_avg:.2f}ms")
    print(f"  FastAPI:  {fastapi_json_avg:.2f}ms")
    print(f"  Speedup:  {speedup:.2f}x {'faster' if speedup > 1 else 'slower'}")
    print()
    
    # Overall winner
    quickapi_total = quickapi_hello_avg + quickapi_json_avg
    fastapi_total = fastapi_hello_avg + fastapi_json_avg
    
    print("Overall Performance:")
    print(f"  QuickAPI Total: {quickapi_total:.2f}ms")
    print(f"  FastAPI Total:  {fastapi_total:.2f}ms")
    
    if quickapi_total < fastapi_total:
        speedup = fastapi_total / quickapi_total
        print(f"  🏆 QuickAPI is {speedup:.2f}x faster overall!")
    else:
        speedup = quickapi_total / fastapi_total
        print(f"  FastAPI is {speedup:.2f}x faster overall")
    
    print()
    return results


if __name__ == "__main__":
    run_comparison()
