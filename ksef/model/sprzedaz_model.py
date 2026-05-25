from dataclasses import dataclass


@dataclass
class SprzedazWiersz:
    LpSprzedazy: int
    NrKontrahenta: str
    NazwaKontrahenta: str
    DowodSprzedazy: str
    DataWystawienia: str
    DataSprzedazy: str
    NrKSeF: str = ""

    # VAT
    K_19: float = 0.0
    K_20: float = 0.0
    K_21: float = 0.0
    K_22: float = 0.0
    K_23: float = 0.0
    K_24: float = 0.0
    K_27: float = 0.0
    K_28: float = 0.0

    # Procedury
    WDT: str | None = None
    Eksport: str | None = None
    OO: str | None = None
    MPP: str | None = None
    Marza: str | None = None
    SW: str | None = None
    EE: str | None = None
    TP: str | None = None
    OFF: str | None = None

    # GTU
    GTU: str | None = None
