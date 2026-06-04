# Tax App

![Python](https://img.shields.io/badge/python-3.13-blue)
![Quality](https://github.com/dariuszpolzer/tax-app-public/actions/workflows/quality.yml/badge.svg)
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
- walidacja konfiguracji i danych wejściowych przed generowaniem raportów

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
Koszt delegacji jest przypisywany do miesiąca z `date_to`.

Jeśli w configu ustawione są oba pola, `delegations_csv` ma pierwszeństwo przed
legacy `trips_xml`. Jeśli w configu nie ma ani `delegations_csv`, ani
`trips_xml`, aplikacja przyjmuje brak delegacji.

`trips_xml` jest importerem legacy dla prywatnego formatu `Voyage.xml` używanego
we wcześniejszych makrach VBA. Nie jest to publiczny ani oficjalny format danych.
Do przejścia ze starego XML na CSV służy konwerter:

```powershell
uv run python tools/convert_voyages_to_delegations_csv.py C:/tax-app-data/delegacje/Col_Voyage.xml C:/tax-app-data/delegacje/delegations.csv
```

### Synchronizacja `Col_Voyage.xml` przez FTP

Do wymiany pliku delegacji między komputerami użyj prywatnego katalogu FTP poza
publicznym katalogiem WWW, np.:

```text
/tax_exchange/delegacje/Col_Voyage.xml
```

Skopiuj `ftp-sync.example.json` do `ftp-sync.json` i wpisz lokalne dane FTP.
`ftp-sync.json` jest ignorowany przez Git i nie powinien trafiać do repozytorium.

Pobranie aktualnego pliku z FTP:

```powershell
.\tools\download_delegations.ps1
```

Wysłanie lokalnego pliku na FTP:

```powershell
.\tools\upload_delegations.ps1
```

`config.json` powinien wskazywać tę samą lokalną kopię, która jest synchronizowana
z FTP:

```json
"trips_xml": "C:/tax-app-data/delegacje/Col_Voyage.xml"
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
  "health_contribution": {
    "income_basis": "previous_month"
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

## Walidacja

Przed generowaniem raportu można sprawdzić konfigurację i dane wejściowe:

```powershell
uv run python main.py validate --year 2026 --config config.json
```

Walidacja sprawdza:

- istnienie pliku `config.json` oraz ścieżek do danych,
- poprawność profilu podatnika,
- obecność i format plików JPK XML,
- wymagane kolumny, daty i kwoty w `delegations_csv`,
- wymagane kolumny, daty i kwoty w `other_costs_csv`,
- ostrzeżenia dla danych z innego roku niż walidowany raport.

Opcjonalnie można pominąć sprawdzanie folderu JPK:

```powershell
uv run python main.py validate --year 2026 --config config.json --skip-jpk
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
Domyślnie aplikacja używa mechanizmu ZUS, czyli składka za dany miesiąc jest
liczona od dochodu z miesiąca poprzedniego:

```json
"health_contribution": {
  "income_basis": "previous_month"
}
```

Dostępny jest też wariant pomocniczy liczony od dochodu tego samego miesiąca:

```json
"health_contribution": {
  "income_basis": "current_month"
}
```

Reguły roczne są w `health_contribution.py`; dla 2026 roku aplikacja używa
stawki 9% i minimalnej składki miesięcznej zapisanej w parametrach roku.

## Uruchomienie

Walidacja konfiguracji i danych wejściowych:

```powershell
uv run python main.py validate --year 2026 --config config.json
```

Raport roczny:

```powershell
uv run python main.py report --year 2026 --out-dir reports/2026
```

Raport narastająco do wskazanego miesiąca:

```powershell
uv run python main.py report --year 2026 --month 4 --out-dir reports/2026-04
```

Stary wariant wywołania bez podkomendy nadal działa:

```powershell
uv run python main.py --year 2026 --out-dir reports/2026
```

Kontrola samych delegacji:

```powershell
uv run python main.py delegations check --year 2026
```

Wynikiem są:

- `report_monthly.csv`,
- `report_yearly.csv`,
- `report_tax.xlsx`.

`report_monthly.csv` zawiera VAT, miesięczne narastające zaliczki `PIT JDG`
oraz miesięczną składkę zdrowotną JDG.
`report_yearly.csv` i `report_tax.xlsx` zawierają roczne PIT z emeryturą,
dochodem małżonka oraz porównaniem `PIT osobno` i `PIT wspólnie`.
Raport XLSX zawiera też arkusze z danymi wejściowymi oraz ostrzeżeniami
walidacji.

Arkusze w `report_tax.xlsx`:

- `Dashboard`,
- `VAT miesięcznie`,
- `PIT JDG`,
- `Zdrowotna JDG`,
- `Delegacje`,
- `Inne koszty`,
- `Roczny`,
- `Dane wejściowe`,
- `Ostrzeżenia`.

## Orchestratory

Lokalne launchery workflow nie są częścią publicznego repo `tax-app-public`.
Są utrzymywane osobno w prywatnym repozytorium `Orchestrators`.

Typowy zewnętrzny workflow uruchamia:

1. synchronizację KSeF,
2. generowanie JPK,
3. pobranie delegacji,
4. `tax-app-public validate`,
5. `tax-app-public report`.

### Harmonogram zadań Windows

Do prostego uruchamiania cyklicznego można zarejestrować zadania Windows dla
prywatnych launcherów z repo `Orchestrators`:

```powershell
.\tools\register_windows_tasks.ps1 `
  -MonitorMFPath "C:\Orchestrators\MonitorMF.ps1" `
  -OfflineE2EPath "C:\Orchestrators\OfflineE2E.ps1" `
  -VerifyPreviousPath "C:\Orchestrators\VerifyPrevious.ps1" `
  -MonitorMFSchedule Daily `
  -MonitorMFTime "06:00"
```

`MonitorMF` jest rejestrowany jako zadanie dzienne albo tygodniowe:

```powershell
.\tools\register_windows_tasks.ps1 `
  -MonitorMFPath "C:\Orchestrators\MonitorMF.ps1" `
  -OfflineE2EPath "C:\Orchestrators\OfflineE2E.ps1" `
  -VerifyPreviousPath "C:\Orchestrators\VerifyPrevious.ps1" `
  -MonitorMFSchedule Weekly `
  -MonitorMFWeeklyDay Monday `
  -MonitorMFTime "06:00"
```

`OfflineE2E` i `VerifyPrevious` są rejestrowane jako zadania uruchamiane ręcznie
z Harmonogramu zadań albo komendą:

```powershell
schtasks /Run /TN "\TaxApp\OfflineE2E"
schtasks /Run /TN "\TaxApp\VerifyPrevious"
```

Praktyczny rytm:

- `MonitorMF` raz dziennie albo raz w tygodniu,
- `OfflineE2E` po każdej większej zmianie,
- `VerifyPrevious` po zamknięciu miesiąca.

### Alert po zmianie MF

Jeśli prywatny `MonitorMF` wykryje zmianę w źródłach Ministerstwa Finansów,
może zapisać ostatni status przez wspólny adapter:

```powershell
.\tools\write_mf_monitor_status.ps1 `
  -Status Changed `
  -Message "Wykryto zmianę komunikatu MF" `
  -PreviousValue "2026-05-01" `
  -CurrentValue "2026-06-04" `
  -SourceUrl "https://www.podatki.gov.pl/" `
  -OutDir "."
```

Skrypt zapisuje:

- `mf_monitor_latest_status.txt` - prosty status do szybkiego odczytu,
- `mf_monitor_latest_status.json` - status strukturalny dla automatyzacji,
- `mf_monitor_alert.html` - gotowy fragment do wklejenia lub osadzenia w raporcie HTML.

Dla braku zmiany:

```powershell
.\tools\write_mf_monitor_status.ps1 `
  -Status NoChange `
  -Message "Brak zmian MF" `
  -CurrentValue "2026-06-04"
```

Opcjonalne wysłanie maila przy `Changed` albo `Error`:

```powershell
.\tools\write_mf_monitor_status.ps1 `
  -Status Changed `
  -Message "Wykryto zmianę komunikatu MF" `
  -CurrentValue "2026-06-04" `
  -SendMail `
  -SmtpServer "smtp.example.com" `
  -SmtpPort 587 `
  -MailFrom "tax-app@example.com" `
  -MailTo "adres@example.com" `
  -UseSsl
```

Mail nie jest wysyłany dla `NoChange`.

### Jedno polecenie kontrolne

Po zarejestrowaniu zadań Windows można uruchomić pełny lokalny audyt jednym
poleceniem:

```powershell
.\wife-launcher.ps1 -Action AuditAll
```

`AuditAll` wykonuje kolejno:

- `Doctor`, czyli lokalne `.\check.ps1`,
- `MonitorMF` z Harmonogramu zadań,
- `OfflineE2E` z Harmonogramu zadań,
- ostatni `VerifyPrevious` z Harmonogramu zadań,
- `security-check`, czyli `tools/security_check.py --redact`.

Pojedyncze akcje można uruchomić tym samym launcherem:

```powershell
.\wife-launcher.ps1 -Action Doctor
.\wife-launcher.ps1 -Action MonitorMF
.\wife-launcher.ps1 -Action OfflineE2E
.\wife-launcher.ps1 -Action VerifyPrevious
.\wife-launcher.ps1 -Action SecurityCheck
```

Domyślna ścieżka zadań to `\TaxApp\`. Jeśli zadania są zarejestrowane gdzie
indziej:

```powershell
.\wife-launcher.ps1 -Action AuditAll -TaskPath "\InnaSciezka\"
```

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
