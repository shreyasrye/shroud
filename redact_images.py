import os
import fitz
import json
from PIL import Image
import io
from openai import OpenAI
import base64
from tqdm import tqdm

def load_redaction_specs(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: Specification file '{file_path}' not found.")
        raise

def encode_image(image):
    """
    Encode a PIL image into a Base64 string.
    """
    try:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        return base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image: {e}")
        raise

def extract_images_from_pdf(pdf_path):
    """
    Extract all images from a PDF and return them as a list of (page_number, image_object) tuples.
    """
    try:
        doc = fitz.open(pdf_path)
        images = []
        bboxes = {}

        for page_number in tqdm(range(len(doc)), desc="Extracting Images from PDF"):
            page = doc[page_number]
            image_list = page.get_images(full=True)

            for img in image_list:
                xref = img[0]
                bboxes[xref] = page.get_image_bbox(img)
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))
                images.append((page_number, image, xref))

        doc.close()
        return images, bboxes
    except Exception as e:
        print(f"Error extracting images from '{pdf_path}': {e}")
        raise

def detect_text_in_images(images, redaction_specs):
    """
    Use GPT-4 Vision to detect text in images and return a list of redaction entities.
    """
    try:
        with open("config.json") as config_file:
            config = json.load(config_file)
        client = OpenAI(api_key=config["openai"]["api_key"])

        entities_to_redact = []

        for page_number, image, xref in tqdm(images, desc="Detecting Text in Images"):
            base64_image = encode_image(image)

            with open("./prompts/redact_images_prompt.txt", "r") as prompt_file:
                redaction_prompt = prompt_file.read().strip()

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                {
                    "role": "user",
                    "content": [
                    {"type": "text", "text": redaction_prompt.format(redaction_specs=redaction_specs)},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
                ],
                max_tokens=300,
                response_format={"type": "json_object"},
                temperature=0.0
            )

            detected_text = response.choices[0].message.content
            detected_entities = json.loads(detected_text).get("redactions", [])

            if detected_entities:
                entities_to_redact.append((page_number, xref, detected_entities))

        return entities_to_redact
    except FileNotFoundError:
        print("Error: 'config.json' or prompt file not found.")
        raise
    except Exception as e:
        print(f"Error during text detection in images: {e}")
        raise

def redact_images_in_pdf(input_pdf, output_pdf, redacted_entities, img_bboxes):
    """
    Redact images in the PDF based on detected sensitive text.
    """
    try:
        doc = fitz.open(input_pdf)

        for page_number, xref, entities in tqdm(redacted_entities, desc="Redacting Images"):
            page = doc[page_number]

            image_list = page.get_images(full=True)
            image_bbox = None
            try:
                for item in image_list:
                    if item[0] == xref:
                        image_bbox = img_bboxes.get(xref)
                        break
                if not image_bbox:
                    print(f"Skipping xref {xref} on page {page_number}: No bounding box found.")
                    continue

                page.add_redact_annot(image_bbox, fill=(0, 0, 0))
                page.apply_redactions()
            except ValueError:
                print(f"Skipping xref {xref} on page {page_number}: Not a valid inline image.")

        doc.save(output_pdf, deflate=True)
        doc.close()
    except Exception as e:
        print(f"Error redacting images in PDF '{input_pdf}': {e}")
        raise

def process_pdf(input_folder, output_folder, redaction_specs):
    """
    Main function to process all PDFs in the input folder, extract images, detect sensitive text, and redact them.
    """
    try:
        for pdf_file in tqdm(os.listdir(input_folder), desc="Processing PDFs"):
            if pdf_file.endswith(".pdf"):
                input_pdf_path = os.path.join(input_folder, pdf_file)
                output_pdf_path = os.path.join(output_folder, pdf_file)

                images, bboxes = extract_images_from_pdf(input_pdf_path)
                redacted_entities = detect_text_in_images(images, redaction_specs)
                redact_images_in_pdf(input_pdf_path, output_pdf_path, redacted_entities, bboxes)
    except Exception as e:
        print(f"Error processing PDFs in folder '{input_folder}': {e}")
        raise

if __name__ == "__main__":
    PARTIALLY_REDACTED_FOLDER = "./partially_redacted_pdfs"
    OUTPUT_FOLDER = "./output_pdfs"
    SPEC_FILE = "./entities_to_redact.txt"

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    if not os.path.exists(PARTIALLY_REDACTED_FOLDER):
        os.makedirs(PARTIALLY_REDACTED_FOLDER)

    try:
        specs = load_redaction_specs(SPEC_FILE)
        process_pdf(PARTIALLY_REDACTED_FOLDER, OUTPUT_FOLDER, specs)
        print("Image-based redaction completed successfully.")
    except Exception as e:
        print(f"Critical error: {e}")
