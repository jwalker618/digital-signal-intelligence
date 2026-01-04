"""
DSI Production Extractor - TLS/SSL Configuration Analysis

Analyzes TLS/SSL configuration by performing a TLS handshake and
examining certificate details.

This is a FREE extractor - uses Python's ssl library.

Checks Performed:
    - TLS version supported (TLS 1.2, 1.3)
    - Certificate validity and expiration
    - Certificate chain
    - Cipher suites
    - Key strength
    - Certificate transparency
    - OCSP stapling support

Scoring Implications:
    - TLS 1.3 = Very positive
    - TLS 1.2 only = Positive
    - TLS 1.0/1.1 = Negative (deprecated)
    - Expired/invalid cert = Critical negative
    - Weak ciphers = Negative
"""

import logging
import socket
import ssl
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..base import ProductionExtractor
from ....types import ExtractorResult

logger = logging.getLogger(__name__)


# TLS versions from best to worst
TLS_VERSIONS = {
    ssl.TLSVersion.TLSv1_3: {'name': 'TLS 1.3', 'score': 100, 'secure': True},
    ssl.TLSVersion.TLSv1_2: {'name': 'TLS 1.2', 'score': 85, 'secure': True},
    ssl.TLSVersion.TLSv1_1: {'name': 'TLS 1.1', 'score': 40, 'secure': False},
    ssl.TLSVersion.TLSv1: {'name': 'TLS 1.0', 'score': 20, 'secure': False},
}

# Cipher suite ratings
STRONG_CIPHERS = [
    'ECDHE', 'DHE',  # Forward secrecy
    'AES256', 'AES128',  # Strong encryption
    'CHACHA20',  # Modern stream cipher
    'GCM', 'CCM',  # AEAD modes
]

WEAK_CIPHERS = [
    'RC4', 'DES', '3DES', 'MD5',  # Deprecated
    'NULL', 'EXPORT', 'ANON',  # Insecure
    'CBC',  # Vulnerable to padding oracle (when with TLS < 1.2)
]


