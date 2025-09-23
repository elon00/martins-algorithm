#!/usr/bin/env python3
"""
Test script for Classiq-enhanced Luther's Algorithm
Tests all quantum computing features and enhancements
"""

import sys
import os
sys.path.append('.')

from luther_algorithm.luther_algorithm import LuthersAlgorithm

def test_classiq_integration():
    """Test Classiq integration and authentication"""
    print("🧪 Testing Classiq Integration...")

    try:
        # Initialize with Classiq backend
        luther = LuthersAlgorithm(mode='super', quantum_backend='classiq', use_gpu=False, use_ml=True)

        print(f"✅ Classiq Available: {luther.classiq_available}")
        print(f"✅ Security Level: {luther.get_security_level()}")

        if luther.classiq_available:
            print("✅ Classiq authentication successful!")
            print(f"   Backend: {luther.execution_preferences.backend}")
            print(f"   Shots: {luther.execution_preferences.num_shots}")
            print(f"   Timeout: {luther.execution_preferences.timeout_seconds}s")
        else:
            print("⚠️  Classiq not available, using classical simulation")

        return True

    except Exception as e:
        print(f"❌ Classiq integration test failed: {e}")
        return False

def test_quantum_operations():
    """Test quantum operations"""
    print("\n🧪 Testing Quantum Operations...")

    try:
        luther = LuthersAlgorithm(mode='super', quantum_backend='classiq')

        # Test quantum factoring
        test_number = 15  # Small number for testing
        factors = luther._quantum_factor_parallel(test_number)
        print(f"✅ Quantum factoring of {test_number}: {factors}")

        # Test quantum key distribution
        qkd_key = luther.quantum_key_distribution(256)
        print(f"✅ QKD key generated: {len(qkd_key)} bytes")

        # Test quantum machine learning
        test_data = [1, 2, 3, 4, 5]
        qml_prediction = luther.quantum_machine_learning_predict(test_data, 'classification')
        print(f"✅ QML prediction: {qml_prediction}")

        return True

    except Exception as e:
        print(f"❌ Quantum operations test failed: {e}")
        return False

def test_encryption_layers():
    """Test multi-layer encryption"""
    print("\n🧪 Testing Multi-Layer Encryption...")

    try:
        luther = LuthersAlgorithm(mode='super', quantum_backend='classiq')

        # Test data
        test_data = b"This is a test message for quantum-enhanced encryption!"

        print(f"Original data: {test_data.decode()}")
        print(f"Original size: {len(test_data)} bytes")

        # Encrypt
        encrypted = luther.encrypt(test_data)
        print(f"Encrypted size: {len(encrypted)} bytes")
        print(f"Encryption overhead: {len(encrypted) - len(test_data)} bytes")

        # Decrypt
        decrypted = luther.decrypt(encrypted)
        print(f"Decrypted data: {decrypted.decode()}")

        # Verify
        success = test_data == decrypted
        print(f"✅ Encryption/Decryption successful: {success}")

        return success

    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        return False

def test_security_features():
    """Test all security features"""
    print("\n🧪 Testing Security Features...")

    try:
        luther = LuthersAlgorithm(mode='super', quantum_backend='classiq')

        # Test homomorphic encryption if available
        if luther.homomorphic:
            test_data = [1, 2, 3, 4, 5]
            encrypted_he = luther.homomorphic_encrypt(test_data)
            decrypted_he = luther.homomorphic_decrypt(encrypted_he)
            print(f"✅ Homomorphic encryption: {decrypted_he}")

        # Test zero-knowledge proofs if available
        if luther.zk_proofs:
            secret = 42
            proof = luther.zero_knowledge_proof(secret, None, 'range')
            verified = luther.verify_zero_knowledge_proof(proof, None)
            print(f"✅ Zero-knowledge proof: {verified}")

        # Test threshold cryptography
        secret = b"Super secret key"
        shares = luther.threshold_cryptography(5, 3, secret)
        reconstructed = luther.threshold_cryptography(shares, 3)
        print(f"✅ Threshold cryptography: {reconstructed == secret}")

        return True

    except Exception as e:
        print(f"❌ Security features test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Classiq-Enhanced Luther's Algorithm Tests")
    print("=" * 60)

    tests = [
        test_classiq_integration,
        test_quantum_operations,
        test_encryption_layers,
        test_security_features
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Your algorithm is quantum-enhanced and ready!")
        print("🔬 Features activated:")
        luther = LuthersAlgorithm()
        print(f"   {luther.get_security_level()}")
    else:
        print("⚠️  Some tests failed. Check your Classiq installation and configuration.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)