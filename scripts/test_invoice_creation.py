#!/usr/bin/env python3
"""
Test-Script zur Erstellung einer GoBD-konformen Rechnung

Dieses Script demonstriert die vollständige Rechnungserstellung
nach deutschen Standards (§14 UStG, GoBD).
"""

import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

# Konfiguration
API_BASE_URL = "http://localhost:8000/api"
USERNAME = "admin"
PASSWORD = "admin"

def login():
    """Einloggen und Access Token erhalten"""
    print("🔐 Einloggen...")
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    print(f"✅ Login erfolgreich! Token: {token[:20]}...")
    return token

def create_invoice(token):
    """
    Erstellt eine vollständige GoBD-konforme Rechnung
    
    Beinhaltet alle Pflichtangaben nach §14 UStG:
    - Vollständige Verkäufer-/Käuferangaben
    - USt-IdNr.
    - Rechnungsdatum
    - Lieferdatum
    - Detaillierte Rechnungspositionen
    - Mehrwertsteuersätze
    - Zahlungsbedingungen
    """
    print("\n📄 Erstelle Rechnung...")
    
    # Aktuelles Datum
    today = datetime.now()
    delivery_date = today - timedelta(days=7)
    
    invoice_data = {
        # Verkäufer (Rechnungssteller)
        "seller": {
            "name": "Musterfirma Software GmbH",
            "street": "Innovationsstraße 42",
            "zip": "10115",
            "city": "Berlin",
            "country": "DE",
            "tax_id": "DE123456789",  # USt-IdNr. PFLICHT nach §14 UStG
            "email": "rechnung@musterfirma.de",
            "phone": "+49 30 12345678"
        },
        
        # Käufer (Rechnungsempfänger)
        "buyer": {
            "name": "Kundenfirma Handel AG",
            "street": "Hauptstraße 123",
            "zip": "80331",
            "city": "München",
            "country": "DE",
            "tax_id": "DE987654321",  # Optional bei Privatpersonen
            "email": "buchhaltung@kundenfirma.de",
            "phone": "+49 89 98765432"
        },
        
        # Rechnungsdatum (§14 UStG Abs. 4 Nr. 3)
        "issue_date": today.strftime("%Y-%m-%d"),
        
        # Lieferdatum (§14 UStG Abs. 4 Nr. 6)
        "delivery_date_start": delivery_date.strftime("%Y-%m-%d"),
        "delivery_date_end": delivery_date.strftime("%Y-%m-%d"),
        
        # Währung
        "currency": "EUR",
        
        # Rechnungspositionen (§14 UStG Abs. 4 Nr. 5, 8)
        "line_items": [
            {
                "description": "Softwareentwicklung - Sprint 1 (Web-Frontend)",
                "quantity": 40.0,
                "unit": "H",  # Stunden
                "unit_price": 95.00,
                "tax_rate": 19.0  # MwSt. 19% (Regelsteuersatz)
            },
            {
                "description": "Softwareentwicklung - Sprint 1 (Backend-API)",
                "quantity": 35.0,
                "unit": "H",
                "unit_price": 95.00,
                "tax_rate": 19.0
            },
            {
                "description": "Projektmanagement und Koordination",
                "quantity": 8.0,
                "unit": "H",
                "unit_price": 120.00,
                "tax_rate": 19.0
            },
            {
                "description": "Code-Review und Qualitätssicherung",
                "quantity": 12.0,
                "unit": "H",
                "unit_price": 85.00,
                "tax_rate": 19.0
            },
            {
                "description": "Fachbuch: 'Clean Code' (reduzierter MwSt.-Satz)",
                "quantity": 1.0,
                "unit": "Stk",
                "unit_price": 42.00,
                "tax_rate": 7.0  # MwSt. 7% (ermäßigter Satz für Bücher)
            }
        ],
        
        # Zahlungsbedingungen
        "payment_terms": (
            "Zahlbar innerhalb von 14 Tagen ohne Abzug. "
            "Bei Zahlung innerhalb von 7 Tagen gewähren wir 2% Skonto. "
            "Bitte überweisen Sie auf: IBAN DE89 3704 0044 0532 0130 00, "
            "BIC COBADEFFXXX, Commerzbank AG."
        ),
        
        # Steuerstatus
        "tax_exempt": False,  # Keine Steuerbefreiung
        
        # Hinweise
        "notes": (
            "Vielen Dank für Ihren Auftrag! "
            "Bei Rückfragen stehen wir Ihnen gerne zur Verfügung."
        )
    }
    
    # API-Request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/invoices",
        headers=headers,
        json=invoice_data
    )
    
    response.raise_for_status()
    invoice = response.json()
    
    print(f"✅ Rechnung erstellt!")
    print(f"   📋 Rechnungsnummer: {invoice['invoice_number']}")
    print(f"   📅 Rechnungsdatum: {invoice['issue_date']}")
    print(f"   💰 Nettobetrag: {invoice['net_total']:.2f} {invoice['currency']}")
    print(f"   💰 MwSt.: {invoice['tax_total']:.2f} {invoice['currency']}")
    print(f"   💰 Bruttobetrag: {invoice['gross_total']:.2f} {invoice['currency']}")
    print(f"   🔐 PDF-Hash: {invoice['pdf_hash'][:16]}...")
    print(f"   ⏱️  TSA-Zeitstempel: {invoice['tsa_token'].get('timestamp', 'N/A')}")
    
    return invoice

