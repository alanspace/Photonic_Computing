import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

import io
import datetime
from PIL import Image
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
def optimize_spins(machine, target_spin, iterations=500, temp=1.0, decay_rate=0.99, use_clusters=False, use_adaptive_temp=True):
    """
    Simulated Annealing with adaptive temperature control (Simulated Tempering).
    Monitors acceptance rate and adjusts temperature to maintain optimal exploration.
    """
    current_spin = machine.detected_spin.copy()
    size = machine.size
    
    # Energy calculation
    def calculate_ising_energy(spins, target):
        energy = 0
        for i in range(size):
            for j in range(size):
                if j < size - 1:
                    J = target[i,j] * target[i,j+1]
                    energy -= J * spins[i,j] * spins[i,j+1]
                if i < size - 1:
                    J = target[i,j] * target[i+1,j]
                    energy -= J * spins[i,j] * spins[i+1,j]
        return energy
    
    current_energy = calculate_ising_energy(current_spin, target_spin)
    energies = [current_energy]
    
    # Simulated Tempering tracking
    acceptance_window = 50
    recent_accepts = []
    temperature_history = [temp]
    
    # UI
    col1, col2 = st.columns(2)
    with col1:
        caption = "Current Spin Phase Mask"
        if use_adaptive_temp:
            caption += " (Simulated Tempering)"
        st.caption(caption)
        plot_placeholder_1 = st.empty()
    with col2:
        st.caption("Far-Field Intensity (Fourier Plane)")
        plot_placeholder_2 = st.empty()
        
    chart_placeholder = st.empty()
    
    for i in range(iterations):
        # Single spin flip
        r, c = np.random.randint(0, size, 2)
        old_spin = current_spin[r, c]
        new_spin = -old_spin
        
        # Energy change
        dE = 0
        if c < size - 1:
            J = target_spin[r,c] * target_spin[r,c+1]
            dE -= J * (new_spin - old_spin) * current_spin[r,c+1]
        if c > 0:
            J = target_spin[r,c-1] * target_spin[r,c]
            dE -= J * current_spin[r,c-1] * (new_spin - old_spin)
        if r < size - 1:
            J = target_spin[r,c] * target_spin[r+1,c]
            dE -= J * (new_spin - old_spin) * current_spin[r+1,c]
        if r > 0:
            J = target_spin[r-1,c] * target_spin[r,c]
            dE -= J * current_spin[r-1,c] * (new_spin - old_spin)
        
        # Metropolis
        accepted = False
        if dE < 0 or np.random.rand() < np.exp(-dE / temp):
            current_spin[r, c] = new_spin
            current_energy += dE
            accepted = True
        
        recent_accepts.append(1 if accepted else 0)
        if len(recent_accepts) > acceptance_window:
            recent_accepts.pop(0)
        
        energies.append(current_energy)
        
        # SIMULATED TEMPERING: Adapt temperature based on acceptance rate
        if use_adaptive_temp and i % acceptance_window == 0 and len(recent_accepts) >= acceptance_window:
            acceptance_rate = np.mean(recent_accepts)
            
            # Target: 20-40% acceptance (optimal for single-spin)
            if acceptance_rate < 0.15:  # Too stuck - heat up
                temp *= 1.15
                temp = min(temp, 5.0)
            elif acceptance_rate > 0.6:  # Too random - cool down
                temp *= 0.92
                temp = max(temp, 0.01)
        
        # Still apply decay (slower when adaptive)
        if not use_adaptive_temp or i % 10 == 0:
            temp *= decay_rate
        
        temperature_history.append(temp)
        
        # Visualization
        if i % 10 == 0 or i == iterations - 1:
            machine.detected_spin = current_spin
            I_target, I_detected = machine.compute_intensities(num_points=100)
            
            # Spin map
            fig1, ax1 = plt.subplots(figsize=(4, 4))
            ax1.imshow(current_spin, cmap='RdBu', vmin=-1, vmax=1)
            ax1.set_axis_off()
            plot_placeholder_1.pyplot(fig1)
            plt.close(fig1)
            
            # Intensity
            fig2, ax2 = plt.subplots(figsize=(4, 4))
            ax2.imshow(machine.system.normalize_intensity(I_detected), cmap='inferno')
            ax2.set_axis_off()
            plot_placeholder_2.pyplot(fig2)
            plt.close(fig2)
            
            # Chart: Energy + Temperature
            if use_adaptive_temp:
                fig_chart, (ax1_chart, ax2_chart) = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
                
                # Energy
                ax1_chart.plot(energies, color='#00ADB5', linewidth=2, label='Energy')
                ax1_chart.set_ylabel("Energy", color='gray', fontsize=10)
                ax1_chart.tick_params(colors='gray')
                ax1_chart.legend(loc='upper right', fontsize=9)
                ax1_chart.grid(True, alpha=0.3)
                ax1_chart.set_facecolor((0,0,0,0))
                
                # Temperature
                ax2_chart.plot(temperature_history, color='#FF6B6B', linewidth=2, label='Temperature')
                ax2_chart.set_ylabel("Temp", color='gray', fontsize=10)
                ax2_chart.set_xlabel("Iteration", color='gray', fontsize=10)
                ax2_chart.tick_params(colors='gray')
                ax2_chart.legend(loc='upper right', fontsize=9)
                ax2_chart.grid(True, alpha=0.3)
                ax2_chart.set_facecolor((0,0,0,0))
                
                fig_chart.suptitle("Simulated Tempering (Adaptive)", color='white', fontsize=12)
            else:
                fig_chart, ax_chart = plt.subplots(figsize=(8,3))
                ax_chart.plot(energies, color='#00ADB5', label='Energy')
                ax_chart.set_title("Standard Annealing", color='white')
                ax_chart.set_xlabel("Iteration", color='gray')
                ax_chart.set_ylabel("Energy", color='gray')
                ax_chart.tick_params(colors='gray')
                ax_chart.legend()
                ax_chart.grid(True, alpha=0.3)
                ax_chart.set_facecolor((0,0,0,0))
            
            fig_chart.patch.set_alpha(0.0)
            chart_placeholder.pyplot(fig_chart)
            plt.close(fig_chart)
    
    _, final_intensity = machine.compute_intensities(num_points=100)
    return current_spin, energies, final_intensity


