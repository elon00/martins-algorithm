#!/usr/bin/env python3
"""
Advanced usage example for Luther's Golden Algorithm
Demonstrates performance benchmarking and large-scale operations
"""

import time
import os
from luther_algorithm import LuthersAlgorithm

def benchmark_performance():
    """Benchmark encryption/decryption performance"""
    print("Performance Benchmark - Luther's Golden Algorithm")
    print("=" * 60)

    golden = LuthersGoldenAlgorithm()
    sizes = [1000, 10000, 100000, 1000000]  # 1KB to 1MB

    for size in sizes:
        data = b"A" * size

        # Benchmark encryption
        start_time = time.time()
        for _ in range(10):
            encrypted = golden.encrypt(data)
        enc_time = (time.time() - start_time) / 10

        # Benchmark decryption
        start_time = time.time()
        for _ in range(10):
            decrypted = golden.decrypt(encrypted)
        dec_time = (time.time() - start_time) / 10

        print("2d"
              "6.4f"
              "6.4f"
              ".1f")

def demonstrate_security_features():
    """Demonstrate various advanced security features"""
    print("\nAdvanced Security Features Demonstration")
    print("=" * 50)

    golden = LuthersGoldenAlgorithm()

    # 1. AI-driven adaptive encryption
    print("1. AI-Driven Adaptive Encryption:")
    small_data = b"Small message"
    large_data = b"A" * 500000  # 500KB

    enc_small = golden.encrypt(small_data, adaptive=True)
    enc_large = golden.encrypt(large_data, adaptive=True)

    print(f"   Small data ({len(small_data)} bytes) -> {len(enc_small)} bytes")
    print(f"   Large data ({len(large_data)} bytes) -> {len(enc_large)} bytes")
    print(f"   AI selected mode for large data: {golden.performance_metrics.get('last_encryption_mode', 'unknown')}")

    # 2. Multi-algorithm digital signatures
    print("\n2. Multi-Algorithm Post-Quantum Signatures:")
    message = b"Critical security message"

    # Single algorithm signature
    signature = golden.sign(message, 'dilithium')
    verified = golden.verify(message, signature, 'dilithium')
    print(f"   Dilithium signature: {len(signature)} bytes, verified: {verified}")

    # Multi-algorithm signatures
    try:
        signatures = golden.sign_multiple(message, ['dilithium'])
        verification = golden.verify_multiple(message, signatures)
        print(f"   Multi-algorithm signatures: {list(signatures.keys())}")
        print(f"   All verified: {all(verification.values())}")
    except Exception as e:
        print(f"   Multi-algorithm demo skipped: {e}")

    # 3. Homomorphic encryption
    print("\n3. Homomorphic Encryption (Privacy-Preserving Computation):")
    try:
        data1 = [1.5, 2.3, 3.1]
        data2 = [0.5, 1.7, 2.9]

        enc1 = golden.homomorphic_encrypt(data1)
        enc2 = golden.homomorphic_encrypt(data2)
        enc_sum = golden.homomorphic_compute(enc1, enc2, 'add')
        result = golden.homomorphic_decrypt(enc_sum)

        expected = [a + b for a, b in zip(data1, data2)]
        print(f"   Homomorphic addition successful: {result == expected}")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Homomorphic encryption demo skipped: {e}")

    # 4. Quantum key distribution
    print("\n4. Quantum Key Distribution (QKD) Concepts:")
    try:
        qkd_key = golden.quantum_key_distribution(256)
        print(f"   QKD key generated: {len(qkd_key)} bytes")
    except Exception as e:
        print(f"   QKD demo skipped: {e}")

    # 5. Threshold cryptography
    print("\n5. Threshold Cryptography:")
    try:
        secret = b"Super secret distributed key"
        shares = golden.threshold_cryptography(shares=5, threshold=3, secret=secret)
        reconstructed = golden.threshold_cryptography(shares[:3])  # Need 3 shares
        success = reconstructed == secret
        print(f"   Threshold crypto successful: {success}")
        print(f"   Secret reconstructed from 3/5 shares")
    except Exception as e:
        print(f"   Threshold crypto demo skipped: {e}")

    # 6. Tamper detection
    print("\n6. Tamper Detection:")
    original = b"Original message"
    encrypted = golden.encrypt(original)

    # Simulate tampering
    tampered = bytearray(encrypted)
    if len(tampered) > 10:
        tampered[10] ^= 0xFF  # Flip a bit

    try:
        decrypted_tampered = golden.decrypt(bytes(tampered))
        print("   Tamper detection: FAILED (should have failed)")
    except Exception as e:
        print("   Tamper detection: SUCCESS (correctly detected tampering)")

def file_encryption_demo():
    """Demonstrate file encryption/decryption"""
    print("\nFile Encryption Demonstration")
    print("=" * 35)

    golden = LuthersAlgorithm()

    # Create a sample file
    sample_content = b"This is a sample file content for encryption demonstration.\n" * 100
    filename = "sample.txt"

    with open(filename, "wb") as f:
        f.write(sample_content)

    print(f"Created sample file: {filename} ({len(sample_content)} bytes)")

    # Read and encrypt file
    with open(filename, "rb") as f:
        file_data = f.read()

    encrypted_data = golden.encrypt(file_data)
    print(f"Encrypted file size: {len(encrypted_data)} bytes")

    # Decrypt and verify
    decrypted_data = golden.decrypt(encrypted_data)
    success = file_data == decrypted_data
    print(f"File decryption successful: {success}")

    # Save decrypted file
    with open("decrypted_sample.txt", "wb") as f:
        f.write(decrypted_data)

    print("Decrypted file saved as: decrypted_sample.txt")

    # Cleanup
    os.remove(filename)
    os.remove("decrypted_sample.txt")

def main():
    """Main demonstration function"""
    print("LUTHER'S GOLDEN ALGORITHM - ADVANCED DEMO")
    print("=" * 55)

    try:
        benchmark_performance()
        demonstrate_security_features()
        file_encryption_demo()

        print("\n" + "=" * 55)
        print("ADVANCED DEMO COMPLETED SUCCESSFULLY!")
        print("Luther's Golden Algorithm: The Ultimate Cryptographic Solution")

    except Exception as e:
        print(f"\nError during demonstration: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()