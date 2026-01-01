import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time
from src.photonic_ising.ising_machine import IsingMachine
from src.photonic_ising.utils import generate_random_phase_matrix, binary_phase_to_spin

# --- Page Configuration ---
st.set_page_config(
    page_title="Photonic Ising Machine",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Premium Look ---
st.markdown("""
<style>
    /* Main Background and Text */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(20, 20, 30) 0%, rgb(0, 0, 0) 90%);
        color: #E0E0E0;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0A0A10;
        border-right: 1px solid #333;
    }
    
    /* Headings */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #ffffff;
        text-shadow: 0px 0px 10px rgba(255, 255, 255, 0.2);
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #00ADB5;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #00ADB5, #007BFF);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0px 0px 15px rgba(0, 173, 181, 0.6);
    }
    
    /* Cards/Containers */
    .css-1r6slb0 {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Logic Helper Functions ---
def optimize_spins(machine, target_spin, iterations=500, temp=1.0):
    """
    Runs a Simulated Annealing process to match the target spin configuration.
    Demonstrates the optimization process.
    """
    current_spin = machine.detected_spin.copy()
    current_energy = np.sum(np.abs(current_spin - target_spin)) # Simple Hamming distance energy
    
    energies = [current_energy]
    
    # Placeholder for the plots
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Current Spin Phase Mask")
        plot_placeholder_1 = st.empty()
    with col2:
        st.caption("Far-Field Intensity (Fourier Plane)")
        plot_placeholder_2 = st.empty()
        
    chart_placeholder = st.empty()
    
    for i in range(iterations):
        # 1. Flip a random spin
        r, c = np.random.randint(0, machine.size, 2)
        
        # Calculate Energy Change (Delta H)
        # Using simple Hamming distance: if spins match sign, dist=0, else dist=2
        # We want to MINIMIZE distance (energy).
        
        # Current contribution
        curr_dist = abs(current_spin[r,c] - target_spin[r,c])
        # Proposed flip
        flipped_val = current_spin[r,c] * -1
        new_dist = abs(flipped_val - target_spin[r,c])
        
        dE = new_dist - curr_dist
        
        # Metropolis Criterion
        if dE < 0 or np.random.rand() < np.exp(-dE / temp):
            current_spin[r, c] = flipped_val
            current_energy += dE
        
        energies.append(current_energy)
        
        # Update Visuals every N steps to save time
        if i % 10 == 0 or i == iterations - 1:
            # Update machine state
            machine.detected_spin = current_spin
            
            # Recompute optical intensity only for display
            I_target, I_detected = machine.compute_intensities(num_points=100) # Lower res for speed
            
            # Plot Spins
            fig1, ax1 = plt.subplots(figsize=(4, 4))
            ax1.imshow(current_spin, cmap='RdBu', vmin=-1, vmax=1)
            ax1.set_axis_off()
            plot_placeholder_1.pyplot(fig1)
            plt.close(fig1)
            
            # Plot Intensity
            fig2, ax2 = plt.subplots(figsize=(4, 4))
            ax2.imshow(machine.system.normalize_intensity(I_detected), cmap='inferno')
            ax2.set_axis_off()
            plot_placeholder_2.pyplot(fig2)
            plt.close(fig2)
            
            # Update Chart
            chart_placeholder.line_chart(energies)
            
            # Adaptive Decay
            temp *= 0.99
            
            # time.sleep(0.01) # Small delay for animation effect
            
    return current_spin, energies


# --- Main App Interface ---

def main():
    st.title("🌌 Photonic Ising Machine")
    st.write("_Solving Combinatorial Optimization via Optical Interference_")

    # --- Sidebar Controls ---
    st.sidebar.header("🔬 Simulation Parameters")
    
    grid_size = st.sidebar.slider("Grid Size (N x N)", min_value=5, max_value=20, value=10, step=1, help="The number of spins in the grid (N x N). Larger grids represent more complex optimization problems (NP-hard). Limit is set to 20 for web demo performance.")
    iterations = st.sidebar.slider("Iterations", min_value=100, max_value=2000, value=500, step=100, help="Number of steps in the annealing process. More iterations allow the system to explore more states, increasing the chance of finding the global minimum.")
    temperature = st.sidebar.slider("Initial Temperature", 0.1, 5.0, 1.0, help="Controls the 'randomness' of the search. High temperature helps escape local minima (incorrect solutions that look good locally). Look for a smooth decay curve.")
    
    # Initialize Machine
    if 'machine' not in st.session_state or st.session_state.get('grid_size') != grid_size:
        params = {
            'pixel_pitch': 20e-6,
            'wavelength': 532e-9,
            'focal_length': 500e-3
        }
        st.session_state.machine = IsingMachine(grid_size, params)
        st.session_state.machine.generate_target() # The "Problem" instance
        st.session_state.machine.generate_detected() # Random start
        st.session_state.grid_size = grid_size
        
        # Precompute target intensity once
        st.session_state.I_target, _ = st.session_state.machine.compute_intensities(num_points=100)

    machine = st.session_state.machine

    # --- Layout ---
    
    st.markdown("### Target Configuration (The 'Solution')")
    st.info("The machine tries to find the spin configuration that produces this specific diffraction pattern.")
    
    # Show Target
    c1, c2 = st.columns(2)
    with c1:
        fig_t, ax_t = plt.subplots(figsize=(5,5))
        ax_t.imshow(machine.target_spin, cmap='RdBu', vmin=-1, vmax=1)
        ax_t.set_title("Target Spin Map")
        ax_t.axis('off')
        st.pyplot(fig_t)
        plt.close(fig_t)
        
    with c2:
        fig_ti, ax_ti = plt.subplots(figsize=(5,5))
        ax_ti.imshow(machine.system.normalize_intensity(st.session_state.I_target), cmap='inferno')
        ax_ti.set_title("Target Intensity Pattern")
        ax_ti.axis('off')
        st.pyplot(fig_ti)
        plt.close(fig_ti)

    st.divider()
    
    with st.expander("📖 How to Interpret Results", expanded=False):
        st.markdown("""
        **1. The Spin Map (Left):**
        - Represents the actual solution state.
        - **Blue/Red** pixels are +1/-1 spins.
        - Goal: Match the 'Target Spin Map' exactly.
        
        **2. The Intensity Pattern (Right):**
        - This is what the physics actually computes (Fourier Transform).
        - The machine adjusts spins to make this light pattern match the target pattern.
        
        **3. The Energy Chart (Below):**
        - Shows the "error" over time.
        - **Good Result**: Curve goes down to zero (or very close).
        - **Bad Result**: Curve gets stuck at a high value (Local Minimum). Try increasing *Temperature* or *Iterations*.
        """)

    st.markdown("### Real-Time Optimization")
    
    if st.button("🚀 Run Simulation"):
        # Reset detected to random
        machine.generate_detected() 
        final_spin, energy_history = optimize_spins(machine, machine.target_spin, iterations, temperature)
        st.success("Optimization Complete!")
        
    st.sidebar.markdown("---")
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Theory:** The device encodes problem variables into the phase of a light beam. "
        "Interference performs massive parallel computation to find the ground state."
    )
    st.sidebar.warning(
        "**Tip:** If the optimization gets stuck (Energy doesn't drop to 0), "
        "try increasing the **Initial Temperature** to let it 'jump' out of local traps."
    )

if __name__ == "__main__":
    main()
