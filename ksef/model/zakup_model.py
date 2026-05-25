from dataclasses import dataclass


@dataclass
class ZakupWiersz:
    LpZakupu: int
    NrDostawcy: str
    NazwaDostawcy: str
    DowodZakupu: str
    DataZakupu: str
    DataWplywu: str
    NrKSeF: str = ""

    K_42: float = 0.0
    K_43: float = 0.0
    K_44: float = 0.0
    K_45: float = 0.0
    K_46: float = 0.0
    K_47: float = 0.0

    GTU: str | None = None
    IMP: str | None = None
    MPP: str | None = None
    OO: str | None = None
    VAT_RR: str | None = None
    OFF: str | None = None
