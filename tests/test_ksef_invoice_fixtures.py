from pathlib import Path

import pytest

from ksef.parser import KSeFParser

FIXTURE_DIR = Path("tests/data/ksef")
MY_NIP = "1234567890"


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        (
            "fa_services_books_software.xml",
            {
                "numer": "FV/USL-KS-OPR/1/2026",
                "positions": 3,
                "netto": 1500.00,
                "vat": 345.00,
                "stawki": [23.0],
                "procedury": [],
                "names": [
                    "Usługa konsultingowa",
                    "Książka branżowa",
                    "Licencja oprogramowania",
                ],
            },
        ),
        (
            "fa_foreign_eu_np.xml",
            {
                "numer": "FV/EU-NP/2/2026",
                "positions": 1,
                "netto": 800.00,
                "vat": 0.00,
                "stawki": [],
                "procedury": ["NP"],
                "names": ["Usługa B2B dla odbiorcy UE"],
            },
        ),
        (
            "fa_foreign_non_eu_zero.xml",
            {
                "numer": "FV/EXPORT-0/3/2026",
                "positions": 1,
                "netto": 1200.00,
                "vat": 0.00,
                "stawki": [0.0],
                "procedury": [],
                "names": ["Eksport oprogramowania poza UE"],
            },
        ),
        (
            "fa_corrections_oo.xml",
            {
                "numer": "KOR/IL-WAR-OO/4/2026",
                "positions": 3,
                "netto": -350.00,
                "vat": -23.00,
                "stawki": [0.0, 23.0],
                "procedury": ["OO"],
                "names": [
                    "Korekta ilościowa - zwrot usługi",
                    "Korekta wartościowa - rabat na książki",
                    "Odwrotne obciążenie - komponent oprogramowania",
                ],
            },
        ),
    ],
)
def test_ksef_invoice_fixtures_cover_common_business_cases(filename, expected):
    parser = KSeFParser(my_nip=MY_NIP)

    invoice = parser.parse(str(FIXTURE_DIR / filename))

    assert invoice.meta["typ"] == "sprzedaz"
    assert invoice.meta["numer"] == expected["numer"]
    assert invoice.meta["liczba_pozycji"] == expected["positions"]
    assert invoice.meta["netto_razem"] == expected["netto"]
    assert invoice.meta["vat_razem"] == expected["vat"]
    assert invoice.meta["stawki"] == expected["stawki"]
    assert invoice.meta["kontrola_sum"]["all_ok"] is True
    assert [position.nazwa for position in invoice.pozycje] == expected["names"]

    procedures = sorted(
        procedure
        for position in invoice.pozycje
        for procedure in (position.procedury or [])
    )
    assert procedures == expected["procedury"]


def test_ksef_foreign_recipients_without_polish_nip_are_still_sales():
    parser = KSeFParser(my_nip=MY_NIP)

    eu_invoice = parser.parse(str(FIXTURE_DIR / "fa_foreign_eu_np.xml"))
    non_eu_invoice = parser.parse(str(FIXTURE_DIR / "fa_foreign_non_eu_zero.xml"))

    assert eu_invoice.meta["typ"] == "sprzedaz"
    assert eu_invoice.pozycje[0].kontrahent.nip == ""
    assert eu_invoice.pozycje[0].kontrahent.nazwa == "EU Customer GmbH"

    assert non_eu_invoice.meta["typ"] == "sprzedaz"
    assert non_eu_invoice.pozycje[0].kontrahent.nip == ""
    assert non_eu_invoice.pozycje[0].kontrahent.nazwa == "Non EU Customer Ltd."


def test_ksef_correction_fixture_preserves_negative_values():
    parser = KSeFParser(my_nip=MY_NIP)

    invoice = parser.parse(str(FIXTURE_DIR / "fa_corrections_oo.xml"))

    assert [position.netto for position in invoice.pozycje] == [-100.0, -50.0, -200.0]
    assert [position.vat for position in invoice.pozycje] == [-23.0, 0.0, 0.0]
