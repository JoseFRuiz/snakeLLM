import os
from google import genai
from PIL import Image
import pandas as pd

# Load API key from api_keys.py (gitignored file)
try:
    from api_keys import GEMINI_API_KEY
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
except ImportError:
    # Fallback: try to get from environment variable if api_keys.py doesn't exist
    if "GEMINI_API_KEY" not in os.environ:
        raise ValueError(
            "GEMINI_API_KEY not found. Please create an api_keys.py file with your API key, "
            "or set the GEMINI_API_KEY environment variable. See api_keys.py.example for reference."
        )

client = genai.Client()

def identify_snake_species(reference_image_path, new_image_path, description):
    """
    Uses the Gemini API to compare a new image against a reference image 
    and a text description for species verification.
    """
    try:
        # Load the images using Pillow
        reference_image = Image.open(reference_image_path)
        new_image = Image.open(new_image_path)
        
    except FileNotFoundError as e:
        return f"Error: One or more image files not found. Check the paths: {e}"


    # 📝 Step 1: Craft the detailed, structured prompt
    prompt = f"""
    You are an expert herpetologist performing species verification.
    
    The target species is *Leptodeira annulata*.
    
    --- REFERENCE MATERIALS ---
    
    1.  **Reference Image:** The first image provided shows the key head features of a confirmed *Leptodeira annulata*.
    2.  **Key Text Description (Dorsal Pattern):** "{description}"
    
    --- TASK ---
    
    The second image provided is the **Candidate Image** for identification.
    
    1.  **Compare** the Candidate Image against the Reference Image (head morphology, scale patterns, eye characteristics) AND the Key Text Description (body pattern characteristics).
    2.  **Determine** if the Candidate Image is a **MATCH** or **NO MATCH** for *Leptodeira annulata*.
    3.  **Provide a concise explanation** detailing the matching and non-matching features you observed in both the head and body (if visible).
    
    Format your response as a simple verdict followed by a brief justification.
    """

    # 🔗 Step 2: Combine the prompt and images for the API call
    contents = [
        reference_image,
        new_image,
        prompt
    ]

    # 🚀 Step 3: Call the Gemini API
    print("Sending request to Gemini model for analysis...")
    response = client.models.generate_content(
        model='gemini-2.5-flash', # Excellent multimodal capability and speed
        contents=contents
    )

    return response.text

def parse_match_result(result_text):
    """
    Parses the API response text to determine if it's a MATCH or NO MATCH.
    Returns True for match, False for no match, None if unclear.
    """
    if not result_text or "Error:" in result_text:
        return None
    
    result_lower = result_text.lower()
    
    # Check for explicit match indicators
    if "match" in result_lower:
        # Look for "no match" patterns first (more specific)
        if any(phrase in result_lower for phrase in ["no match", "not a match", "does not match", "non-match"]):
            return False
        # Check for positive match patterns
        elif any(phrase in result_lower for phrase in ["is a match", "matches", "match for"]):
            return True
    
    # If we can't determine, return None
    return None

def extract_explanation(result_text):
    """
    Extracts the explanation/justification from the API response.
    Returns the full result text as explanation (since it contains the explanation).
    """
    if not result_text or "Error:" in result_text:
        return result_text
    
    # The full result text contains the explanation, so return it
    # You could parse it further if needed, but for now return the full text
    return result_text

# --- Execution ---
# Your previous L. annulata description
leptodeira_annulata = {
    "file_name": "L. annulata_reference.PNG",
    "description": "First dorsal blotch with half-moon shape generally fused with other dorsal blotches in the first third of body forming a zigzag pattern."
    }
leptodeira_approximans = {
    "file_name": "L. approximans_reference.PNG",
    "description": "first dorsal blotches of the body with a half-moon shape, generally fused with other dorsal blotches in the first third of body forming a zig-zag pattern"
    }
leptodeira_ashmeadii = {
    "file_name": "L. ashmeadii_reference.PNG",
    "description": "two dark brown parallel stripes in the parietal region which run toward the occipitals; two occipital stripes extend to the body and fuse with the first dorsal blotch"
    }
leptodeira_ornata = {
    "file_name": "L. ornata_reference.PNG",
    "description": "occipital region light brown with medial wide line"
    }

reference_list = [leptodeira_annulata, leptodeira_approximans, leptodeira_ashmeadii, leptodeira_ornata]
species_list = ['L. annulata', 'L. approximans', 'L. ashmeadii', 'L. ornata']

result_list = []
for reference in reference_list:
    REFERENCE_IMAGE_PATH = os.path.join("data","reference",reference["file_name"])
    for species in species_list:
        file_name_list = os.listdir(os.path.join("data","test",species))
        for file_name in file_name_list:
            NEW_IMAGE_PATH = os.path.join("data","test",species,file_name)
            result = identify_snake_species(REFERENCE_IMAGE_PATH, NEW_IMAGE_PATH, reference["description"])
            is_match = parse_match_result(result)
            explanation = extract_explanation(result)
            dict_result = {
                "reference": reference["file_name"],
                "species": species,
                "query_image": file_name,
                "is_match": is_match,
                "explanation": explanation,
                "full_result": result
            }
            result_list.append(dict_result)

df = pd.DataFrame(result_list)
df.to_csv("results.csv", index=False)