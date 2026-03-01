# MRP & Production Optimization Tool

## Overview
This project is a comprehensive desktop application developed with Python, designed to solve complex Material Requirements Planning (MRP) and Production Optimization problems. It transforms Bill of Materials (BOM) data into actionable production and purchasing schedules.

## Key Features
* **BOM Visualization & Matrix Calculations:** Reads product structures from JSON files and automatically calculates the N and T matrices for sub-assembly requirements.
* **Automated MRP Generation:** Calculates gross requirements, net requirements, and planned order releases considering lead times and safety stocks.
* **Linear Programming (LP) Optimization:** Uses the `PuLP` library to minimize total production costs (hiring, firing, inventory, overtime, and sub-contracting) based on demand forecasts and constraints.
* **Interactive GUI:** Built with `Tkinter`, providing a user-friendly interface for inputting parameters and viewing generated schedules and visual charts (`Matplotlib`).

## Technologies Used
* **Language:** Python
* **Libraries:** `pandas`, `numpy`, `pulp` (for LP optimization), `tkinter` (GUI), `matplotlib` (data visualization)

## How to Run
1. Clone this repository.
2. Ensure you have the required libraries installed: `pip install pandas numpy pulp matplotlib`
3. Run the application: `python mrp_app.py`
4. The app uses sample BOM data (e.g., Bicycle) located in the `/urun_agaclari` folder.

*Note: This project was developed as part of an academic study in Industrial Engineering.*
