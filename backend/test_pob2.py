import re

text = """ASSPORT
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

patterns = [
    (r'Mumbai[,\s]+(?:\')?INDIA', "Direct Mumbai pattern"),
    (r'([A-Z][a-z]+,\s*[\'"]?[A-Z]+)\s+(?:Date of issue|sex)', "Before next field"),
    (r'(?:place of birth|lugar de nacimiento|lieu de naissance)(?:[^\n]*?)\s*([A-Z][a-z]+(?:[,\s]+[A-Z]+)?)', "After label"),
]

for pattern, desc in patterns:
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        print(f"{desc}:")
        print(f"  Pattern: {pattern}")
        print(f"  Match: {m.group()}")
        if m.lastindex:
            print(f"  Group 1: {m.group(1)}")
        print()
