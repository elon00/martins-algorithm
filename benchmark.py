from luther_algorithm import LuthersGoldenAlgorithm
import time

golden = LuthersGoldenAlgorithm()
print("Benchmarking Luther's Golden Algorithm...")

data_sizes = [1000, 10000, 100000]

for size in data_sizes:
    data = b'A' * size
    start = time.time()
    for _ in range(10):
        encrypted = golden.encrypt(data)
        decrypted = golden.decrypt(encrypted)
        assert data == decrypted
    end = time.time()
    avg_time = (end - start) / 10
    print(f"Size {size} bytes: {avg_time:.4f} seconds per operation")

print("Benchmark complete!")