# snakeLLM

A Python application for snake species identification using Anthropic's Claude AI model.

## Prerequisites

- **Python 3.11 recommended** (Python 3.10-3.11 supported: `anthropic` and `pillow-heif` need 3.10+, and pandas 2.1.0 works best up to 3.11)
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

**If you only have Python 3.9 or lower, or if you have Python 3.12+:**
- **Recommended:** Download and install Python 3.11 from [python.org](https://www.python.org/downloads/release/python-3110/)
- Python 3.11 is compatible with all packages in this project (pandas 2.1.0 works best with Python 3.10-3.11)
- During installation on Windows, make sure to check "Add Python to PATH"
- After installation, restart your terminal/PowerShell

### 2. Create a Virtual Environment

**Important:** Use Python 3.11 (or Python 3.10) for best compatibility with pandas 2.1.0. Python 3.12+ may cause build errors.

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

# Other compatible version:
python3.10 -m venv venv

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

Create a `api_keys.py` file with your Anthropic API key (get one at [platform.claude.com](https://platform.claude.com)):

1. Copy the example file:
   ```bash
   cp api_keys.py.example api_keys.py
   ```

2. Edit `api_keys.py` and replace `your_api_key_here` with your actual API key:
   ```python
   ANTHROPIC_API_KEY = "your_actual_api_key_here"
   ```

**Note:** The `api_keys.py` file is gitignored and will not be committed to the repository, keeping your API key secure.

**Alternative:** You can also set the API key as an environment variable if you prefer:
- **Windows (PowerShell):** `$env:ANTHROPIC_API_KEY="YOUR_API_KEY"`
- **Windows (Command Prompt):** `set ANTHROPIC_API_KEY=YOUR_API_KEY`
- **macOS/Linux:** `export ANTHROPIC_API_KEY="YOUR_API_KEY"`

### 5. Run the Script

```bash
# Default model (claude-opus-5-5), sent through the Message Batches API
python matching.py

# Or choose a model
python matching.py --model claude-sonnet-5-5
python matching.py --model claude-haiku-5-5

# Send requests one at a time instead of as a batch
python matching.py --model claude-haiku-5-5 --mode direct
```

**Modes:**
- `batch` (default): requests are submitted through the Message Batches API, which costs 50% less. Because the photos are large, they are split into several batches of about 25 MB each. Results usually arrive within an hour (at most 24 hours). The batch IDs are saved to `batch_<model>_es.json`, so you can stop the script with Ctrl+C and run it again later to collect the results.
- `direct`: requests are sent one at a time, with results saved after each one.

The prompt and the diagnostic descriptions (from `data/Diagnósis Duellaman, Costa & Gunter.docx`, all authors combined per species) are in Spanish, and Claude answers in Spanish with `VEREDICTO: COINCIDE` or `VEREDICTO: NO COINCIDE`. Test images can be JPG, PNG or HEIC.

Results are saved per model to `results_<model>_es.csv` (e.g. `results_claude-sonnet-5-5_es.csv`, UTF-8 so Excel shows accents correctly), so runs can be compared across models. Each row records the `model`, the `mode`, the token usage (`input_tokens`, `output_tokens`, where output includes thinking tokens) and an estimated `cost_usd` based on list prices.

## Usage

The script checks every test photo against every species: for each of the four *Leptodeira* species (*L. annulata*, *L. approximans*, *L. ashmeadii*, *L. ornata*) it compares each candidate photo with that species' reference image and diagnostic descriptions, and records whether Claude judges it a match.

Expected data layout:
- Reference images: `data/reference/<species>_reference.PNG`, e.g. `data/reference/L. annulata_reference.PNG`
- Test photos, one folder per species: `data/test/<species>/`, e.g. `data/test/L. ornata/`. The folder name is the photo's true species, so the results can be scored later.

### Quick test before a full run

Run the cheapest model one request at a time, and stop it with Ctrl+C after a few images:

```bash
python matching.py --model claude-haiku-5-5 --mode direct
```

Check `results_claude-haiku-5-5_es.csv` (Spanish answers, verdicts in `is_match`, token usage and cost). Before the real run, delete that file or choose "Start fresh" when the script asks.
