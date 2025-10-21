# Rechnungserstellung nach GoBD-Standards

## 📋 Übersicht

Dieses System erstellt rechtskonforme elektronische Rechnungen für Deutschland nach:

- **§14 UStG** (Umsatzsteuergesetz) - Pflichtangaben für Rechnungen
- **§147 AO** (Abgabenordnung) - 10-jährige Aufbewahrungspflicht
- **GoBD** (Grundsätze zur ordnungsmäßigen Führung und Aufbewahrung von Büchern, Aufzeichnungen und Unterlagen in elektronischer Form)

## 🔐 Sicherheitsmerkmale

### 1. PDF/A-3 Format
- **Langzeitarchivierung**: ISO 19005-3 konform
- **Maschinell lesbar**: Strukturierte Daten eingebettet
- **Unveränderbar**: Format verhindert nachträgliche Änderungen

### 2. ZUGFeRD XML (EN-16931)
- **Strukturierte Rechnungsdaten**: Maschinenlesbar eingebettet
- **Europäischer Standard**: EN-16931 konform
- **Automatische Verarbeitung**: DATEV, Lexware, SAP kompatibel

### 3. RFC3161 Zeitstempel (TSA)
- **Rechtsverbindlicher Zeitstempel**: Von akkreditierter Zeitstempelstelle
- **Revisionssicherheit**: Nachweisbare Unveränderbarkeit
- **GoBD-Konformität**: Erfüllt Anforderungen an technische Sicherheit

### 4. Fortlaufende Rechnungsnummern
- **Lückenlose Nummerierung**: Datenbank-gesichert
- **Keine Duplikate**: Transaction-Level-Locks
- **Anpassbares Format**: Prefix + 6-stellige Nummer

## 📝 Rechnungserstellung - Schritt für Schritt

### Phase 1: Datenvorbereitung

```python
invoice_data = InvoiceCreate(
    # Pflichtangaben Verkäufer (§14 UStG Abs. 4 Nr. 1)
    seller=Seller(
        name="Musterfirma GmbH",
        street="Musterstraße 123",
        zip="10115",
        city="Berlin",
        country="DE",
        tax_id="DE123456789",  # USt-IdNr. PFLICHT
        email="rechnung@musterfirma.de",
        phone="+49 30 12345678"
    ),
    
    # Pflichtangaben Käufer (§14 UStG Abs. 4 Nr. 1)
    buyer=Buyer(
        name="Kundenfirma AG",
        street="Kundenweg 456",
        zip="80331",
        city="München",
        country="DE",
        tax_id="DE987654321",  # Optional bei Privatpersonen
        email="buchhaltung@kunde.de"
    ),
    
    # Rechnungsdatum (§14 UStG Abs. 4 Nr. 3)
    issue_date=datetime.now(),
    
    # Lieferdatum (§14 UStG Abs. 4 Nr. 6)
    delivery_date_start=datetime(2025, 10, 15),
    delivery_date_end=datetime(2025, 10, 15),
    
    # Währung
    currency="EUR",
    
    # Rechnungspositionen (§14 UStG Abs. 4 Nr. 5, 6, 8)
    line_items=[
        InvoiceLineItem(
            description="Softwareentwicklung - Sprint 1",
            quantity=40.0,
            unit="H",  # Stunden
            unit_price=95.00,
            tax_rate=19.0  # MwSt. 19%
        ),
        InvoiceLineItem(
            description="Projektmanagement",
            quantity=8.0,
            unit="H",
            unit_price=120.00,
            tax_rate=19.0
        )
    ],
    
    # Zahlungsbedingungen
    payment_terms="Zahlbar innerhalb von 14 Tagen ohne Abzug.",
    
    # Optionale Hinweise
    notes="Vielen Dank für Ihren Auftrag!"
)
```

### Phase 2: Rechnungsnummer generieren

**Anforderungen (GoBD):**
- ✅ Fortlaufend
- ✅ Lückenlos
- ✅ Eindeutig
- ✅ Unveränderbar

