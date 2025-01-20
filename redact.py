import os
import pymupdf  # PyMuPDF
import json
from openai import OpenAI

# Load redaction specifications from the configuration file
def load_redaction_specs(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

# Process each PDF in the input folder
def redact_pdf(input_folder, output_folder, redaction_specs):
    for pdf_file in os.listdir(input_folder):
        if pdf_file.endswith(".pdf"):
            process_pdf(os.path.join(input_folder, pdf_file), output_folder, redaction_specs)

# Process a single PDF file
def process_pdf(file_path, output_folder, redaction_specs):
    doc = pymupdf.open(file_path)
    with open("config.json") as config_file:
        config = json.load(config_file)
    client = OpenAI(api_key=config["openai"]["api_key"])
    
    for page_num, page in enumerate(doc):
        # Extract text with positional metadata
        page_data = page.get_text("dict")
        text_chunks = []
        for block in page_data["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text_chunks.append({
                        "text": span["text"],
                        "bounding_box": span["bbox"],
                        "page_number": page_num + 1
                    })
        
        prompt = f"Redaction Spefications: {redaction_specs}\n\n Text Chunks: {json.dumps(text_chunks)}\n\n{open(PROMPT_FILE).read()}"
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt},
            ],
            response_format={ "type": "json_object" },
            temperature=0.0
        )
        print(response.choices[0].message.content)
        redaction_data = json.loads(response.choices[0].message.content)

        # Apply redactions
        for item in redaction_data["redactions"]:
            rect = pymupdf.Rect(*item["bounding_box"])
            page.add_redact_annot(rect, fill=(0, 0, 0))
        
        page.apply_redactions()
    
    # Save the redacted PDF
    output_path = os.path.join(output_folder, os.path.basename(file_path))
    doc.save(output_path, deflate=True)
    doc.close()
    print(f"Processed and saved: {output_path}")

# Main function
if __name__ == "__main__":
    INPUT_FOLDER = "./input_pdfs"  # Folder containing input PDFs
    OUTPUT_FOLDER = "./output_pdfs"  # Folder to save redacted PDFs
    SPEC_FILE = "./entities_to_redact.txt"  # Redaction specifications
    PROMPT_FILE = "./redaction_prompt.txt"  # Prompt template file

    # Create output folder if it doesn't exist
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Load redaction specs and prompt template
    specs = load_redaction_specs(SPEC_FILE)

    # Process PDFs
    redact_pdf(INPUT_FOLDER, OUTPUT_FOLDER, specs)

    print("Redaction completed.")
