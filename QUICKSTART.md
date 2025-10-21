# Schnellstart-Anleitung

## 🚀 Método más Rápido: Script Python (Desarrollo Local)

### Prerrequisitos
```bash
# Instalar psutil
pip3 install psutil
```

### Iniciar la Aplicación

#### Opción 1: Desde VS Code (Más Fácil)
1. Abre el proyecto en VS Code
2. Presiona **F5** o haz clic en el botón Play ▶️
3. Selecciona **"🚀 Iniciar Aplicación Completa"**
4. ¡Listo! Backend y Frontend se inician automáticamente

#### Opción 2: Línea de Comandos
```bash
# Iniciar aplicación completa
python3 run.py start

# Ver estado
python3 run.py status

# Detener aplicación
python3 run.py stop

# Reiniciar aplicación
python3 run.py restart
```

### URLs de Acceso
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Credenciales
- Usuario: `admin`
- Password: `admin`

---

## 🐳 Método con Docker (Producción)

## Voraussetzungen

- Docker & Docker Compose
- (Optional) Python 3.11+ für lokale Entwicklung
- (Optional) Node.js 18+ für lokale Entwicklung

## Schritt 1: Umgebungsvariablen konfigurieren

```bash
# Backend-Konfiguration kopieren
cp backend/.env.example backend/.env

# Optional: TSA-Anbieter konfigurieren (für Produktion erforderlich)
# Öffne backend/.env und trage TSA-URL und Zugangsdaten ein
```

## Schritt 2: Docker-Container starten

```bash
# Alle Services starten (PostgreSQL, MinIO, Backend, Frontend)
docker-compose up -d

# Logs anzeigen
docker-compose logs -f
```

## Schritt 3: Datenbank initialisieren

```bash
# In Backend-Container wechseln
docker-compose exec backend bash

# Datenbank-Tabellen erstellen
alembic upgrade head

# Admin-Benutzer anlegen
python scripts/seed_admin.py

# Container verlassen
exit
```

## Schritt 4: Anwendung öffnen

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Dokumentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

**Standard-Login:**
- Benutzername: `admin`
- Passwort: `admin`

⚠️ **Wichtig**: Passwort in Produktion ändern!

## Schritt 5: Erste Rechnung erstellen

1. Im Frontend einloggen
2. "Neue Rechnung" klicken
3. Formular ausfüllen (alle Pflichtfelder gemäß §14 UStG)
4. "Erstellen" klicken
5. PDF/A-3 mit ZUGFeRD XML wird generiert und signiert
6. Rechnung ist revisionssicher archiviert

## Lokale Entwicklung (ohne Docker)

### Backend

```bash
cd backend

# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt

# Datenbank initialisieren
alembic upgrade head
python scripts/seed_admin.py

# Server starten
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

# Dependencies installieren
npm install

# Dev-Server starten
npm run dev
```

## Nächste Schritte

### TSA-Anbieter konfigurieren (Produktion)

Für rechtskonforme Zeitstempel in Produktion:

1. **Bundesdruckerei D-Trust**: https://www.d-trust.net/
2. **GlobalSign**: https://www.globalsign.com/
3. **DigiStamp**: https://www.digistamp.com/

Konfiguration in `backend/.env`:

```env
TSA_URL=https://tsa.d-trust.net/tsa
TSA_USERNAME=your_username
TSA_PASSWORD=your_password
```

### Weitere Konfiguration

- **S3 Storage**: Für Produktion AWS S3 oder MinIO mit Object Lock konfigurieren
- **Backup**: Regelmäßige Backups von Datenbank und S3 einrichten
- **Monitoring**: Logs und Metrics überwachen
- **SSL/TLS**: HTTPS mit gültigem Zertifikat einrichten

## Probleme?

**Backend startet nicht:**
- Prüfe `docker-compose logs backend`
- Stelle sicher, dass PostgreSQL läuft
- Prüfe Datenbankverbindung in `.env`

**Frontend zeigt Fehler:**
- Prüfe `docker-compose logs frontend`
- Stelle sicher, dass Backend erreichbar ist
- Prüfe CORS-Konfiguration

**TSA-Signatur funktioniert nicht:**
- Im Development-Modus wird ein Mock-Token verwendet
- Für Produktion: TSA-Anbieter konfigurieren

## Hilfe & Support

- **Issues**: https://github.com/TitoElantenista/Rechnungen-GoBD-DE/issues
- **Dokumentation**: Siehe `/docs` Ordner