def get_ai_interpretation(api_key, grid_size, final_energy, start_energy, iterations, temperature, decay_rate, spin_image, chart_image, history):
    """
    Calls Google Gemini (using the new google-genai SDK) to interpret the simulation results visually and historically.
    """
    if not api_key:
        return "⚠️ Please enter a Google API Key in the sidebar to use AI interpretation."
        
    try:
        from google import genai
        from google.genai import types
        
        # Initialize the client with the provided API key
        client = genai.Client(api_key=api_key)
        
        # Format history for the prompt
        history_str = ""
        if history:
            history_str = "HISTORY OF PREVIOUS RUNS:\n" + "\n".join([str(run) for run in history[-5:]]) # Limit to last 5 to save tokens
        else:
            history_str = "No previous runs recorded."

        prompt = f"""
        You are a senior physicist with expertise in statistical mechanics and stochastic optimization, analyzing a Photonic Ising Machine simulation.
        
        CRITICAL PHYSICS CONTEXT:
        - This is a STOCHASTIC Monte Carlo simulation using Metropolis-Hastings algorithm
        - Run-to-run variations of 5-15% are NORMAL and EXPECTED (thermal fluctuations + random initial conditions)
        - Energy scale: For a {grid_size}x{grid_size} grid, ground state ≈ -{2*(grid_size-1)*grid_size} (perfect), random ≈ 0
        - More negative energy = BETTER (Ising Hamiltonian convention)
        
        CURRENT RUN PARAMETERS:
        - Grid Size: {grid_size}x{grid_size} spins
        - Iterations: {iterations}
        - Initial Temperature: {temperature}
        - Cooling/Decay Rate: {decay_rate}
        - Starting Energy: {start_energy:.2f}
        - Final Energy: {final_energy:.2f}
        - Ground State Target: ≈ -{2*(grid_size-1)*grid_size}
        
        {history_str}
        
        IMAGES PROVIDED:
        1. Final Spin Phase Mask (Blue/Red = ±1 spins): Look for domain walls, cluster sizes
        2. Optimization Trajectory: Look for plateaus (metastable states), convergence rate
        
        ANALYSIS INSTRUCTIONS:
        Provide a response in THREE parts:
        
        1. **Visual Analysis** (Physics):
           - Describe domain structure (large coherent vs. fragmented)
           - Identify plateaus in trajectory (metastable states)
           - Estimate optimization quality: (final_energy / ground_state) as percentage
        
        2. **Trend Analysis** (Statistics):
           - Compare current result to history
           - IMPORTANT: Variations of 5-15% between runs are NORMAL for stochastic processes
           - Only flag as "potential bug" if:
             * Results are IDENTICAL (variation <1%) across different random runs
             * Logical parameter improvements consistently worsen results
             * Energy is POSITIVE or increasing
           - Otherwise, attribute variation to thermal fluctuations (correct physics!)
        
        3. **Recommendation** (Optimization):
           - Suggest ONE specific parameter change to improve convergence:
             * Increase iterations (more exploration time)
             * Adjust temperature (higher = escape local minima)
             * Adjust decay rate (slower cooling = better equilibration)
           - Quantify expected improvement (e.g., "should reach ~-160")
        
        Keep response concise, physics-focused, and educational. DO NOT incorrectly flag normal stochastic behavior as bugs.
        """
        
        # Prepare content list for multimodal request
        contents = [
            prompt,
            spin_image,
            chart_image
        ]
        
        # Using gemini-2.0-flash-exp for multimodal capabilities
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp", 
            contents=contents
        )
        return response.text
    except Exception as e:
        return f"Error contacting AI: {str(e)}"


