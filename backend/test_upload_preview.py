"""Test what text preview users see after upload."""

import sys
sys.path.append('d:/Cloud EL/Smart_Cloud_Vault/backend')

from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer

# Exact passport OCR from user
passport_ocr = """ASSPORT
SSEPORT

t

NP PN FAAS SEL 5
Type /Type/ Tipo "Coda! Cou

eS 31195855

Geven Names / Prénome /tombres

ity onal CCN
UNITED STATES OF AMERICA
Date de nuisance / Fecha de nacimiento
2 Jan 1974
eu de naissance / Lugar de nacimiento sex | Seat / Sexo
Mumbai, 'INDIA

Date of issue / Date

ce / Fecha de expedscate Aathonty /Autonité/ Aulondad
18 Sep 2005 United States
a oe ©" Department of State

SEEPAGE5|

P<USAGUPTA<<RAHUL<RAM<<<<<<<<<<<<<<<<<<
311958554USA1234567M 12345678901 23456<123456"""

print("=" * 80)
print("WHAT USER UPLOADS (Raw OCR - Messy):")
print("=" * 80)
print(passport_ocr[:500])
print("\n... (truncated)\n")

print("=" * 80)
print("WHAT USER SEES IN PREVIEW (After Normalization - Clean):")
print("=" * 80)

normalizer = GovernmentDocumentNormalizer()
context = {'classification': 'government_id', 'confidence': 0.95, 'identity_signals': {'passport': True}}

# This is what happens in the upload API
normalized = normalizer.normalize_document(passport_ocr, context)
formatted_text = normalizer.format_normalized_document(normalized, mask=False, raw_text=passport_ocr)

# This is what gets returned as "ocr_extracted_text" in the API response
preview = formatted_text[:500]  # First 500 chars

print(preview)
print("\n... (truncated to 500 chars)\n")

print("=" * 80)
print("FULL FORMATTED TEXT:")
print("=" * 80)
print(formatted_text)