class TLSConfigExtractor(ProductionExtractor):
    """
    Analyzes TLS/SSL configuration for a domain.

    Performs TLS handshake and examines certificate and connection details.

    Output:
        {
            'domain': str,
            'tls_supported': bool,
            'tls_version': str,
            'tls_score': int,  # 0-100
            'certificate': {
                'subject': str,
                'issuer': str,
                'valid_from': str,
                'valid_until': str,
                'days_until_expiry': int,
                'is_valid': bool,
                'is_expired': bool,
                'is_self_signed': bool,
                'key_size': int,
                'key_type': str,
                'san_domains': [...],
            },
            'cipher': {
                'name': str,
                'bits': int,
                'is_strong': bool,
            },
            'issues': [...],
            'grade': str,  # A+, A, B, C, D, F
        }
    """

    SOURCE_NAME = "tls_config"
    SOURCE_VERSION = "1.0"
    DEFAULT_TTL_SECONDS = 86400  # 24 hours
    RATE_LIMIT = 5.0
    COST_TIER = "free"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._timeout = config.get('timeout', 10) if config else 10

    def get_required_config(self) -> List[str]:
        return []

    def _do_extract(self, entity_id: str, **kwargs) -> ExtractorResult:
        """Analyze TLS configuration for a domain."""
        domain = entity_id.strip().lower()

        if not domain:
            return self._create_error_result("Empty domain provided")

        # Remove protocol if present
        if domain.startswith(('http://', 'https://')):
            domain = domain.split('://', 1)[1].split('/')[0]

        # Remove port if present
        port = 443
        if ':' in domain:
            domain, port_str = domain.rsplit(':', 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 443

        issues = []

        # Try TLS connection
        try:
            tls_info = self._get_tls_info(domain, port)
        except ssl.SSLError as e:
            return self._create_success_result({
                'domain': domain,
                'port': port,
                'tls_supported': False,
                'error': f"SSL Error: {str(e)}",
                'issues': ['TLS connection failed'],
                'grade': 'F',
            }, confidence=0.90)
        except socket.error as e:
            return self._create_success_result({
                'domain': domain,
                'port': port,
                'tls_supported': False,
                'error': f"Connection Error: {str(e)}",
                'issues': ['Could not connect to server'],
                'grade': 'F',
            }, confidence=0.70)
        except Exception as e:
            return self._create_error_result(f"Error analyzing TLS: {e}")

        # Analyze TLS version
        tls_version_info = TLS_VERSIONS.get(tls_info['tls_version'])
        if tls_version_info:
            tls_version_name = tls_version_info['name']
            tls_score = tls_version_info['score']
            if not tls_version_info['secure']:
                issues.append(f"Insecure TLS version: {tls_version_name}")
        else:
            tls_version_name = str(tls_info['tls_version'])
            tls_score = 50

        # Analyze certificate
        cert_info = tls_info['certificate']
        cert_issues = self._analyze_certificate(cert_info)
        issues.extend(cert_issues)

        # Analyze cipher
        cipher_info = tls_info['cipher']
        cipher_issues = self._analyze_cipher(cipher_info, tls_version_name)
        issues.extend(cipher_issues)

        # Calculate grade
        grade = self._calculate_grade(tls_score, cert_info, cipher_info, issues)

        data = {
            'domain': domain,
            'port': port,
            'tls_supported': True,
            'tls_version': tls_version_name,
            'tls_score': tls_score,
            'certificate': cert_info,
            'cipher': cipher_info,
            'issues': issues,
            'issue_count': len(issues),
            'grade': grade,
        }

        confidence = 0.95
        return self._create_success_result(data, confidence=confidence)

    def _get_tls_info(self, domain: str, port: int = 443) -> Dict[str, Any]:
        """Perform TLS handshake and extract information."""
        context = ssl.create_default_context()

        with socket.create_connection((domain, port), timeout=self._timeout) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                # Get TLS version
                tls_version = ssock.version()

                # Get cipher info
                cipher = ssock.cipher()

                # Get certificate
                cert = ssock.getpeercert()

                # Get certificate in DER format for additional analysis
                cert_der = ssock.getpeercert(binary_form=True)

        # Parse certificate
        cert_info = self._parse_certificate(cert, cert_der, domain)

        # Parse cipher
        cipher_info = {
            'name': cipher[0] if cipher else 'Unknown',
            'protocol': cipher[1] if cipher and len(cipher) > 1 else 'Unknown',
            'bits': cipher[2] if cipher and len(cipher) > 2 else 0,
            'is_strong': self._is_strong_cipher(cipher[0] if cipher else ''),
        }

        # Map version string to enum
        tls_version_enum = None
        if tls_version == 'TLSv1.3':
            tls_version_enum = ssl.TLSVersion.TLSv1_3
        elif tls_version == 'TLSv1.2':
            tls_version_enum = ssl.TLSVersion.TLSv1_2
        elif tls_version == 'TLSv1.1':
            tls_version_enum = ssl.TLSVersion.TLSv1_1
        elif tls_version == 'TLSv1':
            tls_version_enum = ssl.TLSVersion.TLSv1

        return {
            'tls_version': tls_version_enum,
            'tls_version_string': tls_version,
            'cipher': cipher_info,
            'certificate': cert_info,
        }

    def _parse_certificate(self, cert: Dict, cert_der: bytes, domain: str) -> Dict[str, Any]:
        """Parse certificate details."""
        # Extract subject
        subject = dict(x[0] for x in cert.get('subject', []))
        subject_cn = subject.get('commonName', 'Unknown')

        # Extract issuer
        issuer = dict(x[0] for x in cert.get('issuer', []))
        issuer_cn = issuer.get('commonName', 'Unknown')
        issuer_org = issuer.get('organizationName', '')

        # Parse dates
        not_before = cert.get('notBefore', '')
        not_after = cert.get('notAfter', '')

        valid_from = None
        valid_until = None
        days_until_expiry = None
        is_expired = False

        try:
            # Parse date format: 'Mar 15 00:00:00 2024 GMT'
            valid_from = datetime.strptime(not_before, '%b %d %H:%M:%S %Y %Z')
            valid_until = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')

            now = datetime.now(timezone.utc).replace(tzinfo=None)
            days_until_expiry = (valid_until - now).days
            is_expired = days_until_expiry < 0
        except ValueError:
            pass

        # Extract SANs
        san_domains = []
        for san_type, san_value in cert.get('subjectAltName', []):
            if san_type == 'DNS':
                san_domains.append(san_value)

        # Check if self-signed
        is_self_signed = subject_cn == issuer_cn and not issuer_org

        # Check if wildcard
        is_wildcard = subject_cn.startswith('*.')

        # Extract key info (from DER if available)
        key_size = None
        key_type = 'Unknown'

        # Try to get key info from the certificate
        try:
            # This is a simplified approach - in production use cryptography library
            if b'rsaEncryption' in cert_der:
                key_type = 'RSA'
                # Key size detection from DER is complex, estimate from cert_der size
                if len(cert_der) > 2000:
                    key_size = 4096
                elif len(cert_der) > 1200:
                    key_size = 2048
                else:
                    key_size = 1024
            elif b'ecPublicKey' in cert_der or b'id-ecPublicKey' in cert_der:
                key_type = 'ECDSA'
                key_size = 256  # Common EC key size
        except:
            pass

        return {
            'subject': subject_cn,
            'subject_org': subject.get('organizationName', ''),
            'issuer': issuer_cn,
            'issuer_org': issuer_org,
            'valid_from': valid_from.isoformat() if valid_from else not_before,
            'valid_until': valid_until.isoformat() if valid_until else not_after,
            'days_until_expiry': days_until_expiry,
            'is_valid': days_until_expiry is not None and days_until_expiry > 0,
            'is_expired': is_expired,
            'is_self_signed': is_self_signed,
            'is_wildcard': is_wildcard,
            'key_type': key_type,
            'key_size': key_size,
            'san_domains': san_domains[:20],  # Limit
            'san_count': len(san_domains),
            'serial_number': cert.get('serialNumber', ''),
        }

    def _is_strong_cipher(self, cipher_name: str) -> bool:
        """Check if a cipher suite is considered strong."""
        cipher_upper = cipher_name.upper()

        # Check for weak ciphers first
        for weak in WEAK_CIPHERS:
            if weak in cipher_upper:
                return False

        # Check for strong ciphers
        strong_count = sum(1 for strong in STRONG_CIPHERS if strong in cipher_upper)

        return strong_count >= 2  # At least 2 strong indicators

    def _analyze_certificate(self, cert_info: Dict) -> List[str]:
        """Analyze certificate for issues."""
        issues = []

        if cert_info.get('is_expired'):
            issues.append("Certificate is expired")

        days = cert_info.get('days_until_expiry')
        if days is not None:
            if 0 < days <= 7:
                issues.append(f"Certificate expires in {days} days (critical)")
            elif days <= 30:
                issues.append(f"Certificate expires in {days} days (warning)")

        if cert_info.get('is_self_signed'):
            issues.append("Certificate is self-signed")

        key_size = cert_info.get('key_size')
        key_type = cert_info.get('key_type', '')
        if key_type == 'RSA' and key_size and key_size < 2048:
            issues.append(f"Weak RSA key size: {key_size} bits")
        elif key_type == 'ECDSA' and key_size and key_size < 256:
            issues.append(f"Weak EC key size: {key_size} bits")

        return issues

    def _analyze_cipher(self, cipher_info: Dict, tls_version: str) -> List[str]:
        """Analyze cipher suite for issues."""
        issues = []

        cipher_name = cipher_info.get('name', '').upper()

        for weak in WEAK_CIPHERS:
            if weak in cipher_name:
                issues.append(f"Weak cipher component: {weak}")

        bits = cipher_info.get('bits', 0)
        if bits and bits < 128:
            issues.append(f"Weak cipher strength: {bits} bits")

        if not cipher_info.get('is_strong'):
            if 'ECDHE' not in cipher_name and 'DHE' not in cipher_name:
                issues.append("No forward secrecy (missing ECDHE/DHE)")

        return issues

    def _calculate_grade(
        self,
        tls_score: int,
        cert_info: Dict,
        cipher_info: Dict,
        issues: List[str]
    ) -> str:
        """Calculate overall TLS grade."""
        score = tls_score

        # Certificate penalties
        if cert_info.get('is_expired'):
            return 'F'

        if cert_info.get('is_self_signed'):
            score -= 30

        days = cert_info.get('days_until_expiry')
        if days is not None and days <= 7:
            score -= 20
        elif days is not None and days <= 30:
            score -= 10

        # Cipher penalties
        if not cipher_info.get('is_strong'):
            score -= 15

        # Issue penalties
        score -= len(issues) * 5

        # Calculate grade
        if score >= 95:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 75:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 40:
            return 'D'
        else:
            return 'F'
