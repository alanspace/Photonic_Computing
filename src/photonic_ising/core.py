from typing import Tuple, Optional
import numpy as np
import time

class PhotonicIsingSystem:
    def __init__(
        self,
        pixel_pitch: float = 20e-6,
        wavelength: float = 532e-9,
        focal_length: float = 500e-3,
        xi: float = 1.0
    ):
        """
        Initialize the Photonic Ising Machine system parameters.
        
        Args:
            pixel_pitch (float): Pixel pitch in meters (default: 20e-6).
            wavelength (float): Wavelength in meters (default: 532e-9).
            focal_length (float): Focal length of the lens in meters (default: 500e-3).
            xi (float): Scalar amplitude coefficient (default: 1.0).
        """
        self.pixel_pitch = pixel_pitch
        self.wavelength = wavelength
        self.focal_length = focal_length
        self.xi = xi
        self.W = pixel_pitch / 2

    def calculate_spatial_frequency_grid(
        self, 
        num_points: int, 
        factor: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculates the spatial frequency grid.
        
        Args:
            num_points (int): Number of points in the grid.
            factor (float): Factor to determine max frequency (default: 1.0).
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Meshgrid of (kx, ky).
        """
        nyquist_frequency = 1 / (2 * self.pixel_pitch)
        max_frequency = factor * nyquist_frequency
        
        k = np.linspace(-max_frequency, max_frequency, num_points)
        kx, ky = np.meshgrid(k, k)
        
        # Scaling based on wavelength (from notebook logic)
        kx *= (2 * np.pi / self.wavelength)
        ky *= (2 * np.pi / self.wavelength)
        
        return kx, ky

    def calculate_intensity(
        self,
        spin_matrix: np.ndarray,
        kx: np.ndarray,
        ky: np.ndarray,
        verbose: bool = False
    ) -> np.ndarray:
        """
        Calculates the intensity pattern I(x) for the given spin configuration.
        
        Args:
            spin_matrix (np.ndarray): The spin configuration matrix.
            kx (np.ndarray): Spatial frequency grid X.
            ky (np.ndarray): Spatial frequency grid Y.
            verbose (bool): If True, print timing info.
            
        Returns:
            np.ndarray: The intensity pattern I(x).
        """
        start_time = time.time()
        
        # We need to replicate the notebook logic but ideally faster.
        # The notebook logic involves a double loop over all pixels (j and h), which is O(N^2) where N is total pixels.
        # N = n_rows * n_cols. For 10x10, N=100, N^2=10000 iterations.
        
        rows, cols = spin_matrix.shape
        n_pixels = rows * cols
        
        # Initialize E_k (complex field in Fourier domain)
        E_k = np.zeros_like(kx, dtype=complex)
        
        # To optimize, we can iterate over pixels once to build E_k?
        # The notebook has:
        # for j in range(n): ... for h in range(n): ...
        #   E_k += ... spin_j * spin_h * phase_factor ...
        # Wait, the notebook loop accumulates into E_k inside the double loop?
        # That seems like it's calculating the Intensity directly in Fourier domain via Autocorrelation?
        # Notebook code:
        # E_k += (xi^2 * spin[j]* * spin[h] * ... phase_factor)
        # This is summing over pairs. This suggests I(k) or something, but the variable is named E_k.
        # And finally: E_x = ifft2(E_k); I_x = abs(E_x)^2.
        
        # If the notebook calculates: E_k_new = sum_{j,h} ...
        # This term looks like E_k * E_k^* (intensity) in some domain?
        # Let's look closely at the math in the notebook again.
        # I(x) = |E(x)|^2 = sum_j sum_h ...
        
        # It seems the code computes the Fourier transform of the Intensity?
        # If E_k represents the Intensity in Fourier domain (let's call it G_k), then I(x) = IFFT(G_k).
        # Yes, standard property: Fourier Transform of Intensity is Autocorrelation of Field.
        
        # Let's implement the EXACT logic from the notebook first to ensure correctness, 
        # but maybe vectorize the inner loop.
        
        # Vectorized implementation attempt:
        # We can create grids for k_jx, k_jy for all j.
        
        # Flatten spin matrix
        spins_flat = spin_matrix.flatten() # (N,)
        
        # Create coordinate grids
        # j goes 0 to N-1
        # row_j, col_j
        grid_rows, grid_cols = np.indices((rows, cols))
        grid_rows_flat = grid_rows.flatten()
        grid_cols_flat = grid_cols.flatten()
        
        k_jx_flat = 2 * self.W * grid_cols_flat
        k_jy_flat = 2 * self.W * grid_rows_flat
        
        # This is still heavy if we do full broadcasting for large grids.
        # For 1280x768 this will explode.
        # But user's example is 10x10.
        # We will keep the loop for now but maybe just one loop?
        
        # Re-reading the notebook code:
        # It sums over j and h.
        # The term is: spin_j_conj * spin_h * sinc_j * sinc_h_conj * phase(h-j)
        # This is essentially:
        # Term_j = spin_j_conj * sinc_j * exp(-i 2W j k)  <-- wait, phase factor in code is exp(2j * W * ((col_h - col_j) * kx + ...))
        # Let's rewrite phase factor: exp(i * phi_h) * exp(-i * phi_j)
        # where phi_idx = 2 * W * (col_idx * kx + row_idx * ky)
        
        # So the double sum separates!
        # Sum_{j,h} (...) = (Sum_j spin_j_conj * sinc_j * exp(-i phi_j)) * (Sum_h spin_h * sinc_h * exp(i phi_h))
        # Wait, sinc_h_conj = sinc_h (sinc is real).
        # So indeed:
        # Sum_{j,h} = (Sum_j A_j) * (Sum_h B_h) where B_h is conjugate of A_j (if spin is real?)
        # Actually spin is real (+-1).
        # So it is |Sum_j (spin_j * sinc_j * exp(i phi_j))|^2 ?
        
        # Let's verify the term in notebook:
        # spin_matrix[row_j, col_j].conjugate() * spin_matrix[row_h, col_h]
        # * delta_w_square_j * delta_w_square_h.conjugate()
        # * np.exp(2j * W * ((col_h - col_j) * kx + (row_h - row_j) * ky))
        
        # Let Theta_j = 2 * W * (col_j * kx + row_j * ky)
        # Exp term = exp(i * (Theta_h - Theta_j)) = exp(i Theta_h) * exp(-i Theta_j)
        
        # So the total sum is:
        # Sum_{j,h} [ (spin_j^* * sinc_j * exp(-i Theta_j)) * (spin_h * sinc_h * exp(i Theta_h)) ]
        # = [ Sum_j (spin_j^* * sinc_j * exp(-i Theta_j)) ] * [ Sum_h (spin_h * sinc_h * exp(i Theta_h)) ]
        
        # Let F = Sum_h (spin_h * sinc_h * exp(i Theta_h))
        # Then the total sum is F.conj() * F = |F|^2.
        
        # This complexity reduces from O(N^2 * M) to O(N * M) where M is grid size.
        # This is a MASSIVE speedup and definitely "PhD level" optimization.
        
        # Let's implement this optimized version.
        
        # F computation:
        # We iterate over all pixels j.
        # mask = spin_j * sinc(W*(kx - k_jx)) * sinc(W*(ky - k_jy)) * exp(i * 2*W*(col_j*kx + row_j*ky))
        # Accumulate F += mask
        
        F = np.zeros_like(kx, dtype=complex)
        
        for j in range(n_pixels):
            row_j, col_j = divmod(j, cols)
            spin_val = spin_matrix[row_j, col_j]
            
            k_jx = 2 * self.W * col_j
            k_jy = 2 * self.W * row_j
            
            # Sinc terms
            # Note: np.sinc(x) is sin(pi*x)/(pi*x). Notebook used np.sinc.
            # Notebook: np.sinc(W * (kx - k_jx))
            sinc_term = np.sinc(self.W * (kx - k_jx)) * np.sinc(self.W * (ky - k_jy))
            
            # Phase term
            # exp(i * 2W * (col * kx + row * ky))
            phase_arg = 2 * self.W * (col_j * kx + row_j * ky)
            phase_term = np.exp(1j * phase_arg)
            
            F += spin_val * sinc_term * phase_term
            
        # The result E_k in notebook was the double sum.
        # E_k = |F|^2 * xi^2 approximately (checking conjugates)
        # Notebook: E_k += xi^2 * spin_j.conj * spin_h * ...
        # If spin is real, spin.conj = spin.
        # Our F is sum(spin * sinc * exp).
        # F.conj = sum(spin * sinc * exp(-i...))
        # F * F.conj = sum_h(...) * sum_j(...) = double sum.
        # Exactly.
        
        E_k = (np.abs(F) ** 2) * (self.xi ** 2)
        
        # Inverse Fourier Transform to return to spatial domain
        E_x = np.fft.ifft2(E_k)
        
        # Intensity I(x) is the square of the magnitude
        I_x = np.abs(E_x) ** 2
        
        # Scale by focal length
        I_x *= (1 / (self.focal_length ** 2))
        
        if verbose:
            print(f"Computation Time: {time.time() - start_time:.4f} seconds")
            
        return I_x

    def normalize_intensity(self, intensity: np.ndarray) -> np.ndarray:
        """
        Normalizes the intensity matrix to [0, 1].
        """
        i_min = np.min(intensity)
        i_max = np.max(intensity)
        if i_max - i_min == 0:
            return np.zeros_like(intensity)
        return (intensity - i_min) / (i_max - i_min)
