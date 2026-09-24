# Jak wykorzystać Clonerd we własnym środowisku

Ten dokument jest punktem wejścia standardu `wellmanifest/clonerd`.
Odbiorca powinien umieć wybrać komponenty, uruchomić próbę, podłączyć własną
aplikację i sprawdzić rezultat bez dostępu do środowiska autora.
Przykłady dotyczą przypiętego kodu; nie wymagają domen `*.clonerd.com.local`.

## 1. Wybierz zakres

| Potrzeba | Komponenty | Co musisz dostarczyć |
| --- | --- | --- |
| Poznać UI, konto i aktywację na komputerze | `clonerd-com/app` i `llm-account-tool` | Python 3.12 lub 3.13, dwa wolne porty, osobny katalog danych |
| Podłączyć swój program do istniejącego Clonerd | `app/packages/clonerd-sdk` lub klient HTTP | URL operatora, uprawniona sesja lub token urządzenia |
| Uruchomić własny serwer dla zespołu | backend/PWA `app`, reverse proxy; broker opcjonalny | własne nazwy DNS, TLS, trwałe dane, sekrety, procedura kopii |
| Korzystać z własnych modeli | poprzedni wariant + LiteLLM, ewentualnie Ollama | konektor użytkownika, polityka zespołu, model i limity |
| Sterować hostami / noVNC | adapter lokalnego runtime + odpowiednie narzędzia `vnclone`/`premote` | oddzielna instalacja runtime, aktywacja hosta i uprawnienia |

Nie trzeba klonować całej organizacji ani uruchamiać wszystkich domen.
Rejestr hostów w API nie jest instalatorem maszyny wirtualnej. Oddzielny
`clonerd-com/api` nie jest automatycznym zamiennikiem magazynu backendu `app`.
Własna aplikacja może korzystać wyłącznie z API, bez interfejsu PWA.

## 2. Uruchom lokalną próbę

Wymagania: Git, Python 3.12/3.13 z `venv`, możliwość pobrania zależności oraz
dostęp do obu repozytoriów. Jeżeli operator nie udostępnia źródeł, poproś go o
artefakt odpowiadający tym rewizjom; standard nie zastępuje dostępu do kodu.
Przykład dla powłoki POSIX, w nowym katalogu roboczym:

```sh
git clone https://github.com/clonerd-com/app.git clonerd-app
git -C clonerd-app checkout --detach 052aedb137f66ec840478de85d19190dc6890e8d
git clone https://github.com/clonerd-com/llm-account-tool.git clonerd-account-tool
git -C clonerd-account-tool checkout --detach a4f85f4c3f460c46e088e04c2a30fb5e01bba563
cd clonerd-app
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install ../clonerd-account-tool
python -m pip install ./packages/clonerd-sdk
python scripts/run-dev-stack.py --data-dir .reuse-data --cloud-port 8891 --local-port 8790
```

`llm-account-tool` jest osobną zależnością importowaną przez backend; samo
`pip install -r requirements.txt` w tej rewizji jej nie dostarcza.
Na Windows użyj `py -3.12 -m venv .venv` i `.venv\Scripts\Activate.ps1`
w PowerShell; pozostałe wywołania `python` pozostają takie same.

Otwórz adres konta `http://localhost:8891` i urządzenia `http://127.0.0.1:8790`.
Skrypt wypisuje dokładne URL-e i jednorazowy kod zaproszenia. Zarejestruj konto
na pierwszym adresie, rozpocznij aktywację lokalnego urządzenia i zatwierdź kod
w widoku urządzeń konta. Zachowaj różne nazwy hostów: cookies nie rozdzielają
sesji według portu. Ctrl+C kończy oba procesy. Dane pozostają w `.reuse-data`.
Nie kopiuj tego katalogu jako tożsamości kolejnego urządzenia.

To symulator konta centralnego, nie połączenie z publiczną usługą Clonerd.
Tryb lokalny wyłącza zdalne wykonanie i dopuszcza HTTP wyłącznie do tej próby.
Nie wystawiaj go w takiej konfiguracji do sieci zespołu.

