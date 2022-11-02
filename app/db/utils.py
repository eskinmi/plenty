import string
import re


def norm_species(s: str):
    s = s.lower()
    s = s.strip()
    s = re.sub(r'[' + string.punctuation + ']', '', s)
    return s
