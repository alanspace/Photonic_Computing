import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple
from .utils import spin_to_phase

def plot_phase_matrix(
    phase_matrix: np.ndarray, 
    title: str = "Phase Matrix", 
    ax: Optional[plt.Axes] = None,
    colorbar: bool = True
):
    """
    Plots a phase matrix using a pixelated heatmap.
    """
    if ax is None:
        fig, ax = plt.subplots()
    
    cax = ax.imshow(phase_matrix, cmap='viridis')
    ax.set_title(title)
    ax.set_xlabel("Pixel Position X")
    ax.set_ylabel("Pixel Position Y")
    
    if colorbar:
        # Custom colorbar for 0 and pi
        cbar = plt.colorbar(cax, ax=ax, ticks=[0, np.pi])
        cbar.ax.set_yticklabels(['0', '$\\pi$'])

def plot_intensity(
    intensity: np.ndarray, 
    title: str = "Intensity Pattern", 
    ax: Optional[plt.Axes] = None
):
    """
    Plots the intensity pattern.
    """
    if ax is None:
        fig, ax = plt.subplots()
        
    # We might want to use fftshift usually to center it, 
    # but the notebook didn't use it in the display, 
    # however the notebook mentioned using fftshift at the end of thoughts.
    # Let's check the core logic calculation. 
    # I_x comes from ifft2(E_k). 
    # Usually we shift it for visualization.
    
    shifted_intensity = np.fft.fftshift(intensity)
    
    im = ax.imshow(shifted_intensity, cmap='viridis')
    ax.set_title(title)
    ax.set_xlabel("Pixel Position X")
    ax.set_ylabel("Pixel Position Y")
    plt.colorbar(im, ax=ax, label="Intensity")

def plot_comparison(
    target_matrix: np.ndarray,
    detected_matrix: np.ndarray,
    target_intensity: Optional[np.ndarray] = None,
    detected_intensity: Optional[np.ndarray] = None,
    save_path: Optional[str] = None,
    fig_title: Optional[str] = None
):
    """
    Plots a comparison between target and detected matrices and their intensities.
    """
    rows = 2 if target_intensity is not None else 1
    fig, axes = plt.subplots(rows, 2, figsize=(12, 5 * rows))
    
    if fig_title:
        fig.suptitle(fig_title, fontsize=16)

    
    if rows == 1:
        axes = [axes] # standardize to 2D array if possible, or just handle
        
    # Row 1: Phase/Spin Matrices
    # Convert spin to phase for plotting if needed, assuming input matches utility
    # Check if input is spin (-1, 1) or phase (0, pi)
    # Heuristic: if values are -1, 1 then spin.
    
    def get_phase(m):
        if np.all(np.isin(m, [-1, 1])):
            return spin_to_phase(m)
        return m
        
    p1 = get_phase(target_matrix)
    p2 = get_phase(detected_matrix)
    
    ax0 = axes[0][0] if rows > 1 else axes[0]
    ax1 = axes[0][1] if rows > 1 else axes[1]
    
    plot_phase_matrix(p1, "Target Phase Matrix", ax=ax0)
    plot_phase_matrix(p2, "Detected Phase Matrix", ax=ax1)
    
    if rows > 1:
        plot_intensity(target_intensity, "Target Intensity", ax=axes[1][0])
        plot_intensity(detected_intensity, "Detected Intensity", ax=axes[1][1])
        
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.show()
