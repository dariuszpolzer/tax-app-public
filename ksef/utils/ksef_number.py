import os
import re

# Format zgodny z nazwami plików z API KSeF, np.:
# ABC1234567-20260313-5D3A990000FD-B1
# DEF1234567-20260403-4B04D200000B-4D
# GHI1234567-20260401-755BEE800001-B8
KSEF_REGEX = re.compile(
    r"([1-9]((\d[1-9])|([1-9]\d))\d{7}|M\d{9}|[A-Z]{3}\d{7})-"
    r"(20[2-9][0-9]|2[1-9][0-9]{2}|[3-9][0-9]{3})"
    r"(0[1-9]|1[0-2])"
    r"(0[1-9]|[1-2][0-9]|3[0-1])-"
    r"([0-9A-F]{12})-([0-9A-F]{2})$",
    re.IGNORECASE,
)


def normalize_ksef_number(value: str) -> str:
    if not value:
        return ""
    return value.strip().upper()


def is_valid_ksef_number(value: str) -> bool:
    value = normalize_ksef_number(value)
    if not value:
        return False
    return bool(KSEF_REGEX.fullmatch(value))


def extract_ksef_number_from_filename(filename: str) -> str:
    """
    Zwraca NrKSeF z nazwy pliku, jeśli nazwa pliku jest numerem KSeF
    albo zawiera go w środku.
    """
    base = normalize_ksef_number(os.path.splitext(os.path.basename(filename))[0])

    if is_valid_ksef_number(base):
        return base

    match = KSEF_REGEX.search(base)
    if match:
        return match.group(0)

    return ""
