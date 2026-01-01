import sys
sys.path.append('d:/Cloud EL/Smart_Cloud_Vault/backend')

from ai_engine.govt_doc_normalizer import GovernmentDocumentNormalizer

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

normalizer = GovernmentDocumentNormalizer()
pob = normalizer._extract_place_of_birth(passport_ocr)
print(f"Place of Birth: {pob}")
