"""ZUGFeRD XML Generator (EN-16931 compliant)"""

from datetime import datetime
from lxml import etree
from lxml.builder import ElementMaker
from typing import List, Dict

from app.schemas import Seller, Buyer


class ZUGFeRDGenerator:
    """
    Generate ZUGFeRD XML according to EN-16931 standard
    
    ZUGFeRD (Zentraler User Guide des Forums elektronische Rechnung Deutschland)
    is the German implementation of EN-16931 for electronic invoicing.
    """
    
    # Namespaces for ZUGFeRD 2.2 / Factur-X
    NAMESPACES = {
        'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
        'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
        'qdt': 'urn:un:unece:uncefact:data:standard:QualifiedDataType:100',
        'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100',
    }
    
    def generate(
        self,
        invoice_number: str,
        issue_date: datetime,
        seller: Seller,
        buyer: Buyer,
        line_items: List[Dict],
        net_total: float,
        tax_total: float,
        gross_total: float,
        currency: str = "EUR",
        delivery_date_start: datetime = None,
        delivery_date_end: datetime = None,
        payment_terms: str = None,
    ) -> bytes:
        """
        Generate ZUGFeRD XML
        
        Returns XML as bytes (UTF-8 encoded)
        """
        
        # Create namespace map
        RSM = ElementMaker(namespace=self.NAMESPACES['rsm'], nsmap=self.NAMESPACES)
        RAM = ElementMaker(namespace=self.NAMESPACES['ram'])
        UDT = ElementMaker(namespace=self.NAMESPACES['udt'])
        
        # Root element
        root = RSM.CrossIndustryInvoice()
        
        # Exchange context
        context = RSM.ExchangedDocumentContext()
        context.append(RAM.GuidelineSpecifiedDocumentContextParameter(
            RAM.ID('urn:cen.eu:en16931:2017#compliant#urn:factur-x.eu:1p0:basic')
        ))
        root.append(context)
        
        # Document header
        header = RSM.ExchangedDocument()
        header.append(RAM.ID(invoice_number))
        header.append(RAM.TypeCode('380'))  # Commercial invoice
        header.append(RAM.IssueDateTime(
            UDT.DateTimeString(
                issue_date.strftime('%Y%m%d'),
                format='102'
            )
        ))
        root.append(header)
        
        # Transaction
        transaction = RSM.SupplyChainTradeTransaction()
        
        # Line items
        for item in line_items:
            line = RAM.IncludedSupplyChainTradeLineItem()
            
            line.append(RAM.AssociatedDocumentLineDocument(
                RAM.LineID(str(item['position']))
            ))
            
            line.append(RAM.SpecifiedTradeProduct(
                RAM.Name(item['description'])
            ))
            
            line_agreement = RAM.SpecifiedLineTradeAgreement()
            line_agreement.append(RAM.NetPriceProductTradePrice(
                RAM.ChargeAmount(f"{item['unit_price']:.2f}")
            ))
            line.append(line_agreement)
            
            line_delivery = RAM.SpecifiedLineTradeDelivery()
            line_delivery.append(RAM.BilledQuantity(
                str(item['quantity']),
                unitCode=item.get('unit', 'C62')  # C62 = piece
            ))
            line.append(line_delivery)
            
            line_settlement = RAM.SpecifiedLineTradeSettlement()
            
            line_settlement.append(RAM.ApplicableTradeTax(
                RAM.TypeCode('VAT'),
                RAM.CategoryCode('S'),  # Standard rate
                RAM.RateApplicablePercent(f"{item['tax_rate']:.2f}")
            ))
            
            line_settlement.append(RAM.SpecifiedTradeSettlementLineMonetarySummation(
                RAM.LineTotalAmount(f"{item['line_net']:.2f}")
            ))
            
            line.append(line_settlement)
            
            transaction.append(line)
        
        # Agreement
        agreement = RAM.ApplicableHeaderTradeAgreement()
        
        # Seller
        seller_party = RAM.SellerTradeParty()
        seller_party.append(RAM.Name(seller.name))
        seller_party.append(RAM.PostalTradeAddress(
            RAM.PostcodeCode(seller.zip),
            RAM.LineOne(seller.street),
            RAM.CityName(seller.city),
            RAM.CountryID(seller.country)
        ))
        seller_party.append(RAM.SpecifiedTaxRegistration(
            RAM.ID(seller.tax_id, schemeID='VA')
        ))
        agreement.append(seller_party)
        
        # Buyer
        buyer_party = RAM.BuyerTradeParty()
        buyer_party.append(RAM.Name(buyer.name))
        buyer_party.append(RAM.PostalTradeAddress(
            RAM.PostcodeCode(buyer.zip),
            RAM.LineOne(buyer.street),
            RAM.CityName(buyer.city),
            RAM.CountryID(buyer.country)
        ))
        if buyer.tax_id:
            buyer_party.append(RAM.SpecifiedTaxRegistration(
                RAM.ID(buyer.tax_id, schemeID='VA')
            ))
        agreement.append(buyer_party)
        
        transaction.append(agreement)
        
        # Delivery
        delivery = RAM.ApplicableHeaderTradeDelivery()
        if delivery_date_start or delivery_date_end:
            delivery_date = delivery_date_end or delivery_date_start
            delivery.append(RAM.ActualDeliverySupplyChainEvent(
                RAM.OccurrenceDateTime(
                    UDT.DateTimeString(
                        delivery_date.strftime('%Y%m%d'),
                        format='102'
                    )
                )
            ))
        transaction.append(delivery)
        
        # Settlement
        settlement = RAM.ApplicableHeaderTradeSettlement()
        settlement.append(RAM.InvoiceCurrencyCode(currency))
        
        # Tax totals
        tax_breakdown = RAM.ApplicableTradeTax()
        tax_breakdown.append(RAM.CalculatedAmount(f"{tax_total:.2f}"))
        tax_breakdown.append(RAM.TypeCode('VAT'))
        tax_breakdown.append(RAM.BasisAmount(f"{net_total:.2f}"))
        tax_breakdown.append(RAM.CategoryCode('S'))
        
        # Get tax rate from first item (simplified)
        if line_items:
            tax_rate = line_items[0]['tax_rate']
            tax_breakdown.append(RAM.RateApplicablePercent(f"{tax_rate:.2f}"))
        
        settlement.append(tax_breakdown)
        
        # Payment terms
        if payment_terms:
            settlement.append(RAM.SpecifiedTradePaymentTerms(
                RAM.Description(payment_terms)
            ))
        
        # Monetary summation
        summation = RAM.SpecifiedTradeSettlementHeaderMonetarySummation()
        summation.append(RAM.LineTotalAmount(f"{net_total:.2f}"))
        summation.append(RAM.TaxBasisTotalAmount(f"{net_total:.2f}"))
        summation.append(RAM.TaxTotalAmount(f"{tax_total:.2f}", currencyID=currency))
        summation.append(RAM.GrandTotalAmount(f"{gross_total:.2f}"))
        summation.append(RAM.DuePayableAmount(f"{gross_total:.2f}"))
        settlement.append(summation)
        
        transaction.append(settlement)
        
        root.append(transaction)
        
        # Generate XML bytes
        xml_bytes = etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        )
        
        return xml_bytes
    
    def validate(self, xml_bytes: bytes) -> bool:
        """
        Validate XML against ZUGFeRD/EN-16931 XSD schema
        
        Note: For MVP, basic validation. Full XSD validation requires schema files.
        """
        try:
            root = etree.fromstring(xml_bytes)
            
            # Basic checks
            if root.tag != '{urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100}CrossIndustryInvoice':
                return False
            
            # Check required elements exist
            required_paths = [
                './/ram:ID',
                './/ram:SellerTradeParty',
                './/ram:BuyerTradeParty',
                './/ram:GrandTotalAmount',
            ]
            
            for path in required_paths:
                if root.find(path, namespaces=self.NAMESPACES) is None:
                    return False
            
            return True
            
        except Exception as e:
            print(f"XML validation error: {e}")
            return False
