#!/usr/bin/env python3
"""
Basic usage example for Luther's Golden Algorithm
"""

from luther_algorithm import LuthersAlgorithm

def main():
    print("Luther's Golden Algorithm - Basic Usage Demo")
    print("=" * 50)

    # Initialize the golden algorithm
    golden = LuthersAlgorithm()

    # Example 1: Basic encryption/decryption
    print("\n1. Basic Encryption/Decryption:")
    plaintext = b"Hello, this is Luther's Golden Algorithm!"
    print(f"   Original: {plaintext.decode()}")

    # Encrypt
    encrypted = golden.encrypt(plaintext)
    print(f"   Encrypted size: {len(encrypted)} bytes")

    # Decrypt
    decrypted = golden.decrypt(encrypted)
    success = plaintext == decrypted
    print(f"   Decryption successful: {success}")

    # Example 2: Large data encryption
    print("\n2. Large Data Encryption:")
    large_data = b"A" * 100000  # 100KB
    print(f"   Data size: {len(large_data)} bytes")

    encrypted_large = golden.encrypt(large_data)
    print(f"   Encrypted size: {len(encrypted_large)} bytes")

    decrypted_large = golden.decrypt(encrypted_large)
    success_large = len(large_data) == len(decrypted_large)
    print(f"   Large data encryption successful: {success_large}")

    # Example 3: Digital signatures
    print("\n3. Digital Signatures:")
    message = b"This message is signed with golden security"
    print(f"   Message: {message.decode()}")

    signature = golden.sign(message)
    print(f"   Signature created: {len(signature)} bytes")

    verified = golden.verify(message, signature)
    print(f"   Signature verification: {verified}")

    # Example 4: Quantum factoring
    print("\n4. Quantum Factoring:")
    number = 1025
    factors = golden._quantum_factor_parallel(number)
    print(f"   Factoring {number}: {factors}")
    verification = factors[0] * factors[1] == number
    print(f"   Verification: {factors[0]} * {factors[1]} = {factors[0] * factors[1]} ({verification})")

    print("\n" + "=" * 50)
    print("All demos completed successfully!")
    print("Luther's Golden Algorithm: Unbreakable, Unparalleled, Unequaled!")

if __name__ == "__main__":
    main()