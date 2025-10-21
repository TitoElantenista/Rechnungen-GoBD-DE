# TSA (Time Stamping Authority) Konfiguration

## Was ist TSA?

Eine Time Stamping Authority (TSA) stellt **RFC3161-konforme Zeitstempel** aus, die beweisen, dass ein Dokument zu einem bestimmten Zeitpunkt existiert hat. Dies ist für GoBD-Konformität erforderlich.

## Warum TSA für GoBD?

- **Revisionssicherheit**: Beweist, wann eine Rechnung erstellt wurde
- **Unveränderbarkeit**: Zeitstempel kann nicht nachträglich geändert werden
- **Rechtssicherheit**: Von vertrauenswürdiger Drittpartei ausgestellt
- **Integrität**: Hashwert des Dokuments ist im Zeitstempel eingebettet

## Empfohlene TSA-Anbieter (Deutschland)

### 1. Bundesdruckerei D-Trust ⭐ (Empfohlen für behördliche Nutzung)

**Anbieter**: D-TRUST GmbH (Bundesdruckerei-Gruppe)
**Website**: https://www.d-trust.net/

**Vorteile:**
- Staatlich anerkannt in Deutschland
- Höchste Vertrauensstufe
- Ideal für B2G (Business-to-Government)
- EU eIDAS-qualifiziert

**Kosten:** ca. 100-500 €/Jahr (je nach Volumen)

**Konfiguration:**
```env
TSA_URL=https://zeitstempel.d-trust.net/tsa
TSA_USERNAME=ihr_benutzername
TSA_PASSWORD=ihr_passwort
TSA_HASH_ALGORITHM=SHA256
```

### 2. GlobalSign

**Anbieter**: GlobalSign
**Website**: https://www.globalsign.com/

**Vorteile:**
- International anerkannt
- Gute API-Dokumentation
- Flexible Preismodelle

**Kosten:** ca. 50-300 €/Jahr

**Konfiguration:**
```env
TSA_URL=http://timestamp.globalsign.com/tsa/r6advanced1
TSA_USERNAME=
TSA_PASSWORD=
TSA_HASH_ALGORITHM=SHA256
```

### 3. DigiStamp

**Anbieter**: DigiStamp
**Website**: https://www.digistamp.com/

**Vorteile:**
- Spezialisiert auf Zeitstempel
- Pay-per-use Modell verfügbar

**Kosten:** ab 0,01 €/Zeitstempel

### 4. DigiCert (kostenlos für Tests)

**Anbieter**: DigiCert
**Website**: http://timestamp.digicert.com

**Vorteile:**
- Kostenlos nutzbar
- Keine Registrierung erforderlich
- Gut für Tests und Entwicklung

**⚠️ Einschränkungen:**
- Nicht für Produktion empfohlen
- Keine Garantie auf Verfügbarkeit
- Nicht für rechtssichere Archivierung

**Konfiguration:**
```env
TSA_URL=http://timestamp.digicert.com
TSA_USERNAME=
TSA_PASSWORD=
TSA_HASH_ALGORITHM=SHA256
```

## Konfiguration in diesem Projekt

### 1. Umgebungsvariablen setzen

Bearbeite `backend/.env`:

```env
# Für Produktion (D-Trust Beispiel)
TSA_URL=https://zeitstempel.d-trust.net/tsa
TSA_USERNAME=ihr_benutzername
TSA_PASSWORD=ihr_passwort
TSA_HASH_ALGORITHM=SHA256

# Für Development (DigiCert kostenlos)
TSA_URL=http://timestamp.digicert.com
TSA_USERNAME=
TSA_PASSWORD=
TSA_HASH_ALGORITHM=SHA256
```

### 2. Zertifikate (falls erforderlich)

Einige TSA-Anbieter erfordern Client-Zertifikate. Speichere diese in `backend/certs/`:

```bash
backend/
├── certs/
│   ├── client.pem
│   ├── client.key
│   └── ca-chain.pem
```

Konfiguration in `backend/app/services/signature_service.py` anpassen.

### 3. Test der TSA-Verbindung

```bash
# Im Backend-Container oder lokal
python scripts/test_tsa.py
```

## Wie funktioniert RFC3161 Timestamping?

1. **Hash berechnen**: SHA-256 Hash des PDF wird berechnet
2. **TSA-Request**: Hash wird an TSA gesendet
3. **Zeitstempel-Token**: TSA antwortet mit signiertem Token (inkl. Zeit + Hash)
4. **Einbettung**: Token wird in PDF als PAdES-Signatur eingebettet

```
PDF → SHA256 → TSA → Signierter Token → PDF/A-3 mit eingebettetem Token
```

## Verifizierung von Zeitstempeln

### Mit pyHanko (Python)

```python
from pyhanko.sign import validation
from io import BytesIO

with open("rechnung.pdf", "rb") as f:
    pdf_bytes = f.read()

result = validation.validate_pdf_signature(BytesIO(pdf_bytes))
print(f"Zeitstempel gültig: {result.timestamp_validity.valid}")
print(f"Zeitpunkt: {result.timestamp_validity.timestamp}")
```

### Mit Adobe Acrobat

1. PDF öffnen
2. Signaturfeld anklicken
3. "Signatur-Details" → "Zeitstempel-Details"

## Rechtliche Hinweise

### GoBD-Konformität

Laut GoBD müssen elektronische Rechnungen:
- **Unveränderbar** archiviert werden → TSA-Zeitstempel + Object Lock
- **Nachprüfbar** sein → Audit-Logs + Metadaten
- **Vollständig** sein → Lückenlose Rechnungsnummern

### Aufbewahrungspflicht

Zeitstempel-Token müssen zusammen mit dem PDF **10 Jahre** aufbewahrt werden (§147 AO).

### Prüfung durch Finanzamt

Bei Betriebsprüfung muss nachgewiesen werden:
- Wann wurde die Rechnung erstellt?
- Wurde sie nachträglich geändert?
- TSA-Token ist dafür der Nachweis

## Troubleshooting

### "TSA nicht erreichbar"

```python
# Prüfe Firewall / Proxy
curl -X POST https://zeitstempel.d-trust.net/tsa
```

### "Zeitstempel-Validierung fehlgeschlagen"

- Prüfe Systemzeit (NTP)
- Prüfe TSA-Zertifikat (nicht abgelaufen?)
- Prüfe Hash-Algorithmus (SHA-256 supported?)

### "Mock timestamp - not for production"

Im Development-Modus wird ein Mock-Token verwendet, falls TSA nicht verfügbar ist. Für Produktion **echte TSA** konfigurieren!

## Kosten-Kalkulation

**Beispiel: 1.000 Rechnungen/Jahr**

- **D-Trust**: ca. 300 € Flatrate → **0,30 €/Rechnung**
- **DigiStamp**: 1.000 × 0,01 € → **10 €/Jahr**
- **DigiCert (kostenlos)**: **0 €** (nur Tests!)

**Empfehlung:**
- Kleine Unternehmen (< 500 Rechnungen/Jahr): DigiStamp
- Mittlere Unternehmen (500-5000/Jahr): GlobalSign
- Große Unternehmen / Behörden: D-Trust

## Weitere Ressourcen

- **RFC3161**: https://www.ietf.org/rfc/rfc3161.txt
- **PAdES**: https://www.etsi.org/deliver/etsi_ts/102700_102799/10277804/01.01.02_60/ts_10277804v010102p.pdf
- **GoBD**: https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Weitere_Steuerthemen/Abgabenordnung/2019-11-28-GoBD.pdf