## 3. Opisz własne środowisko

Skopiuj [environment.example.json](../profiles/environment.example.json) i
uzupełnij rewizję, wariant, adresy i referencje do sekretów.
Sprawdź opis w katalogu tego standardu:

```sh
python3 standard/conformance.py --environment /sciezka/do/moje-srodowisko.json
```

To przenośny kontrakt dla integratora, **nie plik automatycznie wczytywany przez
Clonerd**. Walidator nie wdraża usług, nie pobiera sekretów ani nie testuje sieci.
Mapuj opis na rzeczywistą konfigurację:

| Pole / potrzeba | Ustawienie backendu lub klienta |
| --- | --- |
| `endpoints.api` | `ClonerdClient(base_url=...)`; adres bez końcówki `/v1` |
| `endpoints.identity` | `CLONERD_CLOUD_URL` urządzenia |
| publiczny adres danej instancji | `CLONERD_PUBLIC_URL` |
| rola procesu | `CLONERD_ROLE=local` albo `cloud` |
| osobny trwały katalog | `CLONERD_DATA_DIR` |
| dozwolone strony przeglądarki | `CLONERD_ORIGINS`, jawna lista adresów |
| cookies i aktywacja | `CLONERD_SECURE_COOKIE=true`, `CLONERD_IDENTITY_REQUIRED=true` poza symulatorem |
| `auth.tokenEnv` | nazwa zmiennej, z której **Twój klient** pobiera token; nie sam token |
| modele i broker | `CLONERD_LITELLM_URL`, konektory i polityki w Konfiguratorze |

Wariant `existing-service` nie wymaga uruchomienia backendu. Operator podaje
adresy i sposób otrzymania tożsamości. Zakres tokenu urządzenia nie zastępuje
sesji użytkownika do administracji kontem. Nie zakładaj SSO pomiędzy hostami.

## 4. Podłącz własny program

Po instalacji SDK, publiczny odczyt niewymagający tokenu:

```python
from clonerd_sdk import ClonerdClient

with ClonerdClient("http://localhost:8891") as client:
    print(client.releases())
```

Dla istniejącej usługi i tokenu urządzenia wydanego przez jej operatora:

```python
import os
from clonerd_sdk import ClonerdClient

with ClonerdClient(os.environ["MY_CLONERD_URL"],
                   token=os.environ["MY_CLONERD_DEVICE_TOKEN"]) as client:
    print(client.models())
```

Token umieść w menedżerze sekretów lub prywatnym środowisku procesu. Nie wpisuj
go do opisu środowiska. Lista modeli może być pusta do czasu konfiguracji
konektora i polityki. Obsłuż `ClonerdError`; 401/403 nie oznacza pustych danych.

HTTP: `contracts/openapi/master.v1.json`; SDK: `packages/clonerd-sdk` z tej
samej rewizji. MCP: `contracts/mcp/tools.json` oraz `/mcp`; zdarzenia:
`contracts/asyncapi/events.v1.yaml`; procesy: `contracts/processes/registry.yaml`.
Wybierz istniejący `operationId` lub URI z kontraktu. NL jest propozycją operacji,
a nie dodatkowym uprawnieniem. Nie integruj przez kopiowanie prywatnych baz.

## 5. Przenieś na własny serwer

Punktem startu są `app/deploy/compose.yml` i `scripts/init-deploy.py` z wybranej
rewizji. Szablon Compose ma nazwy Clonerd zapisane na stałe: przed uruchomieniem
zmień `CLONERD_PUBLIC_URL`, `CLONERD_CLOUD_URL`, `CLONERD_PROXY_URL`,
`CLONERD_ORIGINS` i hosty w `deploy/ingress/Caddyfile` na swoje odpowiedniki.
Nie wystarczy sama zamiana DNS. Sprawdź również hostowe reguły routingu opisane
w `deploy/ingress/README.md`; niestandardowe hosty wymagają testu routingu.