**Implementation:**
```python
async def _generate_invoice_number(self) -> str:
    """
    Generiert eindeutige, fortlaufende Rechnungsnummer
    
    - Verwendet Datenbank-Sequenz mit FOR UPDATE Lock
    - Verhindert Race Conditions bei gleichzeitigen Anfragen
    - Format: RE{JAHR}{6-stellige Nummer}
    """
    prefix = settings.INVOICE_NUMBER_PREFIX  # z.B. "RE2025"
    
    # Transaktion mit Row-Level Lock
    sequence = self.db.query(InvoiceNumberSequence)\
        .filter(InvoiceNumberSequence.prefix == prefix)\
        .with_for_update()\
        .first()
    
    if not sequence:
        sequence = InvoiceNumberSequence(
            prefix=prefix,
            current_number=1
        )
        self.db.add(sequence)
    
    invoice_number = f"{prefix}{sequence.current_number:06d}"
    sequence.current_number += 1
    
    return invoice_number
    # Ergebnis: RE2025000001, RE2025000002, ...
```

### Phase 3: Beträge berechnen

**Nach §14 UStG Abs. 4 Nr. 5, 8:**
- Menge × Einzelpreis = Nettobetrag (Position)
- Nettobetrag × MwSt.-Satz = Steuerbetrag
- Nettobetrag + Steuerbetrag = Bruttobetrag

```python
# Positionsberechnung
for item in invoice_data.line_items:
    line_net = round(item.quantity * item.unit_price, 2)
    tax_amount = round(line_net * item.tax_rate / 100, 2)
    line_gross = round(line_net + tax_amount, 2)
    
    net_total += line_net
    tax_total += tax_amount

gross_total = round(net_total + tax_total, 2)
```

**Beispielrechnung:**
```
Position 1: 40 H × 95,00 € = 3.800,00 € netto
  + MwSt. 19%                =   722,00 €
  = Brutto                   = 4.522,00 €

Position 2: 8 H × 120,00 € =   960,00 € netto
  + MwSt. 19%              =   182,40 €
  = Brutto                 = 1.142,40 €

GESAMT:
  Nettobetrag:   4.760,00 €
  MwSt. 19%:       904,40 €
  ────────────────────────
  Bruttobetrag:  5.664,40 €
```

### Phase 4: ZUGFeRD XML generieren

**ZUGFeRD** = Zentraler User Guide des Forums elektronische Rechnung Deutschland

**Standard:** EN-16931 (europäische Norm für elektronische Rechnungen)

**Vorteile:**
- ✅ Maschinenlesbar
- ✅ Automatische Verbuchung möglich
- ✅ Kompatibel mit DATEV, Lexware, SAP
- ✅ Reduziert manuelle Eingabe

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice 
    xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
    xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
    
    <!-- Kontext -->
    <rsm:ExchangedDocumentContext>
        <ram:GuidelineSpecifiedDocumentContextParameter>
            <ram:ID>urn:cen.eu:en16931:2017#compliant#urn:factur-x.eu:1p0:basic</ram:ID>
        </ram:GuidelineSpecifiedDocumentContextParameter>
    </rsm:ExchangedDocumentContext>
    
    <!-- Rechnungskopf -->
    <rsm:ExchangedDocument>
        <ram:ID>RE2025000001</ram:ID>
        <ram:TypeCode>380</ram:TypeCode> <!-- 380 = Handelsrechnung -->
        <ram:IssueDateTime>
            <udt:DateTimeString format="102">20251022</udt:DateTimeString>
        </ram:IssueDateTime>
    </rsm:ExchangedDocument>
    
    <!-- Transaktionsdaten -->
    <rsm:SupplyChainTradeTransaction>
        <!-- Rechnungspositionen -->
        <ram:IncludedSupplyChainTradeLineItem>
            <ram:AssociatedDocumentLineDocument>
                <ram:LineID>1</ram:LineID>
            </ram:AssociatedDocumentLineDocument>
            <ram:SpecifiedTradeProduct>
                <ram:Name>Softwareentwicklung - Sprint 1</ram:Name>
            </ram:SpecifiedTradeProduct>
            <!-- ... -->
        </ram:IncludedSupplyChainTradeLineItem>
        
        <!-- Verkäufer -->
        <ram:ApplicableHeaderTradeAgreement>
            <ram:SellerTradeParty>
                <ram:Name>Musterfirma GmbH</ram:Name>
                <ram:PostalTradeAddress>
                    <ram:PostcodeCode>10115</ram:PostcodeCode>
                    <ram:LineOne>Musterstraße 123</ram:LineOne>
                    <ram:CityName>Berlin</ram:CityName>
                    <ram:CountryID>DE</ram:CountryID>
                </ram:PostalTradeAddress>
                <ram:SpecifiedTaxRegistration>
                    <ram:ID schemeID="VA">DE123456789</ram:ID>
                </ram:SpecifiedTaxRegistration>
            </ram:SellerTradeParty>
            
            <!-- Käufer -->
            <ram:BuyerTradeParty>
                <!-- ... -->
            </ram:BuyerTradeParty>
        </ram:ApplicableHeaderTradeAgreement>
        
        <!-- Summen -->
        <ram:ApplicableHeaderTradeSettlement>
            <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
            <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                <ram:LineTotalAmount>4760.00</ram:LineTotalAmount>
                <ram:TaxBasisTotalAmount>4760.00</ram:TaxBasisTotalAmount>
                <ram:TaxTotalAmount currencyID="EUR">904.40</ram:TaxTotalAmount>
                <ram:GrandTotalAmount>5664.40</ram:GrandTotalAmount>
                <ram:DuePayableAmount>5664.40</ram:DuePayableAmount>
            </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        </ram:ApplicableHeaderTradeSettlement>
    </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>
