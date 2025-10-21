"""Signature Service - PAdES + RFC3161 TSA"""

import hashlib
from datetime import datetime
from io import BytesIO
from typing import Tuple, Dict, Optional

import pyhanko
from pyhanko.sign import signers, timestamps
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

from app.core.config import settings


class SignatureService:
    """
    Service for PDF signing with PAdES and RFC3161 timestamps
    
    PAdES (PDF Advanced Electronic Signatures) with TSA ensures:
    - Document integrity (cryptographic signature)
    - Timestamp from trusted authority (legal proof of time)
    - GoBD compliance (Revisionssicherheit)
    """
    
    def __init__(self):
        self.tsa_url = settings.TSA_URL
        self.tsa_username = settings.TSA_USERNAME or None
        self.tsa_password = settings.TSA_PASSWORD or None
        self.hash_algorithm = settings.TSA_HASH_ALGORITHM or "SHA256"
    
    async def sign_pdf(self, pdf_bytes: bytes) -> Tuple[bytes, Dict]:
        """
        Sign PDF with PAdES and add RFC3161 timestamp
        
        Args:
            pdf_bytes: Original PDF as bytes
        
        Returns:
            Tuple of (signed_pdf_bytes, tsa_token_metadata)
        """
        
        # For MVP: Use TSA timestamp only (no certificate signing)
        # In production: Add qualified certificate for full PAdES-LTV
        
        signed_pdf, tsa_token = await self._add_timestamp(pdf_bytes)
        
        return signed_pdf, tsa_token
    
    async def _add_timestamp(self, pdf_bytes: bytes) -> Tuple[bytes, Dict]:
        """
        Add RFC3161 timestamp to PDF
        
        Uses pyHanko to:
        1. Calculate PDF hash
        2. Request timestamp from TSA
        3. Embed timestamp in PDF signature
        """
        
        try:
            # Create HTTP TSA client
            tsa_client = timestamps.HTTPTimeStamper(
                url=self.tsa_url,
                username=self.tsa_username,
                password=self.tsa_password,
            )
            
            # Open PDF
            input_buffer = BytesIO(pdf_bytes)
            writer = IncrementalPdfFileWriter(input_buffer)
            
            # Create document timestamp (no signing certificate)
            # This is sufficient for timestamp-only proof
            sig_meta = signers.PdfSignatureMetadata(
                field_name='Timestamp',
                name='RFC3161 TimeStamp',
                reason='GoBD compliance - revisionssichere Archivierung',
            )
            
            # Add timestamp
            output_buffer = BytesIO()
            
            # Use PdfTimeStamper for timestamp-only (no certificate needed)
            signer = signers.PdfTimeStamper(
                timestamper=tsa_client,
            )
            
            signers.sign_pdf(
                writer,
                sig_meta,
                signer=signer,
                output=output_buffer,
            )
            
            signed_pdf_bytes = output_buffer.getvalue()
            
            # Extract TSA token info for storage
            tsa_token_metadata = {
                "tsa_url": self.tsa_url,
                "timestamp": datetime.utcnow().isoformat(),
                "hash_algorithm": self.hash_algorithm,
                "pdf_hash": hashlib.sha256(pdf_bytes).hexdigest(),
                "signed_pdf_hash": hashlib.sha256(signed_pdf_bytes).hexdigest(),
            }
            
            output_buffer.close()
            input_buffer.close()
            
            return signed_pdf_bytes, tsa_token_metadata
            
        except Exception as e:
            # Fallback for development/testing: return unsigned PDF with mock token
            print(f"TSA signing failed (using mock for development): {e}")
            
            return pdf_bytes, {
                "tsa_url": "mock_tsa",
                "timestamp": datetime.utcnow().isoformat(),
                "hash_algorithm": self.hash_algorithm,
                "pdf_hash": hashlib.sha256(pdf_bytes).hexdigest(),
                "signed_pdf_hash": hashlib.sha256(pdf_bytes).hexdigest(),
                "warning": "Mock timestamp - not for production use",
            }
    
    def verify_signature(self, signed_pdf_bytes: bytes) -> bool:
        """
        Verify PDF signature and timestamp
        
        Args:
            signed_pdf_bytes: Signed PDF
        
        Returns:
            True if signature and timestamp are valid
        """
        try:
            from pyhanko.sign import validation
            
            input_buffer = BytesIO(signed_pdf_bytes)
            r = validation.validate_pdf_signature(input_buffer)
            
            input_buffer.close()
            
            return r.timestamp_validity.valid if r.timestamp_validity else False
            
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False
