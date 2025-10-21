# Rechnungsgenerator GoBD-konform für Deutschland 🇩🇪

Ein vollständiges System zur Erstellung GoBD-konformer elektronischer Rechnungen nach deutschen Standards.

## ✨ Hauptmerkmale

### 📋 Rechtliche Konformität
- ✅ **§14 UStG**: Alle Pflichtangaben für Rechnungen
- ✅ **§147 AO**: 10-jährige Aufbewahrungspflicht
- ✅ **GoBD**: Grundsätze ordnungsmäßiger Buchführung
- ✅ **DSGVO**: Datenschutz-konform

### 🔐 Technische Sicherheit
- ✅ **PDF/A-3**: Langzeitarchivierungsformat (ISO 19005-3)
- ✅ **ZUGFeRD 2.2**: Eingebettetes XML nach EN-16931
- ✅ **RFC3161 TSA**: Qualifizierte Zeitstempel
- ✅ **PAdES**: Fortgeschrittene elektronische Signatur
- ✅ **SHA-256**: Kryptographische Hash-Funktion

### 💼 Geschäftsfunktionen
- ✅ **Fortlaufende Nummerierung**: Lückenlose Rechnungsnummern
- ✅ **Mehrere Steuersätze**: 19%, 7%, 0% (Kleinunternehmer)
- ✅ **Multi-Währung**: EUR, USD, CHF
- ✅ **Versionierung**: Alle Änderungen nachvollziehbar
- ✅ **Audit-Logs**: Vollständige Protokollierung
- ✅ **Export-Funktionen**: PDF, XML, JSON, CSV

## 🏗️ Systemarchitektur

### Backend (Python + FastAPI)
```
backend/
├── app/
│   ├── main.py              # FastAPI Anwendung
│   ├── models/              # SQLAlchemy Datenmodelle
│   ├── schemas/             # Pydantic Validierung
│   ├── api/                 # REST API Endpoints
│   ├── services/
│   │   ├── invoice_service.py       # Hauptlogik
│   │   ├── zugferd_generator.py     # ZUGFeRD XML
│   │   ├── pdf_generator.py         # PDF/A-3
│   │   ├── signature_service.py     # TSA Signatur
│   │   └── storage_service.py       # Dateiverwaltung
│   └── core/
│       ├── config.py        # Konfiguration
│       ├── database.py      # Datenbank-Setup
│       └── security.py      # Authentifizierung
└── requirements.txt
```

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── components/          # UI Komponenten
│   ├── pages/               # Seiten
│   ├── services/            # API Client
│   ├── contexts/            # React Context
│   └── types/               # TypeScript Typen
└── package.json
```

### Datenbank
- **Entwicklung**: SQLite
- **Produktion**: PostgreSQL empfohlen
- **Migrationen**: Alembic
- **ORM**: SQLAlchemy 2.0

## 🚀 Schnellstart

### Voraussetzungen
- Python 3.12+
- Node.js 18+
- `psutil` Python-Paket (für run.py): `pip3 install psutil`
- (Optional) Docker + Docker Compose

### ⚡ Einfachster Start - Mit VS Code

Die einfachste Methode ist, die Anwendung direkt aus VS Code zu starten:

#### Option 1: Play Button (F5)
1. Öffne das Projekt in VS Code
2. Drücke **F5** oder klicke auf das Play-Symbol
3. Wähle **"🚀 Iniciar Aplicación Completa"**
4. Die Anwendung startet automatisch Backend und Frontend!

#### Option 2: Kommandozeile
```bash
# Anwendung starten
python3 run.py start

# Status prüfen
python3 run.py status

# Anwendung stoppen
python3 run.py stop

# Anwendung neustarten
python3 run.py restart
```

Das war's! Die Anwendung läuft auf:
- 🌐 **Frontend**: http://localhost:5173
- 🔧 **Backend API**: http://localhost:8000
- 📚 **API Dokumentation**: http://localhost:8000/docs

**Login:**
- Username: `admin`
- Password: `admin`

### Installation - Manuell (falls benötigt)

#### 1. Backend starten
```bash
cd backend

# Python Virtual Environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Umgebungsvariablen
cp .env.example .env
# .env bearbeiten nach Bedarf

# Datenbank initialisieren
python scripts/create_tables.py

# Admin-User erstellen (admin/admin)
python scripts/seed_admin.py

# Server starten
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend läuft auf: **http://localhost:8000**  
API Docs: **http://localhost:8000/docs**

#### 2. Frontend starten
```bash
cd frontend

# Dependencies installieren
npm install

# Dev-Server starten
npm run dev
```

Frontend läuft auf: **http://localhost:5173**

### Installation - Docker

```bash
# Alle Services starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f

# Stoppen
docker-compose down
```

## 📖 Verwendung

### 1. Anmelden
- URL: http://localhost:5173
- Username: `admin`
- Password: `admin`
- ⚠️ **In Produktion sofort ändern!**

### 2. Rechnung erstellen