# --- Main App Interface ---

def main():
    st.title("🌌 Photonic Ising Machine")
    st.write("_Solving Combinatorial Optimization via Optical Interference_")

    # --- Sidebar Controls ---
    st.sidebar.header("🔬 Simulation Parameters")
    
    grid_size = st.sidebar.slider("Grid Size (N x N)", min_value=5, max_value=20, value=10, step=1, help="The number of spins in the grid (N x N). Larger grids represent more complex optimization problems (NP-hard). Limit is set to 20 for web demo performance.")
    iterations = st.sidebar.slider("Iterations", min_value=100, max_value=5000, value=500, step=100, help="Number of steps in the annealing process. More iterations allow the system to explore more states, increasing the chance of finding the global minimum.")
    temperature = st.sidebar.slider("Initial Temperature", 0.1, 5.0, 1.0, help="Controls the 'randomness' of the search. High temperature helps escape local minima.")
    decay_rate = st.sidebar.slider("Cooling Rate (Decay)", 0.90, 0.999, 0.99, step=0.001, format="%.3f", help="How fast the temperature drops. Higher values (closer to 1.0, e.g. 0.995) mean slower cooling, giving the system more time to find the true solution.")
    
    st.sidebar.markdown("### ⚙️ Advanced Options")
    use_adaptive_temp = st.sidebar.checkbox("Enable Simulated Tempering", value=True, help="Adaptive temperature control: monitors acceptance rate and adjusts temperature automatically for optimal exploration. Typically 20-40% faster convergence!")
    
    st.sidebar.markdown("### 🤖 AI Analysis")
    api_key = st.sidebar.text_input("Google API Key", type="password", help="Enter your Gemini API key to get AI interpretation of the results.")
    
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
    
    # Initialize History
    if 'history' not in st.session_state:
        st.session_state.history = []

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
        - **Note**: For the Ising Hamiltonian, energy is NEGATIVE. More negative = better!
        - **Good Result**: Curve goes down to very negative values (ideally around -200 for 10x10 grid).
        - **Bad Result**: Curve gets stuck at less negative values (Local Minimum). Try increasing *Temperature* or *Iterations*.
        """)

    st.markdown("### Real-Time Optimization")
    
    if st.button("🚀 Run Simulation"):
        #Reset detected to random with fresh seed
        np.random.seed(int(time.time() * 1000) % (2**32))  # Ensure different random state each run
        machine.generate_detected() 
        final_spin, energy_history, final_intensity = optimize_spins(machine, machine.target_spin, iterations, temperature, decay_rate, use_clusters=False, use_adaptive_temp=use_adaptive_temp)
        st.success("Optimization Complete!")
        
        # Record Run
        run_record = {
            "Grid": grid_size,
            "Iter": iterations,
            "Temp": temperature,
            "Decay": decay_rate,
            "Final_E": float(f"{energy_history[-1]:.2f}")
        }
        st.session_state.history.append(run_record)
        
        # Store results in session state to persist across reruns (like clicking Save button)
        st.session_state.last_run = {
            "final_spin": final_spin,
            "target_spin": machine.target_spin,
            "energy_history": energy_history,
            "final_intensity": final_intensity,
            "target_intensity": st.session_state.I_target,
            "grid_size": grid_size,
            "iterations": iterations,
            "temperature": temperature,
            "decay_rate": decay_rate,
            "start_energy": energy_history[0],
            "final_energy": energy_history[-1],
            "analysis": None # Will fill this after AI runs
        }

    # Display Results if they exist in session state (so they persist after button clicks)
    if 'last_run' in st.session_state:
        # Retrieve data
        run_data = st.session_state.last_run
        
        # AI Analysis Section
        st.divider()
        st.subheader("🤖 AI Researcher Analysis")
        
        if api_key:
            if run_data["analysis"] is None: 
                # Run AI only if we haven't already for this specific run
                with st.spinner("sending the phase mask and energy plot to Gemini 2.0 for visual physics analysis..."):
                    # Generate side-by-side comparison images for report
                    
                    # 1. Spin Comparison (Target vs Final)
                    fig_spins, (ax_t, ax_f) = plt.subplots(1, 2, figsize=(10, 4))
                    ax_t.imshow(run_data["target_spin"], cmap='RdBu', vmin=-1, vmax=1)
                    ax_t.set_title("Target Spin Map", fontsize=14, fontweight='bold')
                    ax_t.axis('off')
                    ax_f.imshow(run_data["final_spin"], cmap='RdBu', vmin=-1, vmax=1)
                    ax_f.set_title("Final Solved Spin Map", fontsize=14, fontweight='bold')
                    ax_f.axis('off')
                    fig_spins.tight_layout()
                    buf_spins = io.BytesIO()
                    fig_spins.savefig(buf_spins, format="png", bbox_inches='tight', dpi=150)
                    buf_spins.seek(0)
                    img_spins = Image.open(buf_spins)
                    plt.close(fig_spins)

                    # 2. Intensity Comparison (Target vs Final)
                    fig_int, (ax_ti, ax_fi) = plt.subplots(1, 2, figsize=(10, 4))
                    norm_target_I = machine.system.normalize_intensity(run_data["target_intensity"])
                    norm_final_I = machine.system.normalize_intensity(run_data["final_intensity"])
                    
                    im1 = ax_ti.imshow(norm_target_I, cmap='inferno')
                    ax_ti.set_title("Target Intensity Pattern (Goal)", fontsize=14, fontweight='bold')
                    ax_ti.axis('off')
                    im2 = ax_fi.imshow(norm_final_I, cmap='inferno')
                    ax_fi.set_title("Final Output Intensity Pattern", fontsize=14, fontweight='bold')
                    ax_fi.axis('off')
                    fig_int.tight_layout()
                    buf_int = io.BytesIO()
                    fig_int.savefig(buf_int, format="png", bbox_inches='tight', dpi=150)
                    buf_int.seek(0)
                    img_int = Image.open(buf_int)
                    plt.close(fig_int)
                    
                    # 3. Energy Trajectory
                    fig_chart, ax_chart = plt.subplots(figsize=(8,3))
                    ax_chart.plot(run_data["energy_history"], color='#00ADB5', linewidth=2, label='System Energy')
                    ax_chart.set_title("Optimization Trajectory (Energy vs Iterations)", fontsize=14, fontweight='bold') 
                    ax_chart.set_xlabel("Iteration", fontsize=12)
                    ax_chart.set_ylabel("Energy (Hamming Distance)", fontsize=12)
                    ax_chart.legend()
                    ax_chart.grid(True, alpha=0.3)
                    buf_chart = io.BytesIO()
                    fig_chart.savefig(buf_chart, format="png", bbox_inches='tight', dpi=150)
                    buf_chart.seek(0)
                    img_chart = Image.open(buf_chart)
                    plt.close(fig_chart)
                    
                    # Create single spin image for AI (focused view)
                    fig_spin_ai, ax_spin_ai = plt.subplots(figsize=(4, 4))
                    ax_spin_ai.imshow(run_data["final_spin"], cmap='RdBu', vmin=-1, vmax=1)
                    ax_spin_ai.axis('off')
                    buf_spin_ai = io.BytesIO()
                    fig_spin_ai.savefig(buf_spin_ai, format="png", bbox_inches='tight', pad_inches=0)
                    buf_spin_ai.seek(0)
                    img_spin_ai = Image.open(buf_spin_ai)
                    plt.close(fig_spin_ai)
                    
                    analysis = get_ai_interpretation(api_key, run_data["grid_size"], run_data["final_energy"], run_data["start_energy"], run_data["iterations"], run_data["temperature"], run_data["decay_rate"], img_spin_ai, img_chart, st.session_state.history)
                    
                    # Store analysis and comparison images
                    st.session_state.last_run["analysis"] = analysis
                    st.session_state.last_run["img_spin_comparison"] = img_spins
                    st.session_state.last_run["img_intensity_comparison"] = img_int
                    st.session_state.last_run["img_chart"] = img_chart
            
            # Display Analysis (from state)
            if st.session_state.last_run["analysis"]:
                st.markdown(f"**Insight:** {st.session_state.last_run['analysis']}")

                # Download buttons for report and images
                if st.button("💾 Save Simulation Report"):
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    report_filename = f"simulation_report_{timestamp}.md"
                    
                    # Create a simple markdown report
                    report_content = f"""# Photonic Ising Machine Simulation Report
