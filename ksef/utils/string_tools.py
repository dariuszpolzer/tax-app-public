import re
import unicodedata


def safe_filename(text: str) -> str:
    """
    Zamienia nazwę na bezpieczną dla plików:
    - usuwa polskie znaki
    - zamienia spacje na _
    - usuwa znaki specjalne
    """

    if not text:
        return "unknown"

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    text = text.replace(" ", "_")

    text = re.sub(r"[^A-Za-z0-9_]", "", text)

    return text