#### Web-Interface:
1. "Neue Rechnung" klicken
2. Verkäufer-Daten eingeben (oder Template verwenden)
3. Käufer-Daten eingeben
4. Rechnungspositionen hinzufügen
5. Zahlungsbedingungen festlegen
6. "Erstellen" → System generiert automatisch:
   - PDF/A-3 mit eingebettetem ZUGFeRD XML
   - RFC3161 Zeitstempel
   - Fortlaufende Rechnungsnummer

#### API (cURL):
```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.access_token')

# Rechnung erstellen
curl -X POST http://localhost:8000/api/invoices \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "seller": {
      "name": "Musterfirma GmbH",
      "street": "Musterstraße 123",
      "zip": "10115",
      "city": "Berlin",
      "country": "DE",
      "tax_id": "DE123456789",
      "email": "info@musterfirma.de"
    },
    "buyer": {
      "name": "Kundenfirma AG",
      "street": "Kundenweg 456",
      "zip": "80331",
      "city": "München",
      "country": "DE",
      "tax_id": "DE987654321"
    },
    "issue_date": "2025-10-22",
    "delivery_date_start": "2025-10-15",
    "currency": "EUR",
    "line_items": [
      {
        "description": "Softwareentwicklung",
        "quantity": 40,
        "unit": "H",
        "unit_price": 95.00,
        "tax_rate": 19.0
      }
    ],
    "payment_terms": "Zahlbar innerhalb 14 Tagen",
    "notes": "Vielen Dank!"
  }'
```

### 3. Rechnung herunterladen

```bash
# PDF herunterladen
curl -X GET http://localhost:8000/api/invoices/{id}/download \
  -H "Authorization: Bearer $TOKEN" \
  -o rechnung.pdf

# Komplettes Archiv (PDF + XML + TSA + Metadaten)
curl -X GET http://localhost:8000/api/invoices/{id}/archive \
  -H "Authorization: Bearer $TOKEN" \
  -o rechnung_archiv.zip
```

### 4. Rechnungen auflisten

```bash
# Alle Rechnungen
curl -X GET http://localhost:8000/api/invoices \
  -H "Authorization: Bearer $TOKEN"

# Filtern nach Status
curl -X GET "http://localhost:8000/api/invoices?status=issued" \
  -H "Authorization: Bearer $TOKEN"

# Suche nach Kunde
curl -X GET "http://localhost:8000/api/invoices?buyer_name=Kundenfirma" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔧 Konfiguration

### Backend (.env)

```bash
# Anwendung
APP_NAME="Rechnungsgenerator GoBD"
APP_VERSION="0.1.0"
ENVIRONMENT=development

# Datenbank
DATABASE_URL=sqlite:///./rechnungen.db
# Produktion: postgresql://user:pass@host:5432/dbname

# Security
SECRET_KEY=your-secret-key-here-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS
CORS_ORIGINS=http://localhost:5173

# Rechnungsnummern
INVOICE_NUMBER_PREFIX=RE2025
INVOICE_NUMBER_START=1

# S3 Storage (optional)
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=invoices
S3_USE_SSL=False

# RFC3161 TSA
TSA_URL=https://freetsa.org/tsr
TSA_USERNAME=
TSA_PASSWORD=
TSA_HASH_ALGORITHM=SHA256
```

### Produktions-TSA Anbieter

**Kostenlos (für Tests):**
- https://freetsa.org/tsr
- http://timestamp.digicert.com

**Kommerziell (empfohlen):**
- **DigiCert**: https://timestamp.digicert.com
- **GlobalSign**: http://timestamp.globalsign.com/tsa/r6advanced1
- **D-Trust**: https://zeitstempel.d-trust.net/TSS (deutscher Anbieter)
- **Bundesdruckerei**: https://tsa.governikus.de (qualifiziert)

## 📊 Datenbank-Schema

### Tabellen

#### invoices
- Haupttabelle für Rechnungen
- Alle Pflichtfelder nach §14 UStG
- `is_immutable=True` → Unveränderbar nach Erstellung

#### invoice_line_items
- Rechnungspositionen
- Verknüpft mit `invoices`

#### users
- Benutzer mit Rollen
- Passwort: bcrypt-Hash

#### audit_logs
- Vollständige Protokollierung
- Jede Aktion mit Timestamp, User, IP

#### invoice_number_sequence
- Fortlaufende Nummerierung
- Row-Level-Lock für Konsistenz

### ER-Diagramm

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │
│ username        │
│ email           │
│ hashed_password │
│ is_active       │
│ is_superuser    │
└────────┬────────┘
         │
         │ created_by
         │
┌────────▼────────────────────┐        ┌──────────────────────┐
│       invoices              │◄───────┤ invoice_line_items   │
├─────────────────────────────┤        ├──────────────────────┤
│ id (PK)                     │        │ id (PK)              │
│ invoice_number (UNIQUE)     │        │ invoice_id (FK)      │
│ issue_date                  │        │ position             │
│ seller_* (§14 UStG)        │        │ description          │
│ buyer_* (§14 UStG)         │        │ quantity             │
│ net_total                   │        │ unit_price           │
│ tax_total                   │        │ tax_rate             │
│ gross_total                 │        │ line_gross           │
│ pdfa3_path                  │        └──────────────────────┘
│ zugferd_xml_path            │
│ pdf_hash                    │
│ tsa_token (JSON)            │
│ status                      │
│ is_immutable                │
│ created_by (FK)             │
│ created_at                  │
└─────────────────────────────┘
```

