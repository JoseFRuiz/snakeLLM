# snakeLLM

A Python application for snake species identification using Google's Gemini AI model.

## Prerequisites

- **Python 3.11 recommended** (Python 3.9-3.11 compatible with numpy 1.26.0 and pandas 2.1.0)
  - **Note:** Python 3.12+ may have compatibility issues with pandas 2.1.0 (build errors during installation)
  - Python 3.11 is the recommended version for this project
  - Download Python 3.11 from [python.org](https://www.python.org/downloads/release/python-3110/)
  - **Important:** Make sure to check the "Add Python to PATH" option during installation on Windows

## Setup

### 1. Check Your Python Version

**Windows (PowerShell):**
```powershell
# First, deactivate any active virtual environment
deactivate

# Check your system Python version
python --version

# If that doesn't work, try:
Get-Command python | Select-Object -ExpandProperty Source

# Or check common installation paths (Python 3.11 recommended):
& "C:\Program Files\Python311\python.exe" --version
& "C:\Program Files\Python310\python.exe" --version
& "C:\Program Files\Python39\python.exe" --version
```

**macOS/Linux:**
```bash
# Check your system Python version
python3 --version
```

**If you only have Python 3.8 or lower, or if you have Python 3.12+:**
- **Recommended:** Download and install Python 3.11 from [python.org](https://www.python.org/downloads/release/python-3110/)
- Python 3.11 is compatible with all packages in this project (pandas 2.1.0 works best with Python 3.9-3.11)
- During installation on Windows, make sure to check "Add Python to PATH"
- After installation, restart your terminal/PowerShell

### 2. Create a Virtual Environment

**Important:** Use Python 3.11 (or Python 3.9-3.10) for best compatibility with pandas 2.1.0. Python 3.12+ may cause build errors.

**Windows:**
```powershell
# Recommended: Use Python 3.11 explicitly
python3.11 -m venv venv

# Or if Python 3.11 is your default python command:
python -m venv venv

# If you need to use full path to Python 3.11:
& "C:\Program Files\Python311\python.exe" -m venv venv

# If py launcher is available:
py -3.11 -m venv venv

# Activate the virtual environment
venv\Scripts\activate

# Verify the Python version in the venv (should be 3.11.x)
python --version
```

**macOS/Linux:**
```bash
# Recommended: Create virtual environment with Python 3.11
python3.11 -m venv venv

# Or if 3.11 is your default:
python3 -m venv venv

# Other compatible versions:
python3.10 -m venv venv
python3.9 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Verify the Python version in the venv (should be 3.11.x)
python --version
```

### 3. Install Dependencies

Once your virtual environment is activated, install the required packages:

```bash
pip install -r requirements.txt
```

### 4. Set Up API Key

Create a `api_keys.py` file with your Google Gemini API key:

1. Copy the example file:
   ```bash
   cp api_keys.py.example api_keys.py
   ```

2. Edit `api_keys.py` and replace `your_api_key_here` with your actual API key:
   ```python
   GEMINI_API_KEY = "your_actual_api_key_here"
   ```

**Note:** The `api_keys.py` file is gitignored and will not be committed to the repository, keeping your API key secure.

**Alternative:** You can also set the API key as an environment variable if you prefer:
- **Windows (PowerShell):** `$env:GEMINI_API_KEY="YOUR_API_KEY"`
- **Windows (Command Prompt):** `set GEMINI_API_KEY=YOUR_API_KEY`
- **macOS/Linux:** `export GEMINI_API_KEY="YOUR_API_KEY"`

### 5. Run the Script

```bash
python matching.py
```

## Usage

The script compares a candidate snake image against a reference image and text description to identify if it matches the species *Leptodeira annulata*.

Make sure you have:
- Reference image in `data/reference/L. annulata_referencia.PNG`
- Test image in `data/test/ICN_265.jpg`