```

### Phase 5: PDF/A-3 generieren

**PDF/A-3** = PDF für Langzeitarchivierung mit eingebetteten Dateien

**Anforderungen:**
- ISO 19005-3 konform
- Alle Schriften eingebettet
- Keine externen Referenzen
- Farbprofil eingebettet
- Strukturierte Daten einbettbar

**Layout nach deutschen Standards:**

```
┌─────────────────────────────────────────────────────────────┐
│  Rechnung RE2025000001                          [Logo]      │
│                                                              │
│  Rechnungssteller:           Rechnungsempfänger:           │
│  Musterfirma GmbH            Kundenfirma AG                │
│  Musterstraße 123            Kundenweg 456                 │
│  10115 Berlin                80331 München                 │
│  Deutschland                 Deutschland                   │
│  USt-IdNr: DE123456789       USt-IdNr: DE987654321        │
│                                                              │
│  Rechnungsnummer: RE2025000001                              │
│  Rechnungsdatum:  22.10.2025                               │
│  Lieferdatum:     15.10.2025                               │
│  Währung:         EUR                                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Rechnungspositionen                                   │  │
│  ├────┬──────────────┬──────┬────┬────────┬─────┬────────┤  │
│  │Pos.│Beschreibung  │Menge │Ein.│Preis   │MwSt.│Gesamt  │  │
│  ├────┼──────────────┼──────┼────┼────────┼─────┼────────┤  │
│  │ 1  │Software...   │40,00 │H   │95,00 € │19% │4.522,00│  │
│  │ 2  │Projektmgmt.  │ 8,00 │H   │120,00€ │19% │1.142,40│  │
│  └────┴──────────────┴──────┴────┴────────┴─────┴────────┘  │
│                                                              │
│                                      Nettobetrag:  4.760,00€│
│                                      MwSt. 19%:      904,40€│
│                                      ─────────────────────── │
│                                      Gesamtbetrag: 5.664,40€│
│                                                              │
│  Zahlungsbedingungen:                                       │
│  Zahlbar innerhalb von 14 Tagen ohne Abzug.                │
│                                                              │
│  Hinweise:                                                   │
│  Vielen Dank für Ihren Auftrag!                             │
│                                                              │
│  ────────────────────────────────────────────────────────── │
│  Dieses Dokument wurde maschinell erstellt und ist ohne    │
│  Unterschrift gültig. Die Rechnung entspricht den          │
│  Anforderungen nach §14 UStG und ist GoBD-konform          │
│  archiviert. PDF/A-3 mit eingebettetem ZUGFeRD XML.        │
└─────────────────────────────────────────────────────────────┘
```

**XML-Einbettung:**
```python
# ZUGFeRD XML in PDF einbetten (pikepdf)
xml_stream = pdf.make_stream(zugferd_xml_bytes)
xml_stream.Type = Name.EmbeddedFile
xml_stream.Subtype = Name('/text#2Fxml')

