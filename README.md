# Fridge Manager

Webbasierte Anwendung zur Verwaltung von Kühlschrank- und Vorratsinhalt.  
Entwickelt im Rahmen des Moduls *Agile Webanwendungen mit Python* an der Hochschule Augsburg.

---

## Motivation

Da ich regelmäßig selbst koche und dabei auf eine ausgewogene Ernährung achte, stehe ich häufig vor einem praktischen Problem: Ich kaufe Lebensmittel ein, vergesse aber, was bereits im Kühlschrank vorhanden ist. Produkte überschreiten unbemerkt ihr Mindesthaltbarkeitsdatum, oder ich kaufe Artikel doppelt, weil ich den Überblick verloren habe.

Fridge Manager entstand aus dieser persönlichen Erfahrung heraus. Die App erfasst nicht nur den Kühlschrankinhalt, sondern auch Trockenwaren und Vorratsartikel, sodass der gesamte Lebensmittelbestand an einem Ort einsehbar ist.

---

## Funktionen

- Benutzerregistrierung und Login
- Zutaten verwalten (hinzufügen, bearbeiten, löschen)
- Ablaufdaten verfolgen mit Farbmarkierung (frisch / läuft bald ab / abgelaufen)
- Wochentliches Einkaufsbudget festlegen und Ausgaben verfolgen
- Einkaufsliste mit automatischen Vorschlägen bei niedrigem Bestand
- Ausgabenverlauf nach Kalenderwochen gruppiert

---

## Tech Stack

| Komponente     | Technologie                    | Version  |
|----------------|-------------------------------|----------|
| Backend        | Python + Flask                | 3.1.3    |
| Datenbank      | SQLite + Flask-SQLAlchemy     | 3.1.1    |
| Migrationen    | Flask-Migrate (Alembic)       | 4.1.0    |
| Authentifizierung | Flask-Login                | 0.6.3    |
| Templates      | Jinja2                        | 3.1.6    |
| Tests          | pytest                        | 9.0.3    |

Alle verwendeten Pakete und deren genaue Versionen sind in `requirements.txt` dokumentiert.

---

## Installation

### Voraussetzungen

- Python 3.13.3
- Git

### Einrichtung

```bash
# Repository klonen
git clone https://github.com/ohlunlacassi/fridge-manager-project.git
cd fridge-manager-project

# Virtuelle Umgebung erstellen und aktivieren
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt
```

---

## Datenbank einrichten

```bash
flask db upgrade
```

---

## Anwendung starten

```bash
flask run
```

Die Anwendung ist anschließend unter `http://127.0.0.1:5000` erreichbar.

---

## Tests ausführen

```bash
pytest
```

---

## Projektstruktur

```
fridge-manager/
├── app/
│   ├── models/             # SQLAlchemy-Modelle
│   ├── static/             # CSS, JS, Bilder
│   │   ├── css/
│   │   └── js/
│   ├── templates/          # Jinja2-Templates
│   ├── __init__.py         # App Factory
│   └── routes.py           # Alle Route-Handler
├── migrations/             # Alembic-Migrationsdateien
├── tests/                  # Pytest-Tests
├── requirements.txt
└── run.py
```

---

## Versionsverwaltung

Das Projekt wurde mit Git versioniert.  
Das vollständige Versionsprotokoll ist Teil der Abgabe und im Repository unter `.git/` enthalten.  
Remote-Repository: `https://github.com/ohlunlacassi/fridge-manager-project.git`
