from dataclasses import dataclass


@dataclass
class Podatnik:
    # dane identyfikacyjne
    nip: str
    imie: str
    nazwisko: str
    data_urodzenia: str
    email: str
    telefon: str

    # dane adresowe
    wojewodztwo: str = ""
    powiat: str = ""
    gmina: str = ""
    ulica: str = ""
    nr_domu: str = ""
    nr_lokalu: str = ""
    miejscowosc: str = ""
    kod_pocztowy: str = ""
    poczta: str = ""

    # dane nagłówkowe JPK
    data_wytworzenia: str = ""
    data_od: str = ""
    data_do: str = ""
    kod_urzedu: str = ""
