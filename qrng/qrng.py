# ⚛️ Pseudo-Quantum RNG built in Python for cryptographic-quality randomness using OS entropy and secure hashing

import os
import time
import hashlib
import numpy as np
from typing import List

class StandaloneQRNG:
    """
    A standalone quantum-like random number generator using system entropy sources.
    Uses multiple cryptographic-quality entropy sources combined with SHA-256 hashing.
    """
    
    def __init__(self):
        # Initialize with multiple entropy sources
        self.entropy_pool = bytearray()
        self._seed_entropy_pool()
    
    def _seed_entropy_pool(self):
        """Gather initial entropy from multiple system sources"""
        # System-specific entropy sources
        entropy_sources = [
            os.urandom(32),                          #OS cryptograph ic randomness
            str(time.perf_counter_ns()).encode(),     # High precision timer
            str(os.getpid()).encode(),                # Process ID
            str(os.getloadavg().encode()) if hasattr(os, "getloadavg") else b"",  # System load (if available)
            str(os.times()).encode(),                # Process times
        ]
        
        # Mix all entropy sources together
        for source in entropy_sources:
            self._add_entropy(source)
    
    def _add_entropy(self, data: bytes):
        """Add new entropy to the pool using cryptographic hashing"""
        # Use SHA-256 to mix new entropy into the pool
        hasher = hashlib.sha256()
        hasher.update(self.entropy_pool)
        hasher.update(data)
        self.entropy_pool = bytearray(hasher.digest())
    
    def _generate_random_bytes(self, num_bytes: int) -> bytes:
        """Generate cryptographically secure random bytes"""
        # Continuously add new entropy and hash the pool
        self._add_entropy(os.urandom(32))
        self._add_entropy(str(time.perf_counter_ns()).encode())
        
        result = bytearray()
        while len(result) < num_bytes:
            # Hash the current pool to get more randomness
            hasher = hashlib.sha256()
            hasher.update(self.entropy_pool)
            hasher.update(os.urandom(8))  # Add more fresh entropy
            result.extend(hasher.digest())
            
            # Update the pool with the new state
            self._add_entropy(hasher.digest())
        
        return bytes(result[:num_bytes])
    
    def get_random_bytes(self, length: int = 1) -> bytes:
        """Get random bytes (0-255)"""
        return self._generate_random_bytes(length)
    
    def get_random_bits(self, num_bits: int = 8) -> List[int]:
        """Get random bits (0 or 1)"""
        num_bytes = (num_bits + 7) // 8
        bytes_data = self._generate_random_bytes(num_bytes)
        bits = []
        for byte in bytes_data:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
                if len(bits) >= num_bits:
                    return bits[:num_bits]
        return bits
    
    def get_random_int(self, min_val: int = 0, max_val: int = 255) -> int:
        """Get random integer in range [min_val, max_val]"""
        if min_val > max_val:
            raise ValueError("max_val must be greater than or equal to min_val")
        if min_val == max_val:
            return min_val
        max_possible = 2**32
        range_size = max_val - min_val + 1
        max_possible = (256 ** 4) - 1
        if range_size > max_possible:
            raise ValueError("Range too large")
        
        # Generate 4 random bytes (32 bits)
        rand_bytes = self._generate_random_bytes(4)
        rand_int = int.from_bytes(rand_bytes, byteorder='big')
        
        return min_val + (rand_int % range_size)
    
    def get_random_float(self) -> float:
        """Get random float between 0 and 1"""
        # Get 8 bytes for 64-bit precision
        rand_bytes = self._generate_random_bytes(8)
        rand_int = int.from_bytes(rand_bytes, byteorder='big')
        # This division produces a float in [0, 1], inclusive of 0 and possibly 1 due to integer division
        return rand_int / (2**64 - 1)
    
    def get_random_normal(self, mean: float = 0.0, stddev: float = 1.0) -> float:
        """Get normally distributed random number using Box-Muller transform"""
        # Get two uniform random numbers
        u1 = self.get_random_float()
        while u1 == 0:  # Avoid log(0)
            u1 = self.get_random_float()
        u2 = self.get_random_float()
        
        # Box-Muller transform
        z0 = np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)
        return mean + stddev * z0

qrng = StandaloneQRNG()
print("Random normal (μ=0, σ=1):", qrng.get_random_normal())


# 🔁 Process:
# 1. Collect raw entropy from OS (urandom, time, PID, CPU stats)
# 2. Mix and hash entropy using SHA-256 to update internal pool
# 3. Generate random bytes from the hashed pool
# 4. Convert bytes into bits, integers, floats, or normal-distributed numbers
# ➤ This layering simulates quantum-like unpredictability without real quantum hardware
