# snakeLLM

A Python application for snake species identification using Google's Gemini AI model.

## Setup

### 1. Create a Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

Once your virtual environment is activated, install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Set Up API Key

Create a `secrets.py` file with your Google Gemini API key:

1. Copy the example file:
   ```bash
   cp secrets.py.example secrets.py
   ```

2. Edit `secrets.py` and replace `your_api_key_here` with your actual API key:
   ```python
   GEMINI_API_KEY = "your_actual_api_key_here"
   ```

**Note:** The `secrets.py` file is gitignored and will not be committed to the repository, keeping your API key secure.

**Alternative:** You can also set the API key as an environment variable if you prefer:
- **Windows (PowerShell):** `$env:GEMINI_API_KEY="YOUR_API_KEY"`
- **Windows (Command Prompt):** `set GEMINI_API_KEY=YOUR_API_KEY`
- **macOS/Linux:** `export GEMINI_API_KEY="YOUR_API_KEY"`

### 4. Run the Script

```bash
python matching.py
```

## Usage

The script compares a candidate snake image against a reference image and text description to identify if it matches the species *Leptodeira annulata*.

Make sure you have:
- Reference image in `data/reference/L. annulata_referencia.PNG`
- Test image in `data/test/ICN_265.jpg`

## Troubleshooting

### NumPy/Pandas Import Error

If you encounter the error `ImportError: cannot import name randbits` or `Unable to import required dependencies: numpy: cannot import name randbits`, this indicates a corrupted or incompatible NumPy installation. To fix:

1. **Uninstall and reinstall numpy and pandas:**
   ```powershell
   pip uninstall numpy pandas -y
   pip install numpy==1.26.0 pandas==2.1.0
   ```

2. **If the above doesn't work, try a clean reinstall:**
   ```powershell
   # Remove the virtual environment and recreate it
   deactivate
   Remove-Item -Recurse -Force venv
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Alternative: Install without version constraints first:**
   ```powershell
   pip install --upgrade --force-reinstall numpy pandas
   ```