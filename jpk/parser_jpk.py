from decimal import Decimal

from defusedxml import ElementTree as ET

SALES_NET_FIELDS = [
    "K_10",
    "K_11",
    "K_13",
    "K_15",
    "K_17",
    "K_19",
    "K_21",
    "K_22",
    "K_23",
    "K_25",
    "K_27",
    "K_29",
    "K_31",
]

SALES_VAT_FIELDS = [
    "K_16",
    "K_18",
    "K_20",
    "K_24",
    "K_26",
    "K_28",
    "K_30",
    "K_32",
    "K_33",
    "K_34",
]

PURCHASE_NET_FIELDS_V7 = ["K_40", "K_42"]
PURCHASE_VAT_FIELDS_V7 = ["K_41", "K_43", "K_44", "K_45", "K_46", "K_47"]

PURCHASE_NET_FIELDS_OLD = ["K_43", "K_45"]
PURCHASE_VAT_FIELDS_OLD = ["K_44", "K_46", "K_47", "K_48", "K_49", "K_50"]


def dec(value: str | None) -> Decimal:
    if not value:
        return Decimal("0.00")
    return Decimal(value.strip().replace(",", "."))


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def child_text(el, name: str) -> str:
    for child in el:
        if local_name(child.tag) == name:
            return child.text.strip() if child.text else ""
    return ""


def find_all(root, name: str):
    return [el for el in root.iter() if local_name(el.tag) == name]


def find_text(root, name: str) -> str:
    for el in root.iter():
        if local_name(el.tag) == name:
            return el.text.strip() if el.text else ""
    return ""


def sum_fields(row, fields: list[str]) -> Decimal:
    return sum((dec(child_text(row, field)) for field in fields), Decimal("0.00"))


def has_any_field(row, fields: list[str]) -> bool:
    return any(child_text(row, field) for field in fields)


def period_month(root) -> str:
    data_od = find_text(root, "DataOd")
    if len(data_od) >= 7:
        return data_od[:7]
    return "unknown"


def is_correction(document: str) -> bool:
    if not document:
        return False

    document = document.lower()

    return "kor" in document or "korekta" in document or "correction" in document


def parse_jpk_v7m(path: str):
    tree = ET.parse(path)
    root = tree.getroot()

    sales_net = Decimal("0.00")
    sales_vat = Decimal("0.00")
    purchase_net = Decimal("0.00")
    purchase_vat = Decimal("0.00")

    sales_rows = []
    purchase_rows = []

    for row in find_all(root, "SprzedazWiersz"):
        netto = sum_fields(row, SALES_NET_FIELDS)
        vat = sum_fields(row, SALES_VAT_FIELDS)

        sales_net += netto
        sales_vat += vat

        document = child_text(row, "DowodSprzedazy")

        sales_rows.append(
            {
                "date": child_text(row, "DataSprzedazy") or child_text(row, "DataWystawienia"),
                "contractor": child_text(row, "NazwaKontrahenta"),
                "document": document,
                "nr_ksef": child_text(row, "NrKSeF"),
                "netto": float(netto),
                "vat": float(vat),
                "is_correction": is_correction(document),
            }
        )

    for row in find_all(root, "ZakupWiersz"):
        if has_any_field(row, PURCHASE_NET_FIELDS_V7 + ["K_41"]):
            netto = sum_fields(row, PURCHASE_NET_FIELDS_V7)
            vat = sum_fields(row, PURCHASE_VAT_FIELDS_V7)
        else:
            netto = sum_fields(row, PURCHASE_NET_FIELDS_OLD)
            vat = sum_fields(row, PURCHASE_VAT_FIELDS_OLD)

        purchase_net += netto
        purchase_vat += vat

        document = child_text(row, "DowodZakupu")

        purchase_rows.append(
            {
                "date": child_text(row, "DataZakupu") or child_text(row, "DataWplywu"),
                "contractor": child_text(row, "NazwaDostawcy"),
                "document": document,
                "nr_ksef": child_text(row, "NrKSeF"),
                "netto": float(netto),
                "vat": float(vat),
                "is_correction": is_correction(document),
            }
        )

    return {
        "sales_net": float(sales_net),
        "sales_vat": float(sales_vat),
        "purchase_net": float(purchase_net),
        "purchase_vat": float(purchase_vat),
        "vat_to_pay": float(sales_vat - purchase_vat),
        "period_month": period_month(root),
        "sales_rows": sales_rows,
        "purchase_rows": purchase_rows,
    }
