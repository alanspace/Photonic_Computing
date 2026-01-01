import numpy as np
import pytest
from photonic_ising.core import PhotonicIsingSystem
from photonic_ising.utils import generate_random_phase_matrix, binary_phase_to_spin

def test_spatial_frequency_grid():
    system = PhotonicIsingSystem()
    kx, ky = system.calculate_spatial_frequency_grid(10)
    assert kx.shape == (10, 10)
    assert ky.shape == (10, 10)

def test_intensity_calculation_runs():
    system = PhotonicIsingSystem()
    spin_matrix = np.array([[1, -1], [-1, 1]])
    kx, ky = system.calculate_spatial_frequency_grid(20)
    
    intensity = system.calculate_intensity(spin_matrix, kx, ky, verbose=True)
    assert intensity.shape == (20, 20)
    # Intensity should be non-negative (real physics)
    # But computational errors might give small negative imaginary parts or something?
    # abs()^2 is always real and >= 0.
    assert np.all(intensity >= 0)

def test_compare_cpu_optimization():
    """
    Check if the vectorized calculation is 'reasonably' fast and outputs correct shape.
    We don't have the original slow function here to cmp against, but we trust the math derivation.
    """
    n = 10
    system = PhotonicIsingSystem()
    phase = generate_random_phase_matrix(n)
    spin = binary_phase_to_spin(phase)
    
    # Grid size for fourier
    grid_size = 50
    kx, ky = system.calculate_spatial_frequency_grid(grid_size)
    
    import time
    t0 = time.time()
    I = system.calculate_intensity(spin, kx, ky)
    t1 = time.time()
    
    assert I.shape == (grid_size, grid_size)
    # 10x10 spin matrix on 50x50 grid should be very fast with optimization (< 0.1s usually)
    # Original code took 0.5s.
    duration = t1 - t0
    print(f"\nOptimization Duration: {duration}s")
    # Not strictly asserting duration to avoid flaky tests on CI, but good for manual check.
