# Simulated Tempering implementation
# Copy this function to replace optimize_spins in app.py

def optimize_spins(machine, target_spin, iterations=500, temp=1.0, decay_rate=0.99, use_clusters=False, use_adaptive_temp=True):
    """
    Simulated Annealing with adaptive temperature control (Simulated Tempering).
    Monitors acceptance rate and adjusts temperature to maintain optimal exploration.
    """
    import numpy as np
    import streamlit as st
    import matplotlib.pyplot as plt
    
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
            caption += " (Adaptive Temp)"
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
