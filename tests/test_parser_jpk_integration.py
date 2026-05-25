from decimal import Decimal
from pathlib import Path

from jpk.parser_jpk import parse_jpk_v7m


def test_parse_jpk_example():
    xml = Path("tests/data/example_jpk.xml")

    data = parse_jpk_v7m(xml)

    assert data["sales_net"] == Decimal("1000.00")
    assert data["sales_vat"] == Decimal("230.00")
    assert data["purchase_net"] == Decimal("200.00")
    assert data["purchase_vat"] == Decimal("46.00")


def test_parse_jpk_sums_multiple_vat_register_fields(tmp_path):
    xml = tmp_path / "JPK.xml"
    xml.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<JPK>
  <Naglowek>
    <DataOd>2025-04-01</DataOd>
    <DataDo>2025-04-30</DataDo>
  </Naglowek>
  <Ewidencja>
    <SprzedazWiersz>
      <DataSprzedazy>2025-04-10</DataSprzedazy>
      <DowodSprzedazy>FV/1/2025</DowodSprzedazy>
      <K_17>100.00</K_17>
      <K_18>8.00</K_18>
      <K_19>200.00</K_19>
      <K_20>46.00</K_20>
    </SprzedazWiersz>
    <ZakupWiersz>
      <DataZakupu>2025-04-11</DataZakupu>
      <DowodZakupu>FZ/1/2025</DowodZakupu>
      <K_40>300.00</K_40>
      <K_41>69.00</K_41>
      <K_42>400.00</K_42>
      <K_43>92.00</K_43>
    </ZakupWiersz>
  </Ewidencja>
</JPK>
""",
        encoding="utf-8",
    )

    data = parse_jpk_v7m(xml)

    assert data["sales_net"] == Decimal("300.00")
    assert data["sales_vat"] == Decimal("54.00")
    assert data["purchase_net"] == Decimal("700.00")
    assert data["purchase_vat"] == Decimal("161.00")
    assert data["period_month"] == "2025-04"


def test_parse_old_jpk_vat_purchase_fields(tmp_path):
    xml = tmp_path / "old-jpk.xml"
    xml.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<JPK>
  <Naglowek>
    <DataOd>2019-11-01</DataOd>
    <DataDo>2019-11-30</DataDo>
  </Naglowek>
  <ZakupWiersz>
    <DataZakupu>2019-11-12</DataZakupu>
    <DowodZakupu>FZ/11/2019</DowodZakupu>
    <K_43>1000.00</K_43>
    <K_44>230.00</K_44>
    <K_45>500.00</K_45>
    <K_46>115.00</K_46>
  </ZakupWiersz>
</JPK>
""",
        encoding="utf-8",
    )

    data = parse_jpk_v7m(xml)

    assert data["purchase_net"] == Decimal("1500.00")
    assert data["purchase_vat"] == Decimal("345.00")
    assert data["period_month"] == "2019-11"