file_spec = Dictionary(
    Type=Name.Filespec,
    F='zugferd-invoice.xml',
    UF='zugferd-invoice.xml',
    EF=Dictionary(F=xml_stream),
    AFRelationship=Name.Alternative  # PDF/A-3 Pflicht
)

# Als "Associated File" markieren
pdf.Root.AF = Array([file_spec])
```

### Phase 6: RFC3161 Zeitstempel

**RFC3161 TSA** = Time Stamp Authority (Zeitstempelstelle)

**Zweck:**
- Beweist Existenz des Dokuments zu bestimmtem Zeitpunkt
- Verhindert nachträgliches Backdating
- Rechtsverbindlich anerkannt

**Ablauf:**
```
1. PDF-Hash berechnen (SHA-256)
   → 3f7a9c4b2e1d8f5a6b9c0e3d7f2a8c1b...

2. Hash an TSA senden
   POST https://timestamp.digicert.com
   Content-Type: application/timestamp-query
   
3. TSA signiert Hash mit eigenem Zertifikat
   + fügt aktuellen Zeitstempel hinzu
   
4. Zeitstempel-Token zurück
   {
     "timestamp": "2025-10-22T14:30:45Z",
     "hash": "3f7a9c4b...",
     "tsa_signature": "MIIFaA...",
     "certificate_chain": [...]
   }

5. Token in PDF einbetten (als Signature)
```

**pyHanko Implementation:**
```python
from pyhanko.sign import signers, timestamps

# TSA-Client konfigurieren
tsa_client = timestamps.HTTPTimeStamper(
    url="https://freetsa.org/tsr",  # Kostenlose TSA
    # Produktiv: DigiCert, GlobalSign, etc.
)

# Zeitstempel hinzufügen
signer = signers.PdfTimeStamper(timestamper=tsa_client)

signers.sign_pdf(
    pdf_writer,
    sig_meta=PdfSignatureMetadata(
        field_name='Timestamp',
        name='RFC3161 TimeStamp',
        reason='GoBD Revisionssicherheit'
    ),
    signer=signer,
    output=output_stream
)
```

### Phase 7: Speicherung

**Datenbank (SQLite/PostgreSQL):**
```sql
INSERT INTO invoices (
    invoice_number,
    issue_date,
    seller_name, seller_tax_id, ...,
    buyer_name, buyer_tax_id, ...,
    net_total, tax_total, gross_total,
    pdfa3_path,
    zugferd_xml_path,
    pdf_hash,
    tsa_token,
    status,
    is_immutable,  -- TRUE = unveränderbar
    created_by,
    created_at
) VALUES (...);
```

**Dateispeicherung (S3/MinIO/Filesystem):**
```
storage/
├── invoices/
│   ├── RE2025000001/
│   │   ├── v1/
│   │   │   ├── invoice.pdf      (PDF/A-3)
│   │   │   ├── zugferd.xml      (ZUGFeRD XML)
│   │   │   ├── tsa-token.json   (Zeitstempel)
│   │   │   └── metadata.json    (Metadaten)
│   │   └── checksums.sha256     (Hashes)
│   └── RE2025000002/
│       └── ...
```

**GoBD-Anforderungen an Speicherung:**
- ✅ **Unveränderbarkeit**: Write-Once-Read-Many (WORM)
- ✅ **Versionierung**: Alle Versionen archiviert
- ✅ **Zugriffskontrolle**: Audit-Logs für jeden Zugriff
- ✅ **Backup**: Georedundant, automatisch
- ✅ **Aufbewahrungsfrist**: 10 Jahre (§147 AO)

### Phase 8: Audit-Log erstellen

**Jede Aktion protokollieren:**
```sql
INSERT INTO audit_logs (
    user_id,
    entity_type,
    entity_id,
    action,
    details,
    ip_address,
    user_agent,
    timestamp
) VALUES (
    42,  -- User ID
    'invoice',
    1001,  -- Invoice ID
    'create',
    '{"invoice_number": "RE2025000001", "gross_total": 5664.40}',
    '192.168.1.100',
    'Mozilla/5.0...',
    '2025-10-22 14:30:45'
);
```

**Protokollierte Aktionen:**
- `create` - Rechnung erstellt
- `view` - Rechnung angezeigt
- `download` - PDF heruntergeladen
- `cancel` - Rechnung storniert
- `export` - Daten exportiert

## 🔍 Validierung und Prüfung

### PDF/A-3 Validierung
```bash
# Mit veraPDF (Industry-Standard)
verapdf --format text invoice.pdf

