from photonic_ising.ising_machine import IsingMachine
from photonic_ising.visualization import plot_comparison
from photonic_ising.core import PhotonicIsingSystem
import matplotlib.pyplot as plt
import numpy as np

def main():
    print("Initializing Photonic Ising Machine Simulation...")
    # Define system parameters matching the paper/notebook
    params = {
        'pixel_pitch': 20e-6,
        'wavelength': 532e-9,
        'focal_length': 500e-3
    }
    
    # Create machine instance
    n = 10 # 10x10 spins
    machine = IsingMachine(n, params)
    
    # Generate Target Spins
    print(f"Generating random target spin matrix of size {n}x{n}...")
    machine.generate_target()
    
    # Generate 'Detected' Spins (random for comparison)
    print("Generating random detected spin matrix...")
    machine.generate_detected()
    
    # Compute Far-Field Intensities
    print("Computing far-field interference patterns (Fourier Domain)...")
    # Using a high resolution grid for better visualization
    I_target, I_detected = machine.compute_intensities(num_points=200)
    
    # Normalize for plotting
    system = machine.system
    I_target_norm = system.normalize_intensity(I_target)
    I_detected_norm = system.normalize_intensity(I_detected)
    
    print("Visualizing results...")
    plot_comparison(
        target_matrix=machine.target_spin,
        detected_matrix=machine.detected_spin,
        target_intensity=I_target_norm,
        detected_intensity=I_detected_norm,
        save_path="simulation_result.png",
        fig_title="10x10 Photonic Ising Machine: Phase Mask vs Far-Field Intensity"
    )
    print("Simulation complete. Result saved to simulation_result.png")

if __name__ == "__main__":
    main()