## 🧪 Testing

### Unit Tests
```bash
cd backend
pytest tests/unit -v
```

### Integration Tests
```bash
pytest tests/integration -v
```

### E2E Tests
```bash
cd frontend
npm run test:e2e
```

### Coverage
```bash
pytest --cov=app --cov-report=html
```

## 📦 Deployment

### Produktions-Checklist

#### Sicherheit
- [ ] `SECRET_KEY` mit kryptografisch sicherem Wert ersetzen
- [ ] Admin-Passwort ändern
- [ ] HTTPS aktivieren (nginx + Let's Encrypt)
- [ ] Firewall konfigurieren
- [ ] Rate-Limiting aktivieren
- [ ] CORS auf Produktions-Domain einschränken

#### Datenbank
- [ ] Auf PostgreSQL migrieren
- [ ] Automatische Backups einrichten
- [ ] Connection Pooling konfigurieren
- [ ] Read Replicas für Skalierung (optional)

#### Storage
- [ ] S3/MinIO produktiv konfigurieren
- [ ] Versioning aktivieren
- [ ] Object Lock (WORM) aktivieren
- [ ] Lifecycle-Policies (10 Jahre Aufbewahrung)
- [ ] Georedundanz aktivieren

#### Monitoring
- [ ] Prometheus Metriken exponieren
- [ ] Grafana Dashboards einrichten
- [ ] Alerting konfigurieren
- [ ] Log-Aggregation (ELK/Loki)

#### Compliance
- [ ] Verfahrensdokumentation erstellen
- [ ] Datenschutz-Folgenabschätzung
- [ ] Backup-Restore testen
- [ ] Betriebsprüfung vorbereiten

### Docker Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: rechnungen
      POSTGRES_USER: invoiceuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://invoiceuser:${DB_PASSWORD}@postgres:5432/rechnungen
      SECRET_KEY: ${SECRET_KEY}
      TSA_URL: https://zeitstempel.d-trust.net/TSS
    depends_on:
      - postgres
      - minio
    restart: always

  frontend:
    build: ./frontend
    environment:
      VITE_API_URL: https://api.ihre-domain.de
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: always

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    restart: always

volumes:
  postgres_data:
  minio_data:
```

## 🔍 Troubleshooting

### PDF-Generierung schlägt fehl
```bash
# Reportlab-Schriften installieren
pip install reportlab[rlPyCairo]

# Systemschriften verfügbar machen
apt-get install fonts-liberation
```

### TSA-Zeitstempel-Fehler
```python
# Fallback auf Mock-Zeitstempel (nur Entwicklung!)
TSA_URL=mock

# Oder anderer TSA-Provider
TSA_URL=http://timestamp.digicert.com
```

### Datenbankfehler
```bash
# Tabellen neu erstellen
python scripts/create_tables.py

# Alembic Migrationen
alembic upgrade head
```

### CORS-Fehler
```bash
# .env anpassen
CORS_ORIGINS=http://localhost:5173,https://ihre-domain.de
```

## 📚 Dokumentation

- [QUICKSTART.md](docs/QUICKSTART.md) - Schnelleinstieg
- [RECHNUNGSERSTELLUNG-GOBD.md](docs/RECHNUNGSERSTELLUNG-GOBD.md) - Detaillierte Erklärung GoBD-Konformität
- [TSA-KONFIGURATION.md](docs/TSA-KONFIGURATION.md) - Zeitstempel-Konfiguration
- [API.md](docs/API.md) - REST API Referenz
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Produktions-Deployment

## 🤝 Beitragen

Pull Requests willkommen! Bitte beachten:

1. Fork des Repositories
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Tests hinzufügen
4. Commit mit aussagekräftiger Nachricht
5. Push zum Branch
6. Pull Request öffnen

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE)

## ⚠️ Haftungsausschluss

Diese Software dient als Hilfsmittel zur Erstellung GoBD-konformer Rechnungen. Der Betreiber ist selbst verantwortlich für:
- Korrekte Konfiguration
- Einhaltung steuerrechtlicher Vorschriften
- Ordnungsgemäße Archivierung
- Datenschutz-Compliance

**Keine Garantie für steuerliche oder rechtliche Korrektheit.**  
Bitte konsultieren Sie einen Steuerberater für rechtsverbindliche Auskünfte.

## 📞 Support

- **Issues**: GitHub Issues für Bug-Reports
- **Diskussionen**: GitHub Discussions für Fragen
- **Email**: support@ihre-domain.de (für kommerzielle Anfragen)

## 🙏 Danksagungen

- **pyHanko**: PDF-Signatur und Zeitstempel
- **ReportLab**: PDF-Generierung
- **pikepdf**: PDF/A-3 Manipulation
- **lxml**: ZUGFeRD XML
- **FastAPI**: Backend-Framework
- **React**: Frontend-Framework

---

**Made with ❤️ in Germany für deutsche Buchhalter**
