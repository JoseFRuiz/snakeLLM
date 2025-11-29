import os
import time
from google import genai
from PIL import Image
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

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

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((
        httpx.RemoteProtocolError, 
        httpx.ConnectError, 
        httpx.TimeoutException,
        httpx.NetworkError,
        httpx.RequestError
    ))
)
def identify_snake_species(reference_image_path, new_image_path, description):
    """
    Uses the Gemini API to compare a new image against a reference image 
    and a text description for species verification.
    """
    try:
        # Load the images using Pillow
        reference_image = Image.open(reference_image_path)
        new_image = Image.open(new_image_path)
        
        # Resize images if they're too large to prevent timeout issues
        max_size = (2048, 2048)  # Maximum dimensions
        if reference_image.size[0] > max_size[0] or reference_image.size[1] > max_size[1]:
            reference_image.thumbnail(max_size, Image.Resampling.LANCZOS)
        if new_image.size[0] > max_size[0] or new_image.size[1] > max_size[1]:
            new_image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
    except FileNotFoundError as e:
        return f"Error: One or more image files not found. Check the paths: {e}"
    except Exception as e:
        return f"Error loading images: {e}"

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

    # 🚀 Step 3: Call the Gemini API with error handling
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',  # Excellent multimodal capability and speed
            contents=contents
        )
        return response.text
    except Exception as e:
        error_msg = f"Error calling Gemini API: {str(e)}"
        print(f"  ⚠️  {error_msg}")
        raise  # Re-raise to trigger retry mechanism

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

def load_existing_results(csv_path="results.csv"):
    """Load existing results from CSV file if it exists."""
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            # Create a set of tuples (reference, species, query_image) for quick lookup
            existing_results = set()
            for _, row in df.iterrows():
                existing_results.add((row['reference'], row['species'], row['query_image']))
            return df, existing_results
        except Exception as e:
            print(f"Warning: Could not load existing results.csv: {e}")
            return pd.DataFrame(), set()
    return pd.DataFrame(), set()

def is_already_processed(reference_file, species, query_image, existing_results):
    """Check if a combination has already been processed."""
    return (reference_file, species, query_image) in existing_results

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

# Check if results.csv exists and ask user what to do
existing_df, existing_results = load_existing_results()

if len(existing_results) > 0:
    print(f"\nFound existing results.csv with {len(existing_df)} entries.")
    print("Options:")
    print("  1. Resume - Continue from where you left off (skip already processed combinations)")
    print("  2. Start fresh - Delete existing results and start from zero")
    
    while True:
        choice = input("\nEnter your choice (1 for Resume, 2 for Start fresh): ").strip()
        if choice == "1":
            print("\n✓ Resuming from existing results...")
            result_list = existing_df.to_dict('records')
            break
        elif choice == "2":
            print("\n✓ Starting fresh - existing results will be overwritten...")
            result_list = []
            existing_results = set()  # Clear existing results
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")
else:
    print("\nNo existing results.csv found. Starting from zero...")
    result_list = []

# Calculate total combinations first
# For each reference, we process all species, and for each species, all files
total_combinations = 0
for reference in reference_list:
    for species in species_list:
        test_dir = os.path.join("data","test",species)
        if os.path.exists(test_dir):
            total_combinations += len(os.listdir(test_dir))

# Process all combinations
processed_count = 0
skipped_count = 0  # Count of items skipped in current run
error_count = 0
current_position = 0  # Current position in the total

for reference in reference_list:
    REFERENCE_IMAGE_PATH = os.path.join("data","reference",reference["file_name"])
    for species in species_list:
        file_name_list = os.listdir(os.path.join("data","test",species))
        for file_name in file_name_list:
            current_position += 1
            
            # Check if already processed
            if is_already_processed(reference["file_name"], species, file_name, existing_results):
                skipped_count += 1
                print(f"⏭️  Skipping [{current_position}/{total_combinations}]: {reference['file_name']} / {species} / {file_name} (already processed)")
                continue
            
            NEW_IMAGE_PATH = os.path.join("data","test",species,file_name)
            print(f"\n🔄 Processing [{current_position}/{total_combinations}]: {reference['file_name']} / {species} / {file_name}")
            
            try:
                result = identify_snake_species(REFERENCE_IMAGE_PATH, NEW_IMAGE_PATH, reference["description"])
                
                # Check if result contains an error
                if "Error:" in result or "Error calling Gemini API" in result:
                    error_count += 1
                    print(f"  ❌ {result}")
                    # Still save the error result
                    is_match = None
                else:
                    is_match = parse_match_result(result)
                    print(f"  ✓ Analysis complete")
                
                result = result.replace("\n", " ")  # remove line breaks from result
                dict_result = {
                    "reference": reference["file_name"],
                    "species": species,
                    "query_image": file_name,
                    "is_match": is_match,
                    "result_text": result
                }
                result_list.append(dict_result)
                processed_count += 1
                
                # Save progress after each successful processing
                df = pd.DataFrame(result_list)
                df.to_csv("results.csv", index=False)
                
                # Add delay between requests to avoid rate limiting
                time.sleep(1)  # 1 second delay between requests
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ Error processing {file_name}: {e}")
                # Continue with next image even if one fails
                continue

    print(f"\n📊 Progress for {reference['file_name']}: {processed_count} processed, {skipped_count} skipped, {error_count} errors")
    print(f"   Results saved to results.csv")

print(f"\n✅ All processing complete!")
print(f"   Total: {total_combinations} combinations")
print(f"   Processed: {processed_count}")
print(f"   Skipped (already done): {skipped_count}")
print(f"   Errors: {error_count}")
print(f"   Final results saved to results.csv")