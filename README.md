# wellmanifest/clonerd

Eksperymentalny standard kompozycji Clonerd: tożsamość, tryby UI, izolacja demo,
kontrakty domenowe, interpretacja poleceń, digital twins oraz bezpieczne dostarczanie.
HOME `wellmanifest`, SHAPE `domain_pack`. Runtime pozostaje w `clonerd-com/*`.

- [Standard i granice odpowiedzialności](standard/CLONERD.md)
- [Profil v1](profiles/clonerd.v1.json) i [zamknięty JSON Schema](schemas/profile.schema.json)
- [Przykłady sześciu stanów UI](profiles/presentation.examples.json)
- [Dokumentacja adopcji](docs/README.md)
- [Rewizje źródeł i inwentaryzacja](standard/sources.lock.json)

| Stan | Akcent |
| --- | --- |
| Przed logowaniem | błękitny `#22d3ee` |
| Demo, także po zalogowaniu | błękitny `#22d3ee` |
| Zalogowany, tryb zwykły | zielony `#21efad` |
| Zalogowany, AUTO | żółty `#facc15` |

Kolor i parametry URL nie nadają uprawnień. Wygaśnięcie rezerwacji nie przekazuje
własności zadania. Profil wymaga obserwowanego kontrolera i niezależnej walidacji.

## Sprawdzenie profilu

Python 3.11+ oraz biblioteka `jsonschema` 4.x (Draft 2020-12):

```sh
python3 standard/conformance.py
python3 -m unittest discover -s tests -v
./project/governance-check.sh
```

Walidator działa offline. Testy obejmują deklarację profilu, sześć kombinacji
sesji/trybu i odrzucanie osłabionych reguł. Nie testują wdrożonej aplikacji,
nie przejmują rezerwacji i nie wystawiają zatwierdzenia merge.

Stan: propozycja lokalna; brak wydania i potwierdzonej adopcji w Clonerd.