# Erwartete Ausgabe:
# PDF/A-3b: VALID
# ZUGFeRD: Embedded file found
# Profile: PDF/A-3b
```

### ZUGFeRD XML Validierung
```python
from lxml import etree

# XML Schema Validation
schema = etree.XMLSchema(file="ZUGFeRD_2p2.xsd")
xml_doc = etree.parse("zugferd.xml")

is_valid = schema.validate(xml_doc)
# True = EN-16931 konform
```

### Zeitstempel-Prüfung
```python
from pyhanko.sign import validation

# PDF-Signatur validieren
result = validation.validate_pdf_signature(pdf_stream)

print(f"Zeitstempel gültig: {result.timestamp_validity.valid}")
print(f"Zeitstempel: {result.timestamp_validity.timestamp}")
print(f"TSA: {result.timestamp_validity.tsa_name}")
```

## 📊 Checkliste: GoBD-konforme Rechnung

### Pflichtangaben (§14 UStG)
- ✅ Vollständiger Name und Anschrift Leistender
- ✅ Vollständiger Name und Anschrift Leistungsempfänger
- ✅ Steuernummer oder USt-IdNr. Leistender
- ✅ Ausstellungsdatum
- ✅ Fortlaufende Rechnungsnummer
- ✅ Menge und Art der gelieferten Gegenstände/Umfang der Leistung
- ✅ Zeitpunkt der Lieferung/Leistung
- ✅ Entgelt nach Steuersätzen aufgeschlüsselt
- ✅ Steuersatz und Steuerbetrag
- ✅ Bei Steuerbefreiung: Hinweis auf Vorschrift

### Technische Anforderungen (GoBD)
- ✅ PDF/A-3 Format (Langzeitarchivierung)
- ✅ ZUGFeRD XML eingebettet (Maschinenlesbar)
- ✅ RFC3161 Zeitstempel (Revisionssicherheit)
- ✅ SHA-256 Hash (Integrität)
- ✅ Fortlaufende Nummerierung (Lückenlos)
- ✅ Unveränderbare Speicherung (WORM)
- ✅ Vollständige Audit-Logs (Nachvollziehbarkeit)
- ✅ 10 Jahre Aufbewahrung (§147 AO)

### Organisatorische Anforderungen
- ✅ Verfahrensdokumentation vorhanden
- ✅ Zugriffsberechtigungen definiert
- ✅ Backup-Strategie dokumentiert
- ✅ Datenschutz-Konzept (DSGVO)
- ✅ Notfall-Wiederherstellung getestet

## 🎯 Zusammenfassung

Das System erstellt GoBD-konforme Rechnungen durch:

1. **Eindeutige Identifikation**: Fortlaufende, lückenlose Rechnungsnummern
2. **Vollständige Daten**: Alle §14 UStG Pflichtangaben enthalten
3. **Strukturierte Daten**: ZUGFeRD XML für automatische Verarbeitung
4. **Langzeitformat**: PDF/A-3 für 10+ Jahre lesbar
5. **Rechtsverbindlicher Zeitstempel**: RFC3161 TSA für Beweiskraft
6. **Unveränderbarkeit**: Kryptographische Hashes und WORM-Speicherung
7. **Nachvollziehbarkeit**: Vollständige Audit-Logs aller Aktionen
8. **Prüffähigkeit**: Jederzeit für Betriebsprüfung bereit

## 📚 Weiterführende Informationen

- **BMF GoBD**: [bundesfinanzministerium.de](https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Weitere_Steuerthemen/Abgabenordnung/2019-11-28-GoBD.pdf)
- **§14 UStG**: [gesetze-im-internet.de](https://www.gesetze-im-internet.de/ustg_1980/__14.html)
- **ZUGFeRD**: [ferd-net.de](https://www.ferd-net.de/)
- **EN-16931**: [ec.europa.eu](https://ec.europa.eu/digital-building-blocks/wikis/display/DIGITAL/Standards)
- **PDF/A-3**: [pdfa.org](https://www.pdfa.org/resource/pdf-a-3/)
- **RFC3161**: [tools.ietf.org](https://tools.ietf.org/html/rfc3161)
