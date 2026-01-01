import numpy as np
from .core import PhotonicIsingSystem
from .utils import generate_random_phase_matrix, binary_phase_to_spin

class IsingMachine:
    def __init__(self, size: int, system_params: dict = None):
        """
        High-level interface for the Photonic Ising Machine.
        
        Args:
            size (int): Size of the spin grid (size x size).
            system_params (dict): Parameters for PhotonicIsingSystem.
        """
        self.size = size
        if system_params is None:
            system_params = {}
        self.system = PhotonicIsingSystem(**system_params)
        
        self.target_spin = None
        self.detected_spin = None
        self.kx = None
        self.ky = None
        
    def generate_target(self):
        """Generates a random target spin configuration."""
        phase = generate_random_phase_matrix(self.size)
        self.target_spin = binary_phase_to_spin(phase)
        
    def generate_detected(self, noise_level: float = 0.0):
        """
        Generates a detected spin configuration, potentially close to target with some noise/perturbation.
        In this simplified version, we just generate a random one or perturbed one.
        
        Args:
            noise_level (float): If > 0, perturb the target. If 0, random. 
            (Actually, original code generated a random 'detected' or perturbed. Let's do random if target is None)
        """
        if self.target_spin is not None and noise_level > 0:
            # Simple perturbation logic: flip some spins
            n_flips = int(self.size * self.size * noise_level)
            new_spin = self.target_spin.copy()
            for _ in range(n_flips):
                r, c = np.random.randint(0, self.size, 2)
                new_spin[r, c] *= -1
            self.detected_spin = new_spin
        else:
            phase = generate_random_phase_matrix(self.size)
            self.detected_spin = binary_phase_to_spin(phase)
            
    def compute_intensities(self, num_points: int = 100):
        """Computes intensities for current target and detected spins."""
        if self.target_spin is None:
            raise ValueError("Target spin not generated.")
        
        if self.kx is None:
            self.kx, self.ky = self.system.calculate_spatial_frequency_grid(num_points)
            
        I_target = self.system.calculate_intensity(self.target_spin, self.kx, self.ky)
        
        I_detected = None
        if self.detected_spin is not None:
             I_detected = self.system.calculate_intensity(self.detected_spin, self.kx, self.ky)
             
        return I_target, I_detected
