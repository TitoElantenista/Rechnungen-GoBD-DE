# Rechnungsgenerator – GoBD-konform mit PDF/A-3 + ZUGFeRD

Ein minimal lauffähiger Prototyp für **rechtskonforme Rechnungserzeugung** nach deutschen Anforderungen (§14 UStG, GoBD, ZUGFeRD EN-16931).

## Features

- ✅ **PDF/A-3** mit eingebettetem **ZUGFeRD XML** (hybrid: lesbar + maschinenlesbar)
- ✅ **RFC3161 Zeitstempel** (TSA) für Revisionssicherheit
- ✅ **PAdES-Signatur** via pyHanko
- ✅ **Revisionssichere Archivierung** (S3 Object Lock / WORM)
- ✅ **Suche & Filter** (Jahr, Rechnungsnummer, Kunde, USt-ID)
- ✅ **Readonly PDF-Viewer** (keine Änderungen nach Erstellung)
- ✅ Automatische, fortlaufende Rechnungsnummern
- ✅ Vollständige Audit-Logs

## Technologie-Stack

**Backend:**
- Python 3.11+
- FastAPI (asynchron, OpenAPI-Dokumentation)
- SQLAlchemy + Alembic (Migrations)
- PostgreSQL / SQLite
- pyHanko (PAdES, RFC3161 TSA)
- reportlab + pikepdf (PDF/A-3)
- lxml (ZUGFeRD XML)

**Frontend:**
- React 18 + Vite
- Tailwind CSS
- React Router
- Axios

**Infrastructure:**
- Docker + Docker Compose
- MinIO (S3-kompatibles Storage)
- Nginx (reverse proxy)

## Rechtliche Konformität

### §14 UStG Pflichtfelder
Alle Rechnungen enthalten:
- Vollständiger Name und Anschrift des leistenden Unternehmers
- Vollständiger Name und Anschrift des Leistungsempfängers
- Steuernummer oder USt-IdNr. des leistenden Unternehmers
- Ausstellungsdatum
- Fortlaufende Rechnungsnummer
- Menge und Art der gelieferten Gegenstände / Umfang und Art der Leistung
- Zeitpunkt der Lieferung / Leistung
- Entgelt nach Steuersätzen und Steuerbefreiungen
- Anzuwendender Steuersatz und Steuerbetrag
- Hinweis auf Steuerbefreiung (falls zutreffend)

### GoBD-Konformität
- **Unveränderbarkeit**: PDF/A-3 mit PAdES-Signatur + TSA-Zeitstempel
- **Nachvollziehbarkeit**: Vollständige Audit-Logs (User, Timestamp, Aktion)
- **Nachprüfbarkeit**: Export-Funktion (PDF + XML + TSA + Metadaten)
- **Vollständigkeit**: Lückenlose, fortlaufende Rechnungsnummern
- **Ordnungsmäßigkeit**: XSD-Validierung, PDF/A-Konformitätsprüfung

### ZUGFeRD EN-16931
- XML-Schema nach EN-16931 (European Standard for e-invoicing)
- Hybrid: PDF für Menschen, XML für Maschinen
- B2B/B2G kompatibel

## Schnellstart

### Voraussetzungen
```bash
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
```

### 1. Repository klonen
```bash
git clone https://github.com/TitoElantenista/Rechnungen-GoBD-DE.git
cd Rechnungen-GoBD-DE
```

### 2. Umgebungsvariablen konfigurieren
```bash
cp backend/.env.example backend/.env
# TSA-URL und Zugangsdaten eintragen
```

### 3. Mit Docker starten
```bash
docker-compose up -d
```

### 4. Datenbank migrieren
```bash
docker-compose exec backend alembic upgrade head
```

### 5. Anwendung öffnen
```
Frontend: http://localhost:5173
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
MinIO Console: http://localhost:9001
```

## Entwicklung (lokal ohne Docker)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API-Endpoints

```
POST   /api/invoices          # Neue Rechnung erstellen
GET    /api/invoices          # Liste mit Filter/Suche
GET    /api/invoices/{id}     # Rechnungsdetails
GET    /api/invoices/{id}/download  # ZIP (PDF+XML+TSA+Meta)
GET    /api/invoices/{id}/preview   # PDF-Stream readonly
DELETE /api/invoices/{id}     # Stornierung (erzeugt Stornobeleg)
```

