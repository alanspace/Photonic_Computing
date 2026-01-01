import numpy as np
import matplotlib.pyplot as plt
from photonic_ising.ising_machine import IsingMachine
from photonic_ising.utils import binary_phase_to_spin

def run_optimization():
    print("Initializing Photonic Ising Machine Optimization...")
    params = {
        'pixel_pitch': 20e-6,
        'wavelength': 532e-9,
        'focal_length': 500e-3
    }
    n = 10
    machine = IsingMachine(n, params)
    
    # Target
    machine.generate_target()
    
    # Initial Guess
    machine.generate_detected() # Random start
    
    # Grids
    # Use fewer points for speed in loop? The notebook used 100 or so.
    # The complexity is O(NM) where M is grid points.
    num_points = 50 
    kx, ky = machine.system.calculate_spatial_frequency_grid(num_points)
    
    # Precompute Target Intensity
    I_target = machine.system.calculate_intensity(machine.target_spin, kx, ky)
    I_target_norm = machine.system.normalize_intensity(I_target)
    
    # Current State
    current_spin = machine.detected_spin.copy()
    I_current = machine.system.calculate_intensity(current_spin, kx, ky)
    I_current_norm = machine.system.normalize_intensity(I_current)
    
    current_energy = np.sum((I_current_norm - I_target_norm)**2)
    
    energy_history = [current_energy]
    
    # Annealing Parameters
    iterations = 500
    temp = 1.0
    cooling_rate = 0.98
    
    print(f"Starting optimization loop ({iterations} iterations)...")
    
    for i in range(iterations):
        # Cluster Update
        # Allow cluster size to grow
        cluster_size = max(1, int(np.log(i + 2) / np.log(iterations + 2) * (n * n // 4)))
        
        # Propose flip
        new_spin = current_spin.copy()
        
        # Pick random indices
        indices = np.random.choice(n*n, size=cluster_size, replace=False)
        for idx in indices:
            r, c = divmod(idx, n)
            new_spin[r, c] *= -1
            
        # Calculate new intensity
        I_new = machine.system.calculate_intensity(new_spin, kx, ky)
        I_new_norm = machine.system.normalize_intensity(I_new)
        
        # Energy
        new_energy = np.sum((I_new_norm - I_target_norm)**2)
        delta_E = new_energy - current_energy
        
        # Metropolis
        if delta_E < 0 or np.random.rand() < np.exp(-delta_E / temp):
            current_spin = new_spin
            current_energy = new_energy
            I_current_norm = I_new_norm
            
        energy_history.append(current_energy)
        temp *= cooling_rate
        
        if i % 50 == 0:
            print(f"Iter {i}: Energy={current_energy:.4f}, Temp={temp:.4f}, Cluster={cluster_size}")

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(energy_history, label='System Energy', color='blue', linewidth=2)
    plt.title('Energy Minimization over Iterations', fontsize=14)
    plt.xlabel('Iteration Step', fontsize=12)
    plt.ylabel('Cost Function (Energy)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    output_path = "docs/energy_plot.png"
    plt.savefig(output_path, dpi=300)
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    run_optimization()
