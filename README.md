# Tax App

![Python](https://img.shields.io/badge/python-3.13-blue)
![Quality](https://github.com/dariuszpolzer/tax-app/actions/workflows/quality.yml/badge.svg)
![Tests](https://img.shields.io/badge/tests-pytest-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Proste narzędzie w Pythonie do obliczania podatków dla działalności gospodarczej.
Obecny główny scenariusz to JDG na skali, emerytura oraz opcjonalne wspólne
rozliczenie z małżonkiem.

Aplikacja korzysta z:

- plików JPK VAT
- delegacji służbowych
- faktur z KSeF
- ręcznego profilu podatnika w `config.json`

## Funkcjonalności

- miesięczne zestawienie VAT (należny / naliczony)
- obliczanie zaliczek PIT JDG narastająco
- obliczanie miesięcznej składki zdrowotnej JDG na skali
- roczne rozliczenie PIT na skali z emeryturą
- wspólne rozliczenie z małżonkiem według zasady: podatek od połowy łącznej podstawy razy dwa
- porównanie PIT osobno vs wspólnie
- eksport raportów do plików CSV i XLSX

## Środowisko

Projekt używa `uv`. Źródłem prawdy dla zależności jest `pyproject.toml`, a zablokowane wersje są w `uv.lock`.

```powershell
uv sync --dev
```

## Delegacje

Publicznym formatem wejściowym delegacji jest CSV wskazywany przez
`delegations_csv` w `config.json`:

```csv
number;date_from;date_to;year;city;description;transport;employee;amount_pln;test
DEL/1/2026;2026-03-01;2026-03-25;2026;Brunsbuttel;Delegacja sluzbowa;samochod;Jan Testowy;4915.98;false
```

Minimalne pola potrzebne do obliczeń to `date_to` oraz `amount_pln`.
Koszt delegacji jest przypisywany do miesiąca z `date_to`. Jeśli w configu nie ma
ani `delegations_csv`, ani `trips_xml`, aplikacja przyjmuje brak delegacji.

`trips_xml` jest importerem legacy dla prywatnego formatu `Voyage.xml` używanego
we wcześniejszych makrach VBA. Nie jest to publiczny ani oficjalny format danych.
Do przejścia ze starego XML na CSV służy konwerter:

```powershell
uv run python tools/convert_voyages_to_delegations_csv.py C:/tax-app-data/delegacje/Col_Voyage.xml C:/tax-app-data/delegacje/delegations.csv
```

## Dane wejściowe

Plik `config.json` wskazuje źródła danych:

```json
{
  "taxpayer": {
    "is_pensioner": true,
    "settle_jointly_with_spouse": true
  },
  "business": {
    "enabled": true,
    "taxation_form": "scale",
    "vat_payer": true
  },
  "pension": {
    "enabled": true,
    "annual_income": "42000.00"
  },
  "spouse": {
    "enabled": true,
    "annual_income": "18000.00"
  },
  "delegations_csv": "C:/tax-app-data/delegacje/delegations.csv",
  "trips_xml": "C:/tax-app-data/delegacje/Col_Voyage.xml",
  "jpk_folder": "C:/tax-app-data/jpk",
  "other_costs_csv": "C:/tax-app-data/other_costs.csv"
}
```

`jpk_folder` powinien zawierać miesięczne pliki JPK XML. Aplikacja czyta wszystkie
pliki `*.xml` w tym katalogu i podkatalogach. Miesiąc jest brany z nazwy pliku
`..._MM_RRRR.xml`, a jeśli nazwa nie pasuje, z pola `<DataOd>` w XML.

`other_costs_csv` jest opcjonalny. Jeśli plik nie istnieje, aplikacja przyjmuje
brak dodatkowych kosztów. Format CSV:

```csv
date;type;description;amount_pln
2026-04-10;insurance;Ubezpieczenie;1003.44
2026-04-20;bank;Opłata bankowa;50,50
```

## Profil podatnika

Sekcja `taxpayer` steruje wariantem rozliczenia:

- `is_pensioner` - oznacza podatnika pobierającego emeryturę,
- `settle_jointly_with_spouse` - wybiera wspólne rozliczenie roczne.

Sekcja `business` opisuje działalność. Obecnie obsługiwana jest forma
`"taxation_form": "scale"`. Formy `linear` i `lump_sum` są przygotowane w modelu,
ale nie mają jeszcze zaimplementowanych wyliczeń.

Sekcja `pension` dodaje roczny dochód z emerytury do rozliczenia na skali.
Sekcja `spouse` dodaje roczny dochód małżonka i pozwala porównać rozliczenie
osobno ze wspólnym.

Miesięczny raport PIT dotyczy tylko zaliczek z JDG. Pełne rozliczenie z emeryturą
i małżonkiem jest liczone w raporcie rocznym.

Składka zdrowotna JDG jest liczona osobno od dochodu miesięcznego działalności.
Reguły roczne są w `health_contribution.py`; dla 2026 roku aplikacja używa
stawki 9% i minimalnej składki miesięcznej zapisanej w parametrach roku.

## Uruchomienie

Raport roczny:

```powershell
uv run python main.py --year 2026 --out-dir reports/2026
```

Raport narastająco do wskazanego miesiąca:

```powershell
uv run python main.py --year 2026 --month 4 --out-dir reports/2026-04
```

Wynikiem są:

- `report_monthly.csv`,
- `report_yearly.csv`,
- `report_tax.xlsx`.

`report_monthly.csv` zawiera VAT, miesięczne narastające zaliczki `PIT JDG`
oraz miesięczną składkę zdrowotną JDG.
`report_yearly.csv` i `report_tax.xlsx` zawierają roczne PIT z emeryturą,
dochodem małżonka oraz porównaniem `PIT osobno` i `PIT wspólnie`.

## Kontrola

```powershell
.\check.ps1
```

Przed pushem sprawdź:

- `.\check.ps1` kończy się statusem OK,
- `git status` nie pokazuje danych wygenerowanych lub lokalnych,
- w repo nie ma prywatnego `config.json`, raportów CSV/XLSX ani snapshotów roboczych.

Ręcznie:

```powershell
uv run pytest
uv run ruff check .
uv run black --check .
uv run bandit -r . -c pyproject.toml
```

## CI/CD

Repozytorium zawiera workflow GitHub Actions w `.github/workflows/quality.yml`, który uruchamia testy, ruff, black oraz bandit.

## Licencja

Projekt jest udostępniany na licencji MIT.

Szczegółowe warunki znajdują się w pliku `LICENSE`.
