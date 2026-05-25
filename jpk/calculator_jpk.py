from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from jpk.parser_jpk import parse_jpk_v7m


def month_from_filename(path: Path) -> str:
    name = path.stem
    parts = name.split("_")

    if len(parts) < 3:
        return "unknown"

    month = parts[-2]
    year = parts[-1]

    if not month.isdigit() or not year.isdigit():
        return "unknown"

    month_int = int(month)

    if month_int < 1 or month_int > 12:
        return "unknown"

    return f"{year}-{month.zfill(2)}"


def find_jpk_files(jpk_folder: str):
    base = Path(jpk_folder)

    files = sorted(base.rglob("*.xml"))

    if not files:
        raise RuntimeError(f"Brak plików JPK XML w folderze: {base}")

    return files


def sum_jpk_folder(folder: str):
    yearly = {
        "sales_net": Decimal("0.00"),
        "sales_vat": Decimal("0.00"),
        "purchase_net": Decimal("0.00"),
        "purchase_vat": Decimal("0.00"),
    }

    monthly = defaultdict(
        lambda: {
            "sales_net": Decimal("0.00"),
            "sales_vat": Decimal("0.00"),
            "purchase_net": Decimal("0.00"),
            "purchase_vat": Decimal("0.00"),
            "sales_corrections_net": Decimal("0.00"),
            "sales_corrections_vat": Decimal("0.00"),
            "purchase_corrections_net": Decimal("0.00"),
            "purchase_corrections_vat": Decimal("0.00"),
        }
    )

    files = find_jpk_files(folder)

    print(f"Znaleziono plików JPK: {len(files)}")

    for xml_path in files:
        # print("Czytam JPK:", xml_path.name)

        data = parse_jpk_v7m(str(xml_path))

        for key in yearly:
            yearly[key] += Decimal(str(data[key]))

        month = month_from_filename(xml_path)
        if month == "unknown":
            month = data.get("period_month", "unknown")

        for row in data["sales_rows"]:
            monthly[month]["sales_net"] += Decimal(str(row["netto"]))
            monthly[month]["sales_vat"] += Decimal(str(row["vat"]))
            if row.get("is_correction"):
                monthly[month]["sales_corrections_net"] += Decimal(str(row["netto"]))
                monthly[month]["sales_corrections_vat"] += Decimal(str(row["vat"]))

        for row in data["purchase_rows"]:
            monthly[month]["purchase_net"] += Decimal(str(row["netto"]))
            monthly[month]["purchase_vat"] += Decimal(str(row["vat"]))

            if row.get("is_correction"):
                monthly[month]["purchase_corrections_net"] += Decimal(str(row["netto"]))
                monthly[month]["purchase_corrections_vat"] += Decimal(str(row["vat"]))

    yearly["vat_to_pay"] = yearly["sales_vat"] - yearly["purchase_vat"]

    return yearly, monthly
