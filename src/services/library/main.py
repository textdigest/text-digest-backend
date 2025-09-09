#TODO

import ocrmypdf
from pypdf import PdfReader 
import tempfile
import os

#UPLOAD TO S3


#Determine if text already parseable or if image scan 
def determine_OCR_status(path):
    reader = PdfReader(path)
    text = ""
    #We will have to determine that we have at least 3 pages first
    for page in reader.pages[:3]: #read 3 pages worth of content
        text += page.extract_text() or ""
    ocr_parseable = len(text.strip().split()) > 100 #Has at least 100 words within the first 3 pages
    out_fd, out_path = tempfile.mkstemp(suffix=".pdf")
    os.close(out_fd)
    return parse_text_using_OCR(path, skip_text=ocr_parseable, output_pdf=out_path)
    

def parse_text_using_OCR(input_pdf, output_pdf=None, skip_text=False, lang="eng"):
    ocrmypdf.ocr(
            input_pdf, output_pdf,
            skip_text=skip_text,
            deskew = (not skip_text), 
            rotate_pages = (not skip_text), 
            remove_background = (not skip_text),
            optimize=3,
            language=lang,  # requires you to have these tessdata files installed
            progress_bar=False,
    )
    return output_pdf

#Upload to S3 and return PDF
def upload_to_s3(client, pdf_bytes: bytes, filename: str, bucket: str, prefix: str = "uploads/") -> dict:
    """
    Write raw PDF bytes to /tmp, ensure searchable, upload to S3.
    Returns {bucket, key, s3_uri}.
    """
    # 1) Save incoming bytes to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_in:
        tmp_in.write(pdf_bytes)
        in_path = tmp_in.name

    try:
        # 2) Ensure it’s searchable (creates a new file)
        out_path = determine_OCR_status(in_path)

        # 3) Build S3 key and upload
        base_name = os.path.basename(filename) or os.path.basename(out_path)
        key = f"{prefix}{base_name.rsplit('.', 1)[0]}.searchable.pdf"

        client.upload_file(out_path, bucket, key, ExtraArgs={"ContentType": "application/pdf"})
        return {"bucket": bucket, "key": key, "s3_uri": f"s3://{bucket}/{key}"}
    finally:
        # 4) Cleanup temp files
        for p in (locals().get("in_path"), locals().get("out_path")):
            try:
                if p and os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
    


