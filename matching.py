import os
import io
import re
import json
import time
import base64
import argparse
import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from PIL import Image
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load API key from api_keys.py (gitignored file)
try:
    from api_keys import ANTHROPIC_API_KEY
    os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
except ImportError:
    # Fallback: try to get from environment variable if api_keys.py doesn't exist
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. Please create an api_keys.py file with your API key, "
            "or set the ANTHROPIC_API_KEY environment variable. See api_keys.py.example for reference."
        )

client = anthropic.Anthropic()

# Choose the model and mode from the command line, e.g.
#   python matching.py --model claude-sonnet-5-5
#   python matching.py --model claude-haiku-5-5 --mode direct
parser = argparse.ArgumentParser(description="Snake species verification with Claude")
parser.add_argument("--model", default="claude-opus-5-5",
                    help="Claude model ID to use (default: claude-opus-5-5)")
parser.add_argument("--mode", choices=["batch", "direct"], default="batch",
                    help="batch: send all requests through the Message Batches API (50%% cheaper, "
                         "results usually within an hour); direct: one request at a time (default: batch)")
args = parser.parse_args()

MODEL = args.model
MODE = args.mode
RESULTS_CSV = f"results_{MODEL}.csv"  # one results file per model, for later comparison
BATCH_STATE_FILE = f"batch_{MODEL}.json"  # tracks a submitted batch so an interrupted run can collect it later

# Standard prices in USD per 1M tokens (input, output); check current prices at claude.com/pricing.
# Batch requests are billed at 50% of these. Models not listed get an empty cost_usd.
PRICES = {
    "claude-fable-5-1": (10.00, 50.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-haiku-4-5": (1.00, 5.00),
}
BATCH_DISCOUNT = 0.5

def image_to_block(image_path):
    """
    Loads an image, resizes it to Claude's recommended size, and returns it
    as a base64 image content block.
    """
    image = Image.open(image_path).convert("RGB")

    # Claude downscales images whose long edge exceeds ~1568px, so resize up front
    # to keep requests small and under the per-image size limit
    max_size = (1568, 1568)
    if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": base64.standard_b64encode(buffer.getvalue()).decode("utf-8"),
        },
    }

def build_request_params(reference_image_path, new_image_path, species_name, description):
    """
    Builds the Claude request that compares a new image against a reference image
    and a text description for species verification.
    Raises an exception if an image cannot be loaded.
    """
    # 📝 Step 1: Craft the detailed, structured prompt
    prompt = f"""
    You are an expert herpetologist performing species verification.

    The target species is *{species_name}*.

    --- REFERENCE MATERIALS ---

    1.  **Reference Image:** The first image provided shows the key head features of a confirmed *{species_name}*.
    2.  **Key Text Description (Dorsal Pattern):** "{description}"

    --- TASK ---

    The second image provided is the **Candidate Image** for identification.

    1.  **Compare** the Candidate Image against the Reference Image (head morphology, scale patterns, eye characteristics) AND the Key Text Description (body pattern characteristics).
    2.  **Determine** if the Candidate Image is a **MATCH** or **NO MATCH** for *{species_name}*.
    3.  **Provide a concise explanation** detailing the matching and non-matching features you observed in both the head and body (if visible).

    Start your response with a first line that is exactly "VERDICT: MATCH" or "VERDICT: NO MATCH",
    followed by a brief justification.
    """

    # 🔗 Step 2: Combine the prompt and images into one request
    content = [
        {"type": "text", "text": "Reference Image:"},
        image_to_block(reference_image_path),
        {"type": "text", "text": "Candidate Image:"},
        image_to_block(new_image_path),
        {"type": "text", "text": prompt}
    ]

    return {
        "model": MODEL,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": content}]
    }

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((
        anthropic.APIConnectionError,  # includes timeouts
        anthropic.RateLimitError,
        anthropic.InternalServerError
    ))
)
def send_direct_request(params):
    """Sends a single request to the Claude API (used in direct mode)."""
    try:
        return client.messages.create(**params)
    except Exception as e:
        print(f"  ⚠️  Error calling Claude API: {str(e)}")
        raise  # Re-raise to trigger retry mechanism

def estimate_cost(input_tokens, output_tokens, batch):
    """Estimates the cost in USD of one request from its token usage."""
    if MODEL not in PRICES:
        return None
    input_price, output_price = PRICES[MODEL]
    cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
    if batch:
        cost *= BATCH_DISCOUNT
    return round(cost, 6)

def parse_match_result(result_text):
    """
    Parses the API response text to determine if it's a MATCH or NO MATCH.
    Returns True for match, False for no match, None if unclear.
    """
    if not result_text or "Error:" in result_text:
        return None

    verdict = re.search(r"VERDICT:\s*(NO MATCH|MATCH)", result_text, re.IGNORECASE)
    if verdict:
        return verdict.group(1).upper() == "MATCH"

    # If we can't determine, return None
    return None

