# File organizer - program do porządkowania plików
Marta Piraszewska

## Opis
Skrypt `clean_files.py` służy do porządkowania zbiorów plików (dokumentów, zdjęć, nagrań, filmów itp.) znajdujących się w katalogach i ich podkatalogach.  
Ułatwia utrzymanie porządku w dużych kolekcjach plików, w których mogą występować:  
- duplikaty plików (identyczna zawartość),  
- pliki puste,  
- pliki tymczasowe (*.tmp, *~, itp.),  
- pliki o nietypowych atrybutach (np. rwxrwxrwx),  
- pliki o niepoprawnych nazwach (zawierających np. :, ", *, ?, |, \, $),  
- różne wersje plików o tej samej nazwie.

Skrypt może również przenosić lub kopiować brakujące pliki z katalogów pomocniczych (Y1, Y2, ...) do katalogu głównego (X).

## Funkcjonalności
Skrypt potrafi:  
- usuwać pliki puste,  
- usuwać pliki tymczasowe,  
- usuwać duplikaty plików (identyczna zawartość),  
- usuwać pliki o duplikujących się nazwach,  
- zmieniać niepoprawne nazwy plików (zamiana kłopotliwych znaków na bezpieczne),  
- zmieniać niewłaściwe atrybuty,  
- przenosić lub kopiować brakujące pliki z katalogów pomocniczych do katalogu głównego.

## Plik konfiguracyjny
Parametry działania są odczytywane z pliku konfiguracyjnego: `$HOME/.clean_files`.  

Przykładowa zawartość:  
```
[settings]
suggested_mode = 644
bad_chars = :;"*?$#`|\
substitute_char = _
temp_extensions = tmp, bak, ~
```

Jeśli plik nie istnieje, zostaną użyte wartości domyślne.

## Użycie
Podstawowa składnia:  
`python3 clean_files.py [opcje] katalog1 [katalog2 ...]`

Opcje:  
- `--empty` - wyszukuje i usuwa pliki puste  
- `--duplicates` - wyszukuje i usuwa pliki o identycznej zawartości (zostawia najstarszy plik)  
- `--duplicate-names` - wyszukuje i usuwa pliki o tej samej nazwie (zostawia najnowszy plik)  
- `--temp` - wyszukuje i usuwa pliki tymczasowe  
- `--bad-names` - naprawia nazwy plików zawierające niedozwolone znaki  
- `--bad-perms` - naprawia nieprawidłowe atrybuty plików  
- `--move-files` - przenosi lub kopiuje brakujące pliki z katalogów Y... do katalogu X  
- `--all` - wykonuje wszystkie powyższe działania  
- `--interactive` - włącza tryb interaktywny (w tym trybie skrypt pyta użytkownika o potwierdzenie każdej operacji usuwania lub modyfikacji pliku).  

## Przykłady użycia
Usuwanie plików pustych w katalogu X:  
`python3 clean_files.py --empty X`   

Usuwanie duplikatów w trybie interaktywnym w katalogach X i Y (program pyta, które zduplikowane pliki usunąć, a które zostawić):  
`python3 clean_files.py --duplicates --interactive X Y`  

Pełne interaktywne porządkowanie zbioru plików (program pyta, co zrobić z każdym kłopotliwym plikiem):  
`python3 clean_files.py --all --interactive X Y1 Y2`  
