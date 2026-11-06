# ProfitEMS dla Home Assistant

Oficjalna integracja [ProfitEMS](https://profitems.pl). Dane instalacji z bramką EMS Connect trafiają do Home Assistant jako czujniki, których można użyć na wykresach i w automatyzacjach.

Integracja służy wyłącznie do odczytu. Nie steruje falownikiem ani magazynem energii: o ich pracy decyduje system ProfitEMS.

## Wymagania

- Home Assistant 2026.3 lub nowszy
- Instalacja z bramką EMS Connect i konto w aplikacji ProfitEMS

## Instalacja

1. W HACS otwórz menu **Custom repositories** i dodaj `https://github.com/ProfitEMS/home-assistant` jako **Integration**.
2. Zainstaluj ProfitEMS i uruchom ponownie Home Assistant.
3. W aplikacji ProfitEMS wybierz **Konto → Moja instalacja → Dostęp dla Home Assistant → Utwórz klucz**. Klucz jest widoczny tylko raz.
4. W Home Assistant wybierz **Ustawienia → Urządzenia i usługi → Dodaj integrację → ProfitEMS** i wklej klucz.

Klucz przestaje działać po wyłączeniu w aplikacji, po zmianie lub resecie hasła do konta oraz po przypisaniu instalacji do innego właściciela. Home Assistant poprosi wtedy o nowy klucz.

## Czujniki

| Czujnik | Znaczenie |
|---|---|
| Poziom baterii | Naładowanie magazynu energii, % |
| Produkcja z paneli | Moc, W |
| Zużycie domu | Moc, W |
| Moc sieci | Wartość dodatnia oznacza pobór z sieci, ujemna oddawanie do sieci, W |
| Moc magazynu | Wartość ujemna oznacza ładowanie, dodatnia rozładowanie, W |
| Nadwyżka z paneli | O ile produkcja przewyższa zużycie domu, W |
| Tryb pracy | Bieżący tryb systemu; plan na resztę doby w atrybucie `plan`, na całą dobę w `plan_today`, na jutro w `plan_tomorrow` |
| Cena RCE | Cena bieżącej godziny, zł/kWh netto; ceny godzinowe w atrybutach `today` i `tomorrow`, z początkiem i końcem każdej godziny w `prices_today` i `prices_tomorrow` |
| Produkcja z paneli dziś, Zużycie domu dziś, Pobór z sieci dziś, Oddawanie do sieci dziś, Ładowanie magazynu dziś, Rozładowanie magazynu dziś | Liczniki energii z falownika od jego północy, kWh; do panelu Energia |
| Wartość energii dziś | Wartość energii od północy, liczona tak samo jak „Zysk dzisiaj” w aplikacji, zł; podział w atrybutach |
| Najtańsza godzina dziś | Godzina od 0 do 23 |
| Dostępna nadwyżka z paneli | Tak lub nie |
| Magazyn pełny | Tak lub nie |
| Trwa najtańsza godzina | Tak lub nie |
| Praca wyspowa | Tak, gdy instalacja pracuje bez zasilania z sieci |
| Połączenie, Ostatni odczyt, Sterowanie aktywne | Dane diagnostyczne |

Które liczniki energii podaje falownik:

| Marka | Liczniki |
|---|---|
| Deye, Sofar, MUST | wszystkie sześć |
| FoxESS | produkcja, zużycie domu, pobór i oddawanie; bez ładowania i rozładowania magazynu |
| SolaX | tylko produkcja |

Liczniki, których falownik nie podaje, są dodawane jako wyłączone; można je włączyć w ustawieniach urządzenia. Falownik zeruje liczniki według własnego zegara, więc moment zerowania może różnić się od północy. „Wartość energii dziś” system przelicza co godzinę. Aby dodać je do panelu Energia, wybierz **Ustawienia → Pulpity → Energia** i wskaż odpowiednie czujniki.

Dane o pracy instalacji są aktualizowane co 5 minut. Podczas okresu nauki system tylko obserwuje instalację: tryb to „Obserwacja”, a plan jest pusty.

## Przykład: grzałka przy pełnym magazynie

Numer bramki w nazwach czujników zastąp własnym.

```yaml
automation:
  - alias: "Grzałka przy pełnym magazynie i nadwyżce"
    trigger:
      - platform: state
        entity_id: binary_sensor.profitems_pe_26_000_magazyn_pelny
        to: "on"
        for: "00:10:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.profitems_pe_26_000_nadwyzka_z_paneli
        above: 2000
    action:
      - action: switch.turn_on
        target:
          entity_id: switch.grzalka
```

Moc urządzenia dobierz do swojej instalacji i przepisów dotyczących jej pracy. Za działanie automatyzacji i podłączonych urządzeń odpowiada użytkownik.

## Zgłoszenia

Błędy i propozycje zgłaszaj w zakładce [Issues](https://github.com/ProfitEMS/home-assistant/issues). W sprawach instalacji i konta napisz na kontakt@profitems.pl.

## In English

Official read-only ProfitEMS integration for Home Assistant. Create an access key in the ProfitEMS app and add the integration in Home Assistant. Polish and English translations are included.

## Licencja

MIT, zobacz [LICENSE](LICENSE). Nazwa i logo ProfitEMS należą do PROFITEMS Sp. z o.o. i licencja ich nie obejmuje.