def make_result_row(reference_file, species, file_name, message, batch):
    """Builds one results.csv row from a Claude response, including its token usage and cost."""
    if message.stop_reason == "refusal":
        result_text = "Error: Claude declined to answer this request"
    else:
        result_text = "".join(block.text for block in message.content if block.type == "text")

    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens  # includes thinking tokens
    return {
        "model": MODEL,
        "mode": "batch" if batch else "direct",
        "reference": reference_file,
        "species": species,
        "query_image": file_name,
        "is_match": parse_match_result(result_text),
        "result_text": result_text.replace("\n", " "),  # remove line breaks from result
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": estimate_cost(input_tokens, output_tokens, batch)
    }

def load_existing_results(csv_path=RESULTS_CSV):
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
            print(f"Warning: Could not load existing {csv_path}: {e}")
            return pd.DataFrame(), set()
    return pd.DataFrame(), set()

def save_results(result_list):
    """Save all results collected so far."""
    pd.DataFrame(result_list).to_csv(RESULTS_CSV, index=False)

def is_already_processed(reference_file, species, query_image, existing_results):
    """Check if a combination has already been processed."""
    return (reference_file, species, query_image) in existing_results

def submit_batch(pending):
    """
    Submits all pending combinations as one Message Batch and saves the batch ID,
    so the results can still be collected if the script is interrupted.
    Returns (batch state, number of images that could not be loaded).
    """
    requests = []
    request_map = {}
    load_errors = 0
    for i, (reference, species, file_name) in enumerate(pending):
        reference_path = os.path.join("data", "reference", reference["file_name"])
        new_image_path = os.path.join("data", "test", species, file_name)
        try:
            params = build_request_params(reference_path, new_image_path, reference["species_name"], reference["description"])
        except Exception as e:
            load_errors += 1
            print(f"  ❌ Error loading images for {reference['file_name']} / {species} / {file_name}: {e}")
            continue

        # custom_id only allows letters, digits, - and _, so map it back to the combination
        custom_id = f"req-{i}"
        requests.append(Request(custom_id=custom_id, params=MessageCreateParamsNonStreaming(**params)))
        request_map[custom_id] = [reference["file_name"], species, file_name]

    if not requests:
        return None, load_errors

    print(f"\n📤 Submitting batch with {len(requests)} requests...")
    batch = client.messages.batches.create(requests=requests)
    state = {"batch_id": batch.id, "requests": request_map}
    with open(BATCH_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    print(f"   Batch ID: {batch.id} (saved to {BATCH_STATE_FILE})")
    return state, load_errors

def collect_batch(state, result_list, existing_results):
    """
    Waits for a submitted batch to finish and adds its results.
    Failed requests are not saved, so they are retried on the next run.
    Returns (number processed, number of errors).
    """
    batch_id = state["batch_id"]
    print(f"\n⏳ Waiting for batch {batch_id} to finish (usually within an hour).")
    print(f"   You can stop the script with Ctrl+C and run it again later to collect the results.")

    while True:
        batch = client.messages.batches.retrieve(batch_id)
        if batch.processing_status == "ended":
            break
        counts = batch.request_counts
        print(f"   Status: {batch.processing_status} - {counts.processing} processing, "
              f"{counts.succeeded} succeeded, {counts.errored} errored")
        time.sleep(30)

    processed_count = 0
    error_count = 0
    # Results arrive in any order, so look each one up by its custom_id
    for item in client.messages.batches.results(batch_id):
        reference_file, species, file_name = state["requests"][item.custom_id]
        if item.result.type == "succeeded":
            row = make_result_row(reference_file, species, file_name, item.result.message, batch=True)
            if row["result_text"].startswith("Error:"):
                error_count += 1
                print(f"  ❌ {reference_file} / {species} / {file_name}: {row['result_text']}")
            result_list.append(row)
            existing_results.add((reference_file, species, file_name))
            processed_count += 1
        else:
            error_count += 1
            print(f"  ❌ {reference_file} / {species} / {file_name}: {item.result.type} (will be retried on the next run)")

    save_results(result_list)
    os.remove(BATCH_STATE_FILE)
    print(f"   ✓ Batch results saved to {RESULTS_CSV}")
    return processed_count, error_count

# --- Execution ---
# Your previous L. annulata description
leptodeira_annulata = {
    "file_name": "L. annulata_reference.PNG",
    "species_name": "Leptodeira annulata",
    "description": "First dorsal blotch with half-moon shape generally fused with other dorsal blotches in the first third of body forming a zigzag pattern."
    }
leptodeira_approximans = {
    "file_name": "L. approximans_reference.PNG",
    "species_name": "Leptodeira approximans",
    "description": "first dorsal blotches of the body with a half-moon shape, generally fused with other dorsal blotches in the first third of body forming a zig-zag pattern"
    }
leptodeira_ashmeadii = {
    "file_name": "L. ashmeadii_reference.PNG",
    "species_name": "Leptodeira ashmeadii",
    "description": "two dark brown parallel stripes in the parietal region which run toward the occipitals; two occipital stripes extend to the body and fuse with the first dorsal blotch"
    }
leptodeira_ornata = {
    "file_name": "L. ornata_reference.PNG",
    "species_name": "Leptodeira ornata",
    "description": "occipital region light brown with medial wide line"
    }

reference_list = [leptodeira_annulata, leptodeira_approximans, leptodeira_ashmeadii, leptodeira_ornata]
species_list = ['L. annulata', 'L. approximans', 'L. ashmeadii', 'L. ornata']

print(f"\nUsing model: {MODEL} ({MODE} mode)")
print(f"Results file: {RESULTS_CSV}")

# Check if this model's results file exists and ask user what to do
existing_df, existing_results = load_existing_results()
start_fresh = False

if len(existing_results) > 0:
    print(f"\nFound existing {RESULTS_CSV} with {len(existing_df)} entries.")
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
            start_fresh = True
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")
else:
    print(f"\nNo existing {RESULTS_CSV} found. Starting from zero...")
    result_list = []

processed_count = 0
error_count = 0

# A batch submitted by an earlier, interrupted run: collect it, or discard it when starting fresh
if os.path.exists(BATCH_STATE_FILE):
    with open(BATCH_STATE_FILE) as f:
        previous_state = json.load(f)
    if start_fresh:
        print(f"\n🗑️  Discarding unfinished batch {previous_state['batch_id']} from a previous run...")
        try:
            client.messages.batches.cancel(previous_state["batch_id"])
        except anthropic.APIStatusError:
            pass  # the batch has already ended
        os.remove(BATCH_STATE_FILE)
    else:
        print(f"\n📥 Found batch {previous_state['batch_id']} from a previous run - collecting its results first...")
        batch_processed, batch_errors = collect_batch(previous_state, result_list, existing_results)
        processed_count += batch_processed
        error_count += batch_errors

# Find every combination that still needs to be processed
# For each reference, we process all species, and for each species, all files
total_combinations = 0
skipped_count = 0  # Count of items already processed in an earlier run
pending = []
for reference in reference_list:
    for species in species_list:
        for file_name in os.listdir(os.path.join("data","test",species)):
            total_combinations += 1
            if is_already_processed(reference["file_name"], species, file_name, existing_results):
                skipped_count += 1
                continue
            pending.append((reference, species, file_name))

print(f"\n{len(pending)} of {total_combinations} combinations to process ({skipped_count} already done).")

if pending and MODE == "batch":
    state, load_errors = submit_batch(pending)
    error_count += load_errors
    if state:
        batch_processed, batch_errors = collect_batch(state, result_list, existing_results)
        processed_count += batch_processed
        error_count += batch_errors

elif pending and MODE == "direct":
    for position, (reference, species, file_name) in enumerate(pending, start=1):
        REFERENCE_IMAGE_PATH = os.path.join("data","reference",reference["file_name"])
        NEW_IMAGE_PATH = os.path.join("data","test",species,file_name)
        print(f"\n🔄 Processing [{position}/{len(pending)}]: {reference['file_name']} / {species} / {file_name}")

        try:
            params = build_request_params(REFERENCE_IMAGE_PATH, NEW_IMAGE_PATH, reference["species_name"], reference["description"])
            message = send_direct_request(params)
            row = make_result_row(reference["file_name"], species, file_name, message, batch=False)

            # Check if result contains an error (still saved)
            if row["result_text"].startswith("Error:"):
                error_count += 1
                print(f"  ❌ {row['result_text']}")
            else:
                print(f"  ✓ Analysis complete ({row['input_tokens']} in / {row['output_tokens']} out tokens)")

            result_list.append(row)
            processed_count += 1

            # Save progress after each successful processing
            save_results(result_list)

            # Add delay between requests to avoid rate limiting
            time.sleep(1)  # 1 second delay between requests

        except Exception as e:
            error_count += 1
            print(f"  ❌ Error processing {file_name}: {e}")
            # Continue with next image even if one fails
            continue

# Summarize token usage and cost across everything saved for this model
summary_df = pd.DataFrame(result_list)

print(f"\n✅ All processing complete!")
print(f"   Model: {MODEL}")
print(f"   Total: {total_combinations} combinations")
print(f"   Processed: {processed_count}")
print(f"   Skipped (already done): {skipped_count}")
print(f"   Errors: {error_count}")
if "cost_usd" in summary_df:
    print(f"   Input tokens: {int(summary_df['input_tokens'].sum())}")
    print(f"   Output tokens: {int(summary_df['output_tokens'].sum())}")
    print(f"   Estimated cost: ${summary_df['cost_usd'].sum():.4f}")
print(f"   Final results saved to {RESULTS_CSV}")
