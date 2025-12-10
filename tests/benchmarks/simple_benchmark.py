"""
Simple benchmark comparing QuickAPI, FastAPI, and Flask
"""
import subprocess
import time
import sys
import asyncio
import httpx
from pathlib import Path


def create_test_apps():
    """Create test applications"""
    
    # QuickAPI app
    quickapi_code = '''
import sys
sys.path.insert(0, '..')
from quickapi import QuickAPI, JSONResponse

app = QuickAPI(title="Benchmark", docs=False)

@app.get("/")
async def root(request):
    return JSONResponse({"message": "Hello World"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")
'''
    
    # FastAPI app
    fastapi_code = '''
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(docs_url=None, redoc_url=None)

@app.get("/")
async def root():
    return JSONResponse({"message": "Hello World"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="error")
'''
    
    # Flask app
    flask_code = '''
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def root():
    return jsonify({"message": "Hello World"})

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="127.0.0.1", port=8003, threads=4)
'''
    
    Path('_quickapi_test.py').write_text(quickapi_code)
    Path('_fastapi_test.py').write_text(fastapi_code)
    Path('_flask_test.py').write_text(flask_code)


async def benchmark_endpoint(url, num_requests=5000, concurrency=50):
    """Benchmark a single endpoint with controlled concurrency"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        semaphore = asyncio.Semaphore(concurrency)
        
        async def make_request():
            async with semaphore:
                try:
                    response = await client.get(url)
                    return response.status_code == 200
                except:
                    return False
        
        start_time = time.perf_counter()
        
        tasks = [make_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.perf_counter() - start_time
        
        successful = sum(1 for r in results if r)
        failed = num_requests - successful
        
        if successful > 0:
            rps = successful / elapsed
            avg_ms = (elapsed / successful) * 1000
            return {
                'total': num_requests,
                'successful': successful,
                'failed': failed,
                'elapsed': elapsed,
                'rps': rps,
                'avg_ms': avg_ms
            }
        return None


def test_framework(name, port, script):
    """Test a single framework"""
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print(f"{'='*60}")
    
    # Start server
    proc = subprocess.Popen(
        [sys.executable, script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd='.'
    )
    
    # Wait for server to start
    print(f"Starting {name} server...")
    time.sleep(3)
    
    # Check if server is running
    url = f"http://127.0.0.1:{port}/"
    try:
        import requests
        for _ in range(10):
            try:
                r = requests.get(url, timeout=1)
                if r.status_code == 200:
                    print(f"✅ {name} is ready")
                    break
            except:
                time.sleep(0.5)
        else:
            print(f"❌ {name} failed to start")
            proc.terminate()
            return None
        
        # Run benchmark
        print(f"Running benchmark (5000 requests, 50 concurrent)...")
        result = asyncio.run(benchmark_endpoint(url, 5000, 50))
        
        if result:
            print(f"  Successful: {result['successful']}/{result['total']}")
            print(f"  Failed: {result['failed']}")
            print(f"  Total time: {result['elapsed']:.2f}s")
            print(f"  Requests/sec: {result['rps']:.0f}")
            print(f"  Avg latency: {result['avg_ms']:.2f}ms")
        
        proc.terminate()
        proc.wait()
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        proc.terminate()
        proc.wait()
        return None


def main():
    print("🚀 QuickAPI vs FastAPI vs Flask Benchmark")
    print("="*60)
    
    # Install dependencies
    try:
        import httpx
    except ImportError:
        print("Installing httpx...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "httpx"])
    
    try:
        import flask
    except ImportError:
        print("Installing flask and waitress...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "flask", "waitress"])
    
    # Create test apps
    print("\nCreating test applications...")
    create_test_apps()
    print("✅ Test apps created")
    
    # Run benchmarks
    results = {}
    results['QuickAPI'] = test_framework('QuickAPI', 8001, '_quickapi_test.py')
    results['FastAPI'] = test_framework('FastAPI', 8002, '_fastapi_test.py')
    results['Flask'] = test_framework('Flask', 8003, '_flask_test.py')
    
    # Print comparison
    print("\n" + "="*60)
    print("📊 RESULTS COMPARISON")
    print("="*60)
    
    valid_results = {k: v for k, v in results.items() if v is not None}
    
    if valid_results:
        print("\n| Framework | RPS    | Avg Latency (ms) | Success Rate |")
        print("|-----------|--------|------------------|--------------|")
        
        for name, result in valid_results.items():
            success_rate = (result['successful'] / result['total']) * 100
            print(f"| {name:9} | {result['rps']:6.0f} | {result['avg_ms']:16.2f} | {success_rate:11.1f}% |")
        
        # Find winner
        winner = max(valid_results.items(), key=lambda x: x[1]['rps'])
        print(f"\n🥇 Winner: {winner[0]} with {winner[1]['rps']:.0f} requests/second")
        
        # Calculate speedup
        if 'QuickAPI' in valid_results and 'FastAPI' in valid_results:
            speedup = valid_results['QuickAPI']['rps'] / valid_results['FastAPI']['rps']
            print(f"   QuickAPI is {speedup:.2f}x {'faster' if speedup > 1 else 'slower'} than FastAPI")
        
        if 'QuickAPI' in valid_results and 'Flask' in valid_results:
            speedup = valid_results['QuickAPI']['rps'] / valid_results['Flask']['rps']
            print(f"   QuickAPI is {speedup:.2f}x {'faster' if speedup > 1 else 'slower'} than Flask")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    Path('_quickapi_test.py').unlink(missing_ok=True)
    Path('_fastapi_test.py').unlink(missing_ok=True)
    Path('_flask_test.py').unlink(missing_ok=True)
    print("✅ Done!")


if __name__ == "__main__":
    main()
