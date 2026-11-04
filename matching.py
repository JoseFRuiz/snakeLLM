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
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
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

# Let Pillow open iPhone .HEIC photos
register_heif_opener()

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
RESULTS_CSV = f"results_{MODEL}_es.csv"  # one results file per model (Spanish prompt), for later comparison
BATCH_STATE_FILE = f"batch_{MODEL}_es.json"  # tracks a submitted batch so an interrupted run can collect it later

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
MAX_BATCH_MB = 25  # upload size of each batch; the photos make one batch for every request too large

def image_to_block(image_path):
    """
    Loads an image, resizes it to Claude's recommended size, and returns it
    as a base64 image content block.
    """
    # Pillow detects the format from the file contents, not the extension
    # (e.g. the .DNG files in data/test are really JPEGs)
    image = Image.open(image_path)
    # Phone photos store their rotation in EXIF; apply it so the snake isn't sideways
    image = ImageOps.exif_transpose(image).convert("RGB")

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

def build_request_params(reference_image_path, new_image_path, species_name, descriptions):
    """
    Builds the Claude request that compares a new image against a reference image
    and the diagnostic descriptions of the species (one per author).
    Raises an exception if an image cannot be loaded.
    """
    descriptions_text = "\n".join(f"    - {author}: {text}" for author, text in descriptions)

    # 📝 Step 1: Craft the detailed, structured prompt (in Spanish)
    prompt = f"""
    Eres un herpetólogo experto que realiza la verificación de especies.

    La especie objetivo es *{species_name}*.

    --- MATERIALES DE REFERENCIA ---

    1.  **Imagen de referencia:** La primera imagen muestra los rasgos clave de la cabeza de un ejemplar confirmado de *{species_name}*.
    2.  **Descripciones diagnósticas (patrón de coloración), por autor:**
{descriptions_text}

    --- TAREA ---

    La segunda imagen es la **Imagen candidata** que se debe identificar.

    1.  **Compara** la imagen candidata con la imagen de referencia (morfología de la cabeza, patrón de escamas, características de los ojos) Y con las descripciones diagnósticas (patrón de la cabeza y del cuerpo).
    2.  **Determina** si la imagen candidata **COINCIDE** o **NO COINCIDE** con *{species_name}*.
    3.  **Explica brevemente** los rasgos que coinciden y los que no coinciden, tanto en la cabeza como en el cuerpo (si es visible), indicando en qué descripción se basa cada observación.

    Responde en español. La primera línea de tu respuesta debe ser exactamente "VEREDICTO: COINCIDE" o "VEREDICTO: NO COINCIDE",
    seguida de una breve justificación.
    """

    # 🔗 Step 2: Combine the prompt and images into one request
    content = [
        {"type": "text", "text": "Imagen de referencia:"},
        image_to_block(reference_image_path),
        {"type": "text", "text": "Imagen candidata:"},
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
    Parses the API response text to determine if it's a match (COINCIDE) or not (NO COINCIDE).
    Returns True for match, False for no match, None if unclear.
    """
    if not result_text or "Error:" in result_text:
        return None

    verdict = re.search(r"VEREDICTO:\s*(NO COINCIDE|COINCIDE)", result_text, re.IGNORECASE)
    if verdict:
        return verdict.group(1).upper() == "COINCIDE"

    # If we can't determine, return None
    return None

def make_result_row(reference_file, species, file_name, message, batch):
    """Builds one results.csv row from a Claude response, including its token usage and cost."""
    if message.stop_reason == "refusal":
        result_text = "Error: Claude se negó a responder esta solicitud"
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
            df = pd.read_csv(csv_path, encoding="utf-8-sig")
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
    # utf-8-sig so Excel shows accented characters (ó, á, ñ) correctly
    pd.DataFrame(result_list).to_csv(RESULTS_CSV, index=False, encoding="utf-8-sig")

def is_already_processed(reference_file, species, query_image, existing_results):
    """Check if a combination has already been processed."""
    return (reference_file, species, query_image) in existing_results

def save_batch_state(batches):
    """Saves the submitted batches that still have to be collected (deletes the file when none are left)."""
    if batches:
        with open(BATCH_STATE_FILE, "w") as f:
            json.dump({"batches": batches}, f, indent=2)
    elif os.path.exists(BATCH_STATE_FILE):
        os.remove(BATCH_STATE_FILE)

def submit_batches(pending):
    """
    Submits all pending combinations as Message Batches. The images make the requests large,
    so they are split into batches of about MAX_BATCH_MB each; one huge upload fails.
    Each batch ID is saved as soon as it is created, so the results can still be
    collected if the script is interrupted.
    Returns (list of submitted batches, number of combinations whose images could not be loaded).
    """
    batches = []
    load_errors = 0
    requests, request_map, chunk_bytes = [], {}, 0

    def submit_chunk():
        print(f"\n📤 Submitting batch {len(batches) + 1} with {len(requests)} requests (~{chunk_bytes / 1024 / 1024:.0f} MB)...")
        batch = client.messages.batches.create(requests=requests)
        batches.append({"batch_id": batch.id, "requests": request_map})
        save_batch_state(batches)
        print(f"   Batch ID: {batch.id} (saved to {BATCH_STATE_FILE})")

    for i, (reference, species, file_name) in enumerate(pending):
        reference_path = os.path.join("data", "reference", reference["file_name"])
        new_image_path = os.path.join("data", "test", species, file_name)
        try:
            params = build_request_params(reference_path, new_image_path, reference["species_name"], reference["descriptions"])
        except Exception as e:
            load_errors += 1
            print(f"  ❌ Error loading images for {reference['file_name']} / {species} / {file_name}: {e}")
            continue

        request_bytes = len(json.dumps(params))
        if requests and chunk_bytes + request_bytes > MAX_BATCH_MB * 1024 * 1024:
            submit_chunk()
            requests, request_map, chunk_bytes = [], {}, 0

        # custom_id only allows letters, digits, - and _, so map it back to the combination
        custom_id = f"req-{i}"
        requests.append(Request(custom_id=custom_id, params=MessageCreateParamsNonStreaming(**params)))
        request_map[custom_id] = [reference["file_name"], species, file_name]
        chunk_bytes += request_bytes

    if requests:
        submit_chunk()

    return batches, load_errors

def collect_batches(batches, result_list, existing_results):
    """
    Waits for each submitted batch to finish and adds its results.
    Failed requests are not saved, so they are retried on the next run.
    Returns (number processed, number of errors).
    """
    print(f"\n⏳ Waiting for {len(batches)} batch(es) to finish (usually within an hour).")
    print(f"   You can stop the script with Ctrl+C and run it again later to collect the results.")

    processed_count = 0
    error_count = 0
    while batches:
        state = batches[0]
        batch_id = state["batch_id"]

        while True:
            batch = client.messages.batches.retrieve(batch_id)
            if batch.processing_status == "ended":
                break
            counts = batch.request_counts
            print(f"   Batch {batch_id}: {batch.processing_status} - {counts.processing} processing, "
                  f"{counts.succeeded} succeeded, {counts.errored} errored")
            time.sleep(30)

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

        # Save the results before forgetting the batch, so nothing is lost or collected twice
        save_results(result_list)
        batches.pop(0)
        save_batch_state(batches)
        print(f"   ✓ Results of batch {batch_id} saved to {RESULTS_CSV}")

    return processed_count, error_count

# --- Execution ---
# Diagnostic descriptions per species and author, from data/Diagnósis Duellaman, Costa & Gunter.docx
leptodeira_annulata = {
    "file_name": "L. annulata_reference.PNG",
    "species_name": "Leptodeira annulata",
    "descriptions": [
        ("Duellman", "A veces, las manchas dorsales están interconectadas y forman una banda en zigzag a lo largo del dorso. "
                     "En algunos individuos, esta banda en zigzag puede ser recta y estrecha, dando la apariencia de una franja "
                     "dorsal media de color marrón oscuro. Las manchas laterales intercalares están ausentes o se presentan "
                     "únicamente como bordes oscurecidos de las escamas en las hileras 1 a 3. El color de la parte superior de "
                     "la cabeza varía de marrón claro a marrón grisáceo apagado. Por lo general carece de marcas, aunque a veces "
                     "presenta una franja tenue a lo largo del borde lateral de cada escama parietal."),
        ("Costa", "Región occipital de color marrón claro a marrón grisáceo, sin franjas; primera mancha dorsal en forma de "
                  "media luna, generalmente fusionada con otras manchas dorsales en el primer tercio del cuerpo, formando un "
                  "patrón en zigzag."),
    ]
    }
leptodeira_approximans = {
    "file_name": "L. approximans_reference.PNG",
    "species_name": "Leptodeira approximans",
    "descriptions": [
        ("Gunter", "Coloración pardusca, con una banda ondulada (en zigzag) de color marrón oscuro a lo largo del dorso. "
                   "Cabeza de color marrón oscuro, con una franja poco definida que va desde el ojo hacia la comisura de la "
                   "boca. Partes inferiores de color amarillento uniforme. A veces, el color de fondo es tan oscuro que la "
                   "banda dorsal apenas se distingue."),
        ("Costa", "Región occipital de color marrón claro a marrón grisáceo, sin franjas; primeras manchas dorsales del "
                  "cuerpo en forma de media luna, generalmente fusionadas con otras manchas dorsales en el primer tercio del "
                  "cuerpo, formando un patrón en zigzag."),
    ]
    }
leptodeira_ashmeadii = {
    "file_name": "L. ashmeadii_reference.PNG",
    "species_name": "Leptodeira ashmeadii",
    "descriptions": [
        ("Duellman", "La primera mancha del cuerpo está dividida a lo largo de la línea media por una franja del color de "
                     "fondo. En algunos individuos, la separación no es completa, de modo que el extremo posterior o el "
                     "anterior de la mancha —o ambos— pueden estar en contacto. Esta mancha se extiende hacia adelante por la "
                     "nuca hasta las escamas postparietales o el borde posterior de las parietales. La superficie dorsal de la "
                     "cabeza es de color marrón claro, con manchas irregulares de color marrón oscuro en las escamas "
                     "prefrontales, frontal y parietales. Estas manchas pueden ser pequeñas y dispersas, o bien más grandes y "
                     "centradas en la parte media de cada escama. Puede haber una franja de color marrón oscuro a lo largo del "
                     "borde lateral de la parietal que conecte con las manchas de la nuca en el borde posteromedial de dicha "
                     "escama."),
    ]
    }
leptodeira_ornata = {
    "file_name": "L. ornata_reference.PNG",
    "species_name": "Leptodeira ornata",
    "descriptions": [
        ("Duellman", "La parte superior de la cabeza es de color marrón grisáceo; a veces presenta manchas de color marrón "
                     "oscuro dispersas en las escamas frontales y parietales. En algunos ejemplares existe una franja fina en "
                     "la nuca —a menudo poco definida— que se extiende hacia atrás desde los bordes posteriores de las "
                     "parietales, abarcando una longitud de tres a cinco escamas. En estas serpientes, por lo general, está "
                     "presente la franja de la nuca, la cual puede estar conectada con la primera mancha del cuerpo. En algunos "
                     "individuos se observa una expansión lateral de la franja de la nuca hacia la parte anterior, formando una "
                     "marca en forma de T, cuyos brazos se extienden lateralmente sobre las escamas postparietales. Las manchas "
                     "dorsales del cuerpo son cortas y equivalen en longitud a los espacios dorsales intermedios. Las serpientes "
                     "de Chocó (Colombia) también presentan manchas corporales bastante cortas, pero suelen tener una franja "
                     "nucal poco definida."),
        ("Costa", "Región occipital de color marrón claro con una línea media ancha."),
    ]
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

# Batches submitted by an earlier, interrupted run: collect them, or discard them when starting fresh
if os.path.exists(BATCH_STATE_FILE):
    with open(BATCH_STATE_FILE) as f:
        previous_batches = json.load(f)["batches"]
    if start_fresh:
        print(f"\n🗑️  Discarding {len(previous_batches)} unfinished batch(es) from a previous run...")
        for previous in previous_batches:
            try:
                client.messages.batches.cancel(previous["batch_id"])
            except anthropic.APIStatusError:
                pass  # the batch has already ended
        save_batch_state([])
    else:
        print(f"\n📥 Found {len(previous_batches)} batch(es) from a previous run - collecting their results first...")
        batch_processed, batch_errors = collect_batches(previous_batches, result_list, existing_results)
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
    batches, load_errors = submit_batches(pending)
    error_count += load_errors
    if batches:
        batch_processed, batch_errors = collect_batches(batches, result_list, existing_results)
        processed_count += batch_processed
        error_count += batch_errors

elif pending and MODE == "direct":
    for position, (reference, species, file_name) in enumerate(pending, start=1):
        REFERENCE_IMAGE_PATH = os.path.join("data","reference",reference["file_name"])
        NEW_IMAGE_PATH = os.path.join("data","test",species,file_name)
        print(f"\n🔄 Processing [{position}/{len(pending)}]: {reference['file_name']} / {species} / {file_name}")

        try:
            params = build_request_params(REFERENCE_IMAGE_PATH, NEW_IMAGE_PATH, reference["species_name"], reference["descriptions"])
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