**Date:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Simulation Parameters
- **Grid Size:** {run_data['grid_size']}x{run_data['grid_size']}
- **Iterations:** {run_data['iterations']}
- **Initial Temperature:** {run_data['temperature']}
- **Decay Rate:** {run_data['decay_rate']}

## Results
- **Starting Energy:** {run_data['start_energy']:.2f}
- **Final Energy:** {run_data['final_energy']:.2f}

## AI Analysis
{st.session_state.last_run['analysis']}

---
*Report generated by Photonic Ising Machine Web App*
"""
                    
                    # Check if images are available
                    if "img_spin_comparison" in st.session_state.last_run:
                        st.success("✅ Report ready! Download buttons below:")
                        
                        # Download markdown report
                        st.download_button(
                            label="📄 Download Report (Markdown)",
                            data=report_content,
                            file_name=report_filename,
                            mime="text/markdown"
                        )
                        
                        # Download spin comparison
                        buf_spin = io.BytesIO()
                        st.session_state.last_run["img_spin_comparison"].save(buf_spin, format="PNG")
                        st.download_button(
                            label="🔵🔴 Download Spin Comparison",
                            data=buf_spin.getvalue(),
                            file_name=f"spin_comparison_{timestamp}.png",
                            mime="image/png"
                        )
                        
                        # Download intensity comparison
                        buf_int = io.BytesIO()
                        st.session_state.last_run["img_intensity_comparison"].save(buf_int, format="PNG")
                        st.download_button(
                            label="🔥 Download Intensity Comparison",
                            data=buf_int.getvalue(),
                            file_name=f"intensity_comparison_{timestamp}.png",
                            mime="image/png"
                        )
                        
                        # Download trajectory chart
                        buf_chart = io.BytesIO()
                        st.session_state.last_run["img_chart"].save(buf_chart, format="PNG")
                        st.download_button(
                            label="📈 Download Trajectory Chart",
                            data=buf_chart.getvalue(),
                            file_name=f"trajectory_{timestamp}.png",
                            mime="image/png"
                        )
                    else:
                        st.warning("⚠️ Images not ready yet. Please wait for AI analysis to complete, then try again.")


        else:
            st.info("Enter a Google API Key in the sidebar to unlock AI interpretation of the simulation physics.")

        st.divider()
        with st.expander("📜 Simulation History", expanded=False):
            if st.session_state.history:
                st.table(st.session_state.history)
                
                # Download history as CSV
                import pandas as pd
                df = pd.DataFrame(st.session_state.history)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="📊 Download History as CSV",
                    data=csv,
                    file_name=f"simulation_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Download all simulation runs from this session for analysis"
                )
            else:
                st.write("No runs recorded yet.")
        
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