Wygeneruj sekrety poleceniem `python scripts/init-deploy.py --acme-email ...
--litellm-image ...`, podając własny adres i zatwierdzony digest obrazu.
Generator odmawia nadpisania istniejącego `deploy/.env`.
Następnie w `deploy`: `docker compose --env-file .env config --quiet`, a po
przeglądzie konfiguracji `docker compose --env-file .env up -d --build`.
Sprawdź dostępność zależności `llm-account-tool` także w obrazie: instrukcja
instalacji z sekcji 2 nie zmienia automatycznie Containerfile.

Domyślny Compose zawiera broker i Postgres dla LiteLLM. Zmniejszenie zestawu
usług wymaga zmiany zależności Compose, nie tylko pominięcia kontenera.
SQLite Clonerd i Postgres LiteLLM pełnią różne role. Trwałe dane, klucze vault,
tożsamość wystawcy oraz konfiguracja wymagają osobnych kopii i testu odtworzenia.
Dla intranetu skonfiguruj zaufane TLS; nie przenoś flag HTTP z symulatora.
Szczegóły operacyjne: `app/docs/DEPLOYMENT.md` oraz `docs/LAN-TLS-DOMAINS.md`.

## 6. Odbiór integracji

| Próba | Oczekiwany rezultat |
| --- | --- |
| `curl --fail http://localhost:8891/healthz` i port 8790 | oba lokalne procesy odpowiadają; to dopiero test startu |
| Odczyt `client.releases()` | poprawna odpowiedź API, także przy pustym katalogu |
| Rejestracja, aktywacja, logowanie, wylogowanie | własna tożsamość urządzenia; wygasła sesja nie daje dostępu |
| Dwa konta / zespoły | konto B nie widzi prywatnych zasobów konta A |
| Demo i przejście do live | demo nie wykonuje rzeczywistych ani płatnych działań |
| Konfiguracja własnego konektora i jego odebranie | dostęp zgodny z polityką, po odebraniu odmowa |
| Zatrzymanie i ponowny start z tym samym katalogiem | dane zachowane; nowe urządzenie aktywowane oddzielnie |
| Własne DNS, Origin, TLS i routing | właściwa powierzchnia API, bez wyłączania weryfikacji TLS |

Zapisz wersję standardu, rewizję Clonerd, opis środowiska bez sekretów oraz
wyniki tych prób. Sam poprawny JSON nie dowodzi działającej integracji.
Przy zmianie wersji porównaj kontrakty API, uruchom próby ponownie i zachowaj
poprzedni artefakt oraz kopię danych. Nie cofaj bazy w ciemno razem z kodem.

## Typowe problemy

- `ModuleNotFoundError: llm_account_tool`: zainstaluj osobny pakiet w tym samym venv.
- 401/403: sprawdź instancję wystawcy, ważność i rodzaj tożsamości, rolę i tenant.
- `Address already in use`: wybierz inne dwa porty flagami skryptu.
- Problemy sesji: zachowaj `localhost` i `127.0.0.1` w próbie lokalnej.
- UI działa, model nie: sprawdź konektor, publikację modelu i politykę zespołu.
- Host widoczny, sesja noVNC nie działa: samo API nie instaluje runtime hosta.

Reguły zgodności zachowania opisuje [CLONERD.md](CLONERD.md). Zasady publikacji
repozytoriów są dodatkiem dla utrzymujących projekt, nie warunkiem użycia SDK.

## Zakres sprawdzenia tego przewodnika

Dla rewizji wskazanej powyżej uruchomiono skrypt dwóch procesów na Pythonie
3.12 w izolowanym kontenerze: oba `/healthz` oraz `client.releases()` przeszły.
Użyto obrazu z wcześniej zainstalowanymi zależnościami. Nie sprawdzono tutaj
pobierania repozytoriów przez nowego użytkownika, instalacji pip od zera,
rejestracji/aktywacji w przeglądarce ani wdrożenia własnych DNS/TLS.
Te etapy pozostają częścią odbioru konkretnego środowiska.
