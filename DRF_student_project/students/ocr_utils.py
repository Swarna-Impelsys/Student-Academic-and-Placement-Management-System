
import easyocr
import pymupdf

# Initialize the OCR reader once and reuse it.
_reader = None


def get_ocr_reader():
    global _reader

    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)

    return _reader


def extract_text_from_image(image_path):
    """
    Extract text from an image file.
    Returns the extracted text as a single string.
    """
    try:
        reader = get_ocr_reader()
        results = reader.readtext(image_path, detail=0)

        return "\n".join(results), ""

    except Exception as exc:
        return "", f"OCR processing failed: {exc}"


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    Uses PyMuPDF to extract existing text and OCR to read scanned pages.
    Returns the extracted text and an error message.
    """
    try:
        reader = get_ocr_reader()
        extracted_text = []

        with pymupdf.open(pdf_path) as pdf:
            for page in pdf:
                text = page.get_text().strip()

                if text:
                    extracted_text.append(text)
                else:
                    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                    image_bytes = pix.tobytes("png")

                    results = reader.readtext(image_bytes, detail=0)
                    extracted_text.append("\n".join(results))

        return "\n".join(extracted_text), ""

    except Exception as exc:
        return "", f"PDF OCR processing failed: {exc}"



def compare_document_text(extracted_text, requested_value, field_name):
    """
    Compare a requested profile value with extracted document text.

    Returns: match, mismatch, or unable_to_verify.
    This is a preliminary text check, not proof of document authenticity.
    """
    if not extracted_text or not extracted_text.strip():
        return "unable_to_verify"

    if not requested_value or not requested_value.strip():
        return "unable_to_verify"

    text = " ".join(extracted_text.casefold().split())
    requested = " ".join(requested_value.casefold().split())

    # Email and phone comparisons can use normalized exact matching.
    if field_name == "email":
        import re

        emails = re.findall(
            r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            extracted_text,
            flags=re.IGNORECASE,
        )

        if not emails:
            return "unable_to_verify"

        return (
            "match"
            if any(email.casefold() == requested for email in emails)
            else "mismatch"
        )

    if field_name == "phone":
        import re

        digits_requested = "".join(
            char for char in requested_value if char.isdigit()
        )
        digits_found = re.findall(r"\+?\d[\d\s().-]{7,}\d", extracted_text)

        if not digits_found or not digits_requested:
            return "unable_to_verify"

        normalized_numbers = [
            "".join(char for char in number if char.isdigit())
            for number in digits_found
        ]

        return (
            "match"
            if any(
                number == digits_requested
                or number.endswith(digits_requested)
                or digits_requested.endswith(number)
                for number in normalized_numbers
            )
            else "mismatch"
        )

    # For other fields, look for the requested value in the extracted text.
    if requested in text:
        return "match"

    # Avoid declaring mismatch if OCR text may be incomplete or ambiguous.
    if len(text) < 5:
        return "unable_to_verify"

    return "mismatch"