def download_invoice_pdf(token, invoice_id, invoice_number):
    """PDF herunterladen"""
    print(f"\n📥 Lade PDF herunter...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE_URL}/invoices/{invoice_id}/download",
        headers=headers
    )
    
    response.raise_for_status()
    
    # PDF speichern
    pdf_path = Path(f"{invoice_number}.pdf")
    pdf_path.write_bytes(response.content)
    
    print(f"✅ PDF gespeichert: {pdf_path.absolute()}")
    print(f"   📊 Größe: {len(response.content) / 1024:.1f} KB")
    
    return pdf_path

def download_archive(token, invoice_id, invoice_number):
    """Komplettes Archiv herunterladen (PDF + XML + TSA + Metadaten)"""
    print(f"\n📦 Lade Archiv herunter...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE_URL}/invoices/{invoice_id}/archive",
        headers=headers
    )
    
    response.raise_for_status()
    
    # ZIP speichern
    zip_path = Path(f"{invoice_number}_archive.zip")
    zip_path.write_bytes(response.content)
    
    print(f"✅ Archiv gespeichert: {zip_path.absolute()}")
    print(f"   📊 Größe: {len(response.content) / 1024:.1f} KB")
    print(f"   📁 Enthält: PDF/A-3, ZUGFeRD XML, TSA Token, Metadaten")
    
    return zip_path

def list_invoices(token):
    """Alle Rechnungen auflisten"""
    print(f"\n📋 Alle Rechnungen:")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE_URL}/invoices",
        headers=headers
    )
    
    response.raise_for_status()
    invoices = response.json()
    
    print(f"\n   Anzahl: {len(invoices)}")
    print(f"   {'Nr.':<15} {'Datum':<12} {'Käufer':<30} {'Betrag':<12} {'Status':<10}")
    print(f"   {'-'*15} {'-'*12} {'-'*30} {'-'*12} {'-'*10}")
    
    for inv in invoices:
        print(f"   {inv['invoice_number']:<15} "
              f"{inv['issue_date']:<12} "
              f"{inv['buyer_name'][:28]:<30} "
              f"{inv['gross_total']:>10.2f} € "
              f"{inv['status']:<10}")

def main():
    """Hauptprogramm"""
    print("=" * 70)
    print("  GoBD-konforme Rechnungserstellung - Test Script")
    print("  § 14 UStG | § 147 AO | GoBD")
    print("=" * 70)
    
    try:
        # 1. Login
        token = login()
        
        # 2. Rechnung erstellen
        invoice = create_invoice(token)
        invoice_id = invoice["id"]
        invoice_number = invoice["invoice_number"]
        
        # 3. PDF herunterladen
        pdf_path = download_invoice_pdf(token, invoice_id, invoice_number)
        
        # 4. Komplettes Archiv herunterladen
        archive_path = download_archive(token, invoice_id, invoice_number)
        
        # 5. Alle Rechnungen auflisten
        list_invoices(token)
        
        print("\n" + "=" * 70)
        print("✅ Test erfolgreich abgeschlossen!")
        print("=" * 70)
        
        print("\n📚 Weitere Schritte:")
        print(f"   1. PDF öffnen: xdg-open {pdf_path}")
        print(f"   2. Archiv extrahieren: unzip {archive_path}")
        print(f"   3. PDF/A-3 validieren: verapdf {pdf_path}")
        print(f"   4. ZUGFeRD prüfen: unzip -p {archive_path} {invoice_number}.xml | xmllint --format -")
        print(f"   5. API Docs: http://localhost:8000/docs")
        print(f"   6. Frontend: http://localhost:5173")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP-Fehler: {e}")
        if e.response is not None:
            print(f"   Status: {e.response.status_code}")
            print(f"   Antwort: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
