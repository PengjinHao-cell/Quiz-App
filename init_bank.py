"""Initialize the question bank from the sample PDF."""
import json
import shutil
import os
import uuid
from datetime import datetime
from parser import parse_file

def main():
    src_pdf = "c:/Program/2026年上半年入党积极分子培训班(题库导出).pdf"
    uploads_dir = "c:/Program/quiz_app/uploads"
    data_dir = "c:/Program/quiz_app/data"
    bank_id = uuid.uuid4().hex[:12]
    original_filename = "2026年上半年入党积极分子培训班(题库导出).pdf"

    # Copy PDF (match naming convention used in app.py: {bank_id}_{original_filename})
    shutil.copy2(src_pdf, os.path.join(uploads_dir, f"{bank_id}_{original_filename}"))

    # Parse
    questions = parse_file(src_pdf, original_filename)
    print(f"Parsed {len(questions)} questions")

    # Save JSON
    bank_data = {
        "id": bank_id,
        "original_filename": original_filename,
        "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "questions": questions,
    }
    with open(os.path.join(data_dir, f"{bank_id}.json"), "w", encoding="utf-8") as f:
        json.dump(bank_data, f, ensure_ascii=False, indent=2)
    print(f"Saved bank {bank_id}")
    print(f"First 3 IDs: {[q['id'] for q in questions[:3]]}")


if __name__ == "__main__":
    main()