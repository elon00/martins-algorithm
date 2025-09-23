from luther_algorithm import LuthersGoldenAlgorithm
import time

golden = LuthersGoldenAlgorithm()
print("=== LUTHER'S GOLDEN ALGORITHM PERFORMANCE VISUALIZATION ===")
print()

# Test different data sizes
sizes = [100, 1000, 10000, 50000, 100000]
results = []

print("Running benchmarks...")
for size in sizes:
    data = b'A' * size
    times = []
    for _ in range(5):  # 5 runs for averaging
        start = time.time()
        encrypted = golden.encrypt(data)
        decrypted = golden.decrypt(encrypted)
        end = time.time()
        times.append(end - start)
        assert data == decrypted

    avg_time = sum(times) / len(times)
    overhead = len(encrypted) - size
    results.append((size, avg_time, overhead))

print("\nPERFORMANCE RESULTS:")
print("=" * 60)
print("Data Size | Time (sec) | Overhead | Efficiency")
print("-" * 60)

for size, avg_time, overhead in results:
    efficiency = size / (size + overhead) * 100
    print(f"{size:8d} | {avg_time:.6f} | {overhead:8d} | {efficiency:.1f}%")

print("\nVISUALIZATION:")
print("=" * 60)

# Simple ASCII bar chart for time
max_time = max(r[1] for r in results)
for size, avg_time, _ in results:
    bar_length = int(avg_time / max_time * 40)
    bar = "#" * bar_length
    print(f"{size:8d} | {bar}")

print("\nSECURITY LEVEL:", golden.get_security_level())
print("POST-QUANTUM:", "Available" if golden.pq else "Not Available")
print("QUANTUM BOOST:", "Enabled" if golden.quantum_boost else "Disabled")
print("ENCRYPTION LAYERS:", golden.layers)

print("\n=== VISUALIZATION COMPLETE ===")