"""Test actual passport OCR from user."""

import sys
sys.path.append('d:/Cloud EL/Smart_Cloud_Vault/backend')

from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer

# Actual passport OCR from user
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
print("PASSPORT OCR - BEFORE FIX")
print("=" * 80)

normalizer = GovernmentDocumentNormalizer()
context = {'classification': 'government_id', 'confidence': 0.95, 'identity_signals': {'passport': True}}

normalized = normalizer.normalize_document(passport_ocr, context)
original = normalizer.format_normalized_document(normalized, mask=False, raw_text=passport_ocr)
masked = normalizer.format_normalized_document(normalized, mask=True, raw_text=passport_ocr)

print("\n📄 ORIGINAL:")
print("-" * 80)
print(original)

print("\n🔒 MASKED:")
print("-" * 80)
print(masked)

print("\n" + "=" * 80)
print("EXPECTED OUTPUT:")
print("=" * 80)
print("""
Name: RAHUL RAM GUPTA
Passport Number: 31195855
Nationality: United States of America
Gender: Male
Date of Birth: 2 Jan 1974
Valid Till: [Should extract from MRZ or data]

Place of Birth: Mumbai, INDIA
Address: [Should mask]
File Number: [Should mask if present]
""")
