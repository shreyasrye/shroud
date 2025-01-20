# Redaction Tool Design Document

## **Scope**
Develop a redaction tool that can identify and redact sensitive (e.g., PII, PHI, PCI) and confidential (e.g., business targets, growth goals) information in documents. The tool will:
- Process and redact content based on customizable specifications provided in a plain text configuration file (`entities_to_redact.txt`).
- Use OpenAI's GPT-4 for all redaction tasks, ensuring flexibility and adaptability.
- Handle text, images, and multi-page continuity.
- Output redacted documents in a user-specified folder.

---

## **Requirements**

### **Functional Requirements**
1. **Input**:
   - Accept a folder containing PDF documents.
2. **Processing**:
   - Extract text and images using **PyMuPDF**.
   - Identify sensitive information based on specifications provided in `entities_to_redact.txt` using **GPT-4**.
   - Generate bounding boxes for identified entities and apply redactions.
   - Flatten PDF metadata to ensure no hidden information remains.
3. **Output**:
   - Save redacted documents in a specified output folder.
4. **Customization**:
   - Allow users to specify redactable entities in natural language or structured patterns within `entities_to_redact.txt`.

### **Non-Functional Requirements**
1. Preserve text/paragraph continuity across pages.
2. Efficiently handle multi-page documents and large volumes of data.

---

## **Workflow**

1. **Extract Text and Images**:
   - Use PyMuPDF's `get_text("dict")` to extract text as structured data, preserving layout and positional metadata.
   - Use `get_images()` to identify images and their metadata.

2. **Load Redaction Specifications**:
   - Read `entities_to_redact.txt` to extract redaction instructions.
   - The file can include specifications in natural language, such as:
     ```
     Redact all email addresses.
     Remove references to any person or organization.
     Mask any mention of revenue or financial targets.
     ```
   - Convert the specifications into prompts for GPT-4.

3. **Redact Sensitive Content**:
   - Feed text chunks to GPT-4 with the redaction specifications and extract flagged sensitive content.
   - Example prompt:
     ```
     Instructions: Redact the following sensitive information based on these criteria:
     - Email addresses
     - Names of people and organizations
     - Revenue or financial targets
     Text: "{chunk}"
     ```
   - Use the response to identify sensitive regions and corresponding bounding boxes for redaction.

4. **Generate Bounding Boxes**:
   - Use `search_for()` to locate GPT-4-identified text within the PDF and generate bounding boxes (`fitz.Rect`).
   - For images, use `get_image_bbox()` to locate regions specified for redaction.

5. **Apply Redactions**:
   - Add black rectangles to sensitive areas using `add_redact_annot()` for both text and image bounding boxes.
   - Permanently remove redacted content with `apply_redactions()`.

6. **Flatten and Save**:
   - Use `save(output_file, deflate=True)` to flatten the document, ensuring no hidden data remains.
   - Save the redacted files in the specified output folder.

---

## **Advantages of Using GPT-4**
1. **Flexibility**:
   - Capable of interpreting complex, user-defined redaction criteria in natural language.
   - Can redact nuanced, context-dependent information that traditional tools cannot handle.
2. **Adaptability**:
   - Works for any domain or type of sensitive information without requiring additional configurations or model retraining.
3. **Precision**:
   - Provides detailed redaction suggestions for ambiguous or contextual cases.

---

## **Use Case Example**
1. User creates an `entities_to_redact.txt` file with the following content:
