# Clonerd we własnym środowisku

Ten standard odpowiada na pytanie: **jak wykorzystać Clonerd w swoim projekcie
lub infrastrukturze?** Zawiera wybór komponentów, instrukcję lokalnego startu,
mapowanie konfiguracji, przykłady SDK/API oraz kryteria odbioru integracji.

**Zacznij od [przewodnika ponownego użycia](standard/REUSE.md).**

1. Wybierz lokalną próbę, własny serwer albo klienta istniejącej usługi.
2. Pobierz wskazane wersje komponentów i uruchom minimalny zestaw.
3. Uzupełnij [opis środowiska](profiles/environment.example.json).
4. Podłącz własną aplikację przez SDK lub HTTP.
5. Wykonaj testy odbioru z przewodnika.

Nie potrzebujesz infrastruktury autora, jego domen ani całej organizacji GitHub.
Potrzebujesz dostępu do wybranych komponentów i własnej tożsamości w usłudze.
Opis środowiska jest kontraktem integracji; nie jest instalatorem ani plikiem
konfiguracyjnym automatycznie wczytywanym przez backend.

## Materiały

- [Uruchomienie, konfiguracja, SDK, własny serwer i diagnostyka](standard/REUSE.md)
- [Schema opisu środowiska](schemas/environment.schema.json)
- [Reguły zgodności zachowania](standard/CLONERD.md) i [profil](profiles/clonerd.v1.json)
- [Źródła przypięte do rewizji](standard/sources.lock.json)
- [Dokumentacja standardu](docs/README.md)

HOME `wellmanifest`, SHAPE `domain_pack`; implementacje pozostają w `clonerd-com/*`.
Status: eksperymentalny standard lokalny, bez wydania i potwierdzonej adopcji.

## Sprawdzenie dokumentów maszynowych

Python 3.11+ i biblioteka `jsonschema` 4.x:

```sh
python3 standard/conformance.py --environment profiles/environment.example.json
python3 standard/conformance.py
python3 -m unittest discover -s tests -v
```

Walidacja opisu nie sprawdza dostępności serwera. Wyniki testów rzeczywistej
instancji zapisuje integrator. Zasady pracy nad repozytorium i jego publikacji
są materiałem dla utrzymujących standard; użytkownik SDK ich nie wdraża.
