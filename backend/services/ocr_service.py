import re
import hashlib
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein distance between two strings."""
    s1 = s1.lower().strip()
    s2 = s2.lower().strip()
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def string_similarity(s1: str, s2: str) -> float:
    """Returns normalized similarity ratio from 0.0 to 1.0 (1.0 = identical)."""
    s1_clean = re.sub(r'[^a-zA-Z0-9]', '', s1.lower())
    s2_clean = re.sub(r'[^a-zA-Z0-9]', '', s2.lower())
    if not s1_clean and not s2_clean:
        return 1.0
    if not s1_clean or not s2_clean:
        return 0.0
    dist = levenshtein_distance(s1_clean, s2_clean)
    max_len = max(len(s1_clean), len(s2_clean))
    return max(0.0, 1.0 - (dist / max_len))

def parse_canonical_date(d_str: str) -> Optional[Tuple[int, int, int]]:
    """Converts DD/MM/YYYY or YYYY-MM-DD or DD-MM-YYYY into (year, month, day)."""
    if not d_str:
        return None
    d_clean = re.sub(r'[^\d]', '-', d_str.strip())
    parts = [int(p) for p in d_clean.split('-') if p.isdigit()]
    if len(parts) == 3:
        if parts[0] > 1900:  # YYYY-MM-DD
            return (parts[0], parts[1], parts[2])
        elif parts[2] > 1900:  # DD-MM-YYYY
            return (parts[2], parts[1], parts[0])
    return None

class OCRService:
    @staticmethod
    def calculate_file_hash(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    @classmethod
    def parse_document_text(cls, raw_text: str, doc_type: str) -> Dict[str, Any]:
        """
        Parses raw text (from Tesseract or sample ID metadata) into structured fields.
        Supports PAN, Aadhaar, Driving Licence, and Salary Slips.
        """
        extracted = {
            "doc_type": doc_type,
            "raw_text_sample": raw_text[:200] if raw_text else "",
            "extracted_name": "",
            "extracted_dob": "",
            "extracted_id_number": "",
            "extra_fields": {}
        }
        
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        
        # 1. PAN Pattern: 5 letters + 4 digits + 1 letter (e.g. ABCDE1234F)
        pan_match = re.search(r'[A-Z]{5}[0-9]{4}[A-Z]', raw_text.upper())
        if pan_match:
            extracted["extracted_id_number"] = pan_match.group(0)
            
        # 2. Aadhaar Pattern: 12 digits (often 4 4 4)
        aadhaar_match = re.search(r'\b\d{4}\s?\d{4}\s?\d{4}\b', raw_text)
        if aadhaar_match and doc_type == "AADHAAR":
            extracted["extracted_id_number"] = aadhaar_match.group(0).replace(" ", "")

        # 3. Driving Licence Pattern
        dl_match = re.search(r'[A-Z]{2}[0-9]{2}[0-9A-Z]{7,11}', raw_text.upper())
        if dl_match and doc_type == "DRIVING_LICENSE":
            extracted["extracted_id_number"] = dl_match.group(0)

        # 4. DOB Pattern (DD/MM/YYYY or YYYY-MM-DD or DD-MM-YYYY)
        dob_match = re.search(r'\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})\b', raw_text)
        if dob_match:
            extracted["extracted_dob"] = dob_match.group(0)

        # 5. Name extraction heuristic
        for line in lines:
            if "name" in line.lower() and ":" in line:
                extracted["extracted_name"] = line.split(":", 1)[1].strip()
                break
            elif re.match(r'^[A-Z][a-zA-Z\s]{3,30}$', line) and not any(k in line.lower() for k in ["income", "tax", "department", "govt", "india", "republic", "card"]):
                if not extracted["extracted_name"]:
                    extracted["extracted_name"] = line.strip()

        return extracted

    @classmethod
    def match_identity_fields(
        cls,
        app_name: str,
        app_dob: str,
        app_id_number: str,
        extracted_data: Dict[str, Any]
    ) -> Tuple[float, bool, List[str]]:
        """
        Compares applicant input against OCR extracted fields using fuzzy matching.
        Returns: (overall_match_score_pct, is_verified_bool, mismatch_reasons_list)
        """
        reasons = []
        scores = []

        # Name Match (Fuzzy Levenshtein)
        extracted_name = extracted_data.get("extracted_name", "")
        if extracted_name:
            name_score = string_similarity(app_name, extracted_name)
            scores.append(name_score * 100.0)
            if name_score < 0.70:
                reasons.append(f"Name mismatch: Applied as '{app_name}', OCR extracted '{extracted_name}' (Score: {name_score*100:.1f}%)")
        else:
            scores.append(50.0)

        # ID Number Match
        extracted_id = extracted_data.get("extracted_id_number", "")
        if extracted_id:
            id_score = string_similarity(app_id_number, extracted_id)
            scores.append(id_score * 100.0)
            if id_score < 0.85:
                reasons.append(f"ID Number mismatch: Applied '{app_id_number}', OCR extracted '{extracted_id}'")
        else:
            scores.append(40.0)
            reasons.append("ID Number could not be detected from the document image.")

        # DOB Match with Canonical Date normalization
        extracted_dob = extracted_data.get("extracted_dob", "")
        if extracted_dob and app_dob:
            d_app = parse_canonical_date(app_dob)
            d_ocr = parse_canonical_date(extracted_dob)
            if d_app and d_ocr and d_app == d_ocr:
                scores.append(100.0)
            else:
                dob_sim = string_similarity(app_dob, extracted_dob)
                scores.append(dob_sim * 100.0)
                if dob_sim < 0.75:
                    reasons.append(f"DOB mismatch: Applied '{app_dob}', OCR extracted '{extracted_dob}'")

        overall_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        is_verified = (overall_score >= 75.0) and (len(reasons) == 0)

        return overall_score, is_verified, reasons
