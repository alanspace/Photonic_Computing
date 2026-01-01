import numpy as np

def generate_random_phase_matrix(n: int) -> np.ndarray:
    """
    Generates a random phase matrix of size nxn with discrete phases {0, pi}.
    
    Args:
        n (int): The size of the matrix (nxn).
        
    Returns:
        np.ndarray: A nxn matrix with entries 0 or pi.
    """
    phase_matrix = np.random.choice([0, np.pi], size=(n, n))
    return phase_matrix

def binary_phase_to_spin(phase_matrix: np.ndarray) -> np.ndarray:
    """
    Converts a binary phase matrix (0, pi) to a spin variable matrix (1, -1).
    0 maps to 1, pi maps to -1.
    
    Args:
        phase_matrix (np.ndarray): The phase matrix.
        
    Returns:
        np.ndarray: The spin matrix.
    """
    spin_matrix = np.where(phase_matrix == 0, 1, -1)
    return spin_matrix

def spin_to_phase(spin_matrix: np.ndarray) -> np.ndarray:
    """
    Converts a spin variable matrix (1, -1) back to binary phase matrix (0, pi).
    1 maps to 0, -1 maps to pi.
    
    Args:
        spin_matrix (np.ndarray): The spin matrix.
        
    Returns:
        np.ndarray: The phase matrix.
    """
    phase_matrix = np.where(spin_matrix == 1, 0, np.pi)
    return phase_matrix
