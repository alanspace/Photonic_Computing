# Large-Scale Photonic Ising Machine Simulation

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A high-performance Python simulation framework for **Photonic Ising Machines** based on Spatial Light Modulation (SLM). This repository provides a rigorous implementation of the optical physics governing the interaction of spins in a photonic system, aimed at solving combinatorial optimization problems.

## 🔬 Overview

Ising machines are physical devices designed to find the ground state of the Ising model, which maps to many NP-hard optimization problems. Photonic implementations leverage the massive parallelism of optics. 

This codebase simulates a specific architecture where a **Spatial Light Modulator (SLM)** encodes spin variables ($\sigma_i \in \{+1, -1\}$) as phase shifts (0 or $\pi$) in a coherent light beam. The interaction between spins is mediated by free-space diffraction and interference, computed efficiently using Fourier optics principles.

### Key Features
- **Rigorous Fourier Optics Model**: Simulates light propagation from the SLM plane to the camera (Fourier) plane.
- **Optimized Physics Engine**: Vectorized implementation of the interference integral, significantly faster than naive summation loops. ($O(NM)$ vs $O(N^2 M)$).
- **Modular Architecture**: Clean separation between core physics (`core.py`), machine logic (`ising_machine.py`), and utility/visualization layers.
- **Visualization Tools**: Built-in plotting for phase matrices and far-field intensity patterns.

## 🚀 Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/alanspace/Photonic_Computing.git
cd Photonic_Computing
pip install -e .
```

## 🗺️ How to Use This Repository

This repository contains both a **stable, optimized simulation library** and **exploratory research notebooks**. Here is a guide on how to navigate and use them.

### 1. The Quick Start (Run the optimized code)
If you want to see the simulation in action immediately:

1.  **Install the package**: `pip install -e .`
2.  **Run the demo**: `python examples/basic_simulation.py`
3.  **Check the output**: The script will generate a file named `simulation_result.png` in your current directory. This image displays the spin configuration (Phase Mask) alongside its corresponding far-field interference pattern (Fourier Intensity).

**What to expect:**
- **Output File**: A PNG image comparing the target spin configuration with the simulated optical intensity pattern. This proves the physics engine is correctly simulating interference.

### 2. The Interactive Web App (Real-Time Demo)
For a premium, interactive experience where you can watch the optimization process live:

```bash
streamlit run app.py
```

This launches a local web dashboard where you can:
- **Visualize** the spin phase mask and Fourier intensity in real-time.
- **Control** simulation parameters (Grid Size, Temperature, Iterations).
- **Run** the Metropolis-Hastings solver to see the energy minimize dynamically.

### 3. The Notebooks (Understand the Physics)
Located in `notebooks/`, these files contain the original research, derivations, and unoptimized prototype code. Use these if you want to understand the *why* and *how*.

- **`IsingMachine.ipynb`**: The **primary reference**. Contains detailed text explanations, mathematical derivations of the Fourier optics model, and step-by-step code blocks. **Read this first** to understand the theory.
- **`IsingMachine_Simplified.ipynb`**: A cleaner version of the above, focusing on the core algorithms without as much verbose exposition.
- **`SimplifiedNoteBook.ipynb`**: A bare-bones sandbox for quick experiments.

*Note: The code in notebooks is for educational/exploratory purposes and is O(N²M) (slower) compared to the O(NM) library implementation.*

### 4. The Library (Build your own experiments)
The `src/photonic_ising` directory contains the professional-grade, optimized Python package. Use this for:
- Building new simulations (e.g., larger spin counts).
- Integrating the Ising Machine logic into other pipelines.
- Running benchmarks.

**Key Modules:**
- `photonic_ising.core`: The vectorized physics engine (Fourier transforms, Sinc envelopes).
- `photonic_ising.ising_machine`: The class managing state (spins, Hamiltonian).
- `photonic_ising.visualization`: Tools for generating publication-quality plots.

## 📂 Repository Structure

- `examples/`: Ready-to-run scripts using the optimized library.
  - `basic_simulation.py`: Main entry point for a standard 10x10 simulation.
- `src/photonic_ising/`: The source code for the optimized package.
- `notebooks/`: Research and prototyping environment (Jupyter Notebooks).
- `tests/`: Unit tests to ensure physical accuracy.

## 🧪 Testing

Run the test suite to verify the installation and physics engine:

```bash
pytest tests/
```

## 📜 citation

If you use this code in your research, please cite the associated papers in `docs/references/`.
