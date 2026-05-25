# jpk_model.py

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from ksef.model.deklaracja_model import DeklaracjaVAT7


@dataclass
class SprzedazCtrl:
    LiczbaWierszySprzedazy: int = 0
    PodatekNalezny: Decimal = Decimal("0.00")


@dataclass
class ZakupCtrl:
    LiczbaWierszyZakupow: int = 0
    PodatekNaliczony: Decimal = Decimal("0.00")


@dataclass
class JPKModel:
    # dane nagłówkowe
    data_wytworzenia: str = ""
    data_od: str = ""
    data_do: str = ""
    kod_urzedu: str = ""

    # dane podatnika
    nip: str = ""
    nazwa: str = ""
    data_urodzenia: str = ""
    email: str = ""
    telefon: str = ""

    # adres (opcjonalny)
    wojewodztwo: str = ""
    powiat: str = ""
    gmina: str = ""
    ulica: str = ""
    nr_domu: str = ""
    nr_lokalu: str = ""
    miejscowosc: str = ""
    kod_pocztowy: str = ""
    poczta: str = ""

    deklaracja: DeklaracjaVAT7 = field(default_factory=DeklaracjaVAT7)

    sprzedaz_wiersz: list = field(default_factory=list)
    zakup_wiersz: list = field(default_factory=list)

    sprzedaz_ctrl: Optional[SprzedazCtrl] = None
    zakup_ctrl: Optional[ZakupCtrl] = None


class WierszEwidencji:
    def __init__(
        self,
        typ,  # "sprzedaz" lub "zakup"
        netto,
        vat,
        stawka,
        kontrahent_nip,
        kontrahent_nazwa,
        nr_ksef,
        dokument,
        data_wystawienia,
        data_sprzedazy,
        data_wplywu=None,
        gtu=None,
        procedury=None,
    ):
        self.typ = typ
        self.netto = netto
        self.vat = vat
        self.stawka = stawka

        self.kontrahent_nip = kontrahent_nip
        self.kontrahent_nazwa = kontrahent_nazwa

        self.nr_ksef = nr_ksef
        self.dokument = dokument

        self.data_wystawienia = data_wystawienia
        self.data_sprzedazy = data_sprzedazy
        self.data_wplywu = data_wplywu

        self.gtu = gtu
        self.procedury = procedury or []
