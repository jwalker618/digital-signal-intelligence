#Utility functions for website discovery

import re
import socket
from typing import List, Optional
from urllib.parse import urlparse


def normalize_company_name(company_name: str) -> str:
    '''
    Normalise company name for domain generation.

    Args:
        company_name: Raw company name

    Returns:
        Normalised name suitable for domain generation
    '''
    # Convert to lowercase
    name = company_name.lower()

    # Remove common suffixes
    suffixes = [
        r'\s+plc$',
        r'\s+ltd$',
        r'\s+limited$',
        r'\s+inc$',
        r'\s+corp$',
        r'\s+corporation$',
        r'\s+llc$',
        r'\s+&\s+co$',
        r'\s+and\s+co$',
    ]
    for suffix in suffixes:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE)

    # Remove special characters except spaces and hyphens
    name = re.sub(r'[^a-z0-9\s\-]', '', name)

    # Replace spaces and multiple hyphens with single hyphen
    name = re.sub(r'[\s\-]+', '-', name)

    # Remove leading/trailing hyphens
    name = name.strip('-')

    return name


def generate_domain_variations(company_name: str) -> List[str]:
    '''
    Generate potential domain name variations from company name.

    Args:
        company_name: Company name

    Returns:
        List of potential domain names
    '''
    normalized = normalize_company_name(company_name)
    variations = []

    # Basic variations
    variations.append(f'{normalized}.com')
    variations.append(f'{normalized}.co.uk')

    # Without hyphens
    no_hyphen = normalized.replace('-', '')
    if no_hyphen != normalized:
        variations.append(f'{no_hyphen}.com')
        variations.append(f'{no_hyphen}.co.uk')

    # Common corporate subdomains
    for base in [normalized, no_hyphen]:
        variations.extend(
            [
                f'corporate.{base}.com',
                f'www.corporate.{base}.com',
                f'investor.{base}.com',
                f'investors.{base}.com',
                f'group.{base}.com',
                f'about.{base}.com',
            ]
        )

    # Remove duplicates while preserving order
    seen = set()
    unique_variations = []
    for var in variations:
        if var not in seen:
            seen.add(var)
            unique_variations.append(var)

    return unique_variations


def is_valid_url(url: str) -> bool:
    '''
    Check if URL is valid and well-formed.

    Args:
        url: URL to validate

    Returns:
        True if valid, False otherwise
    '''
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_domain(url: str) -> Optional[str]:
    '''
    Extract domain from URL.

    Args:
        url: URL to extract domain from

    Returns:
        Domain name or None if invalid
    '''
    try:
        parsed = urlparse(url)
        return parsed.netloc or parsed.path.split('/')[0]
    except Exception:
        return None


def check_dns_exists(domain: str) -> bool:
    '''
    Check if domain has DNS records.

    Args:
        domain: Domain name to check

    Returns:
        True if DNS records exist, False otherwise
    '''
    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False


def sanitize_url(url: str) -> str:
    '''
    Ensure URL has proper scheme.

    Args:
        url: URL to sanitize

    Returns:
        URL with proper scheme
    '''
    if not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url


def extract_company_keywords(company_name: str) -> List[str]:
    '''
    Extract keywords from company name for searching.

    Args:
        company_name: Company name

    Returns:
        List of keywords
    '''
    # Remove common business suffixes
    cleaned = re.sub(
        r'\b(plc|ltd|limited|inc|corp|corporation|llc)\b',
        '',
        company_name,
        flags=re.IGNORECASE,
    )

    # Split into words and filter
    words = cleaned.split()
    keywords = [w for w in words if len(w) > 2]  # Filter very short words

    return keywords
