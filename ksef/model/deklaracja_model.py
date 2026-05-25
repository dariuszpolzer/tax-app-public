from dataclasses import dataclass


@dataclass
class DeklaracjaVAT7:
    # Sprzedaż / podatek należny
    P_10: int = 0
    P_11: int = 0
    P_12: int = 0
    P_13: int = 0
    P_14: int = 0
    P_15: int = 0
    P_16: int = 0
    P_17: int = 0
    P_18: int = 0
    P_19: int = 0
    P_20: int = 0
    P_21: int = 0
    P_22: int = 0
    P_23: int = 0
    P_24: int = 0
    P_25: int = 0
    P_26: int = 0
    P_27: int = 0
    P_28: int = 0
    P_29: int = 0
    P_30: int = 0
    P_31: int = 0
    P_32: int = 0
    P_33: int = 0
    P_34: int = 0
    P_35: int = 0
    P_36: int = 0
    P_37: int = 0
    P_38: int = 0
    P_39: int = 0

    # Zakupy / podatek naliczony
    P_40: int = 0
    P_41: int = 0
    P_42: int = 0
    P_43: int = 0
    P_44: int = 0
    P_45: int = 0
    P_46: int = 0
    P_47: int = 0
    P_48: int = 0
    P_49: int = 0
    P_50: int = 0
    P_51: int = 0

    # Dalsze rozliczenie / zwroty / przeniesienia
    P_52: int = 0
    P_53: int = 0
    P_54: str | None = None
    P_55: str | None = None
    P_56: str | None = None
    P_57: str | None = None
    P_58: str | None = None
    P_59: str | None = None
    P_60: int = 0
    P_61: str | None = None
    P_62: int = 0
    P_63: str | None = None
    P_64: str | None = None
    P_65: str | None = None
    P_66: str | None = None
    P_67: str | None = None
    P_68: int = 0
    P_69: int = 0

    # Uzasadnienie korekty
    P_ORDZU: str | None = None
