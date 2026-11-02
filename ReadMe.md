## CS 424 - Fall 2026 Group Project: Analysis on UIC Student's Commute

**Group Members:** Masa Milojkovic, Sara Alaidroos, Shuroq Hussein

### Assignmemnt 1:

Assignment details and answers location in file "Assignment_1.md" 
Navigate Assignment 1 [here](Assignment-1) 

### Assignment 2

To set up the environment and run the code, follow the steps below.

#### 1. Set up the Virtual Environment

Run these commands in your terminal to create and activate the environment, and install the necessary packages:

```bash
# Create the virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On Mac/Linux:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate

# Install dependancies
pip install pandas plotly altair
```

#### 2. Run the Data Cleaning Script

The `datacleaning.py` script reads the raw form data from `data/raw/a2_commute_data.csv`. It renames the form questions to short column names, drops the timestamp, strips extra spaces, converts dates/times/numbers to proper types, and standardizes locations using `data/lookups/locations.csv`.

The cleaned output is saved to `data/processed/commutes_clean.csv`.

```bash
python Assignment 2/datacleaning.py
```

*(Note: When building charts, use the `location_clean` column.)*

#### 3. Run the Task 5 Visualization

To generate the interactive Vega-Lite dashboard, run the following script:

```bash
python Assignment 2/task5.py
```

This will output an HTML file. To view the interactive visualization, open `task5_dashboard.html` using Live Server in your code editor, or simply open it directly in your web browser.

#### 4. Results

Our final write up and results can be found [here](Assignment 2/assignment_2.md)