Query-Parameter:
- `year`: Filtern nach Jahr
- `q`: Freitext-Suche (Nummer, Kunde, USt-ID)
- `page`, `limit`: Pagination

## Konfiguration

### TSA (Time Stamping Authority)

**Empfohlene Anbieter:**
- **Bundesdruckerei D-Trust** (https://www.d-trust.net/)
- **GlobalSign** (https://www.globalsign.com/)
- **DigiStamp** (https://www.digistamp.com/)

**Test-TSA (nur Entwicklung):**
```env
TSA_URL=http://timestamp.digicert.com
TSA_USERNAME=
TSA_PASSWORD=
```

### S3 Storage (MinIO)
```env
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=invoices
S3_REGION=eu-central-1
```

## Tests

### Backend-Tests
```bash
cd backend
pytest
pytest --cov=app tests/  # Mit Coverage
```

### PDF/A-3 Validierung (veraPDF)
```bash
docker run --rm -v $(pwd)/storage:/data verapdf/verapdf /data/invoice.pdf
```

### ZUGFeRD XML-Validierung
```bash
cd backend
python -m app.services.zugferd_validator tests/fixtures/sample.xml
```

## Architektur

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   React UI  │─────→│  FastAPI     │─────→│ PostgreSQL  │
│  (Browser)  │      │  Backend     │      │   Database  │
└─────────────┘      └──────────────┘      └─────────────┘
                             │
                             ├──────→ MinIO (S3 Storage)
                             │        - PDF/A-3 Files
                             │        - ZUGFeRD XML
                             │        - TSA Tokens
                             │
                             └──────→ TSA Provider (RFC3161)
                                      - Zeitstempel
                                      - PAdES-Signatur
```

## Projekt-Struktur

```
Rechnungen-GoBD-DE/
├── backend/
│   ├── app/
│   │   ├── api/              # API-Routen
│   │   ├── models/           # SQLAlchemy Models
│   │   ├── schemas/          # Pydantic Schemas
│   │   ├── services/         # Business Logic
│   │   │   ├── invoice_generator.py
│   │   │   ├── zugferd_generator.py
│   │   │   ├── pdf_generator.py
│   │   │   ├── signature_service.py
│   │   │   └── archive_service.py
│   │   ├── core/             # Config, Security
│   │   └── main.py
│   ├── tests/
│   ├── alembic/              # DB Migrations
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/       # React Components
│   │   ├── pages/           # Pages
│   │   ├── services/        # API Client
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
├── README.md
└── LICENSE
```

## Sicherheit

- ✅ TLS für alle Verbindungen (HTTPS)
- ✅ Passwortgeschützte UI mit JWT-Authentifizierung
- ✅ Rollen-basierte Zugriffskontrolle (RBAC)
- ✅ Audit-Logs für alle Aktionen
- ✅ SQL-Injection-Schutz (SQLAlchemy ORM)
- ✅ XSS-Schutz (React)
- ✅ CORS-Konfiguration

## Rechtliche Hinweise für Steuerbüro

1. **Dokumentation**: SOP über Erzeugungs- und Archivierungsprozess vorhalten
2. **TSA-Verträge**: Zugang zu TSA-Vertragsdaten/Logs aufbewahren
3. **XRechnung**: Bei B2G prüfen, ob zusätzlich XML-only XRechnung benötigt wird
4. **Aufbewahrung**: 10 Jahre gemäß §147 AO
5. **Prüfbarkeit**: Finanzamt muss jederzeit Zugriff erhalten können

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

## Support & Kontakt

- **Issues**: https://github.com/TitoElantenista/Rechnungen-GoBD-DE/issues
- **Dokumentation**: Siehe `/docs` Ordner

## Roadmap

- [ ] MVP (v0.1.0) - Basis-Funktionalität
- [ ] Mandantenfähigkeit (v0.2.0)
- [ ] E-Mail-Versand (v0.3.0)
- [ ] XRechnung-Export (v0.4.0)
- [ ] Mehrwährungsunterstützung (v0.5.0)
- [ ] ERP-Integration (v1.0.0)

---

**Status**: 🚧 In Entwicklung (MVP)
