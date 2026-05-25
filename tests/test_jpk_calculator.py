from pathlib import Path

from jpk.calculator_jpk import month_from_filename, sum_jpk_folder


def test_month_from_filename():
    path = Path("JPK_Example_User_03_2026.xml")

    assert month_from_filename(path) == "2026-03"


def test_month_from_filename_invalid_short_name():
    path = Path("JPK.xml")

    assert month_from_filename(path) == "unknown"


def test_month_from_filename_invalid_month():
    path = Path("JPK_Test_13_2026.xml")

    assert month_from_filename(path) == "unknown"


def test_month_from_filename_invalid_text():
    path = Path("JPK_Test_marzec_2026.xml")

    assert month_from_filename(path) == "unknown"


def test_sum_jpk_folder_uses_period_month_when_filename_has_no_month(tmp_path):
    xml = tmp_path / "old-jpk.xml"
    xml.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<JPK>
  <Naglowek>
    <DataOd>2019-11-01</DataOd>
    <DataDo>2019-11-30</DataDo>
  </Naglowek>
  <SprzedazWiersz>
    <DataSprzedazy>2019-11-05</DataSprzedazy>
    <DowodSprzedazy>FV/11/2019</DowodSprzedazy>
    <K_19>1000.00</K_19>
    <K_20>230.00</K_20>
  </SprzedazWiersz>
</JPK>
""",
        encoding="utf-8",
    )

    _, monthly = sum_jpk_folder(str(tmp_path))

    assert monthly["2019-11"]["sales_net"] == 1000
    assert monthly["2019-11"]["sales_vat"] == 230
