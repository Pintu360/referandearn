# utils/helpers.py
import base58
import re
from typing import Optional, List
from datetime import datetime, timedelta

def validate_solana_address(address: str) -> bool:
    """
    Validate if a string is a valid Solana address
    
    Solana addresses are base58 encoded strings of 32-44 characters
    """
    try:
        if not address or not isinstance(address, str):
            return False
        
        # Check length
        if len(address) not in [32, 43, 44]:
            return False
        
        # Try to decode from base58
        decoded = base58.b58decode(address)
        
        # Valid addresses decode to 32 bytes
        return len(decoded) == 32
        
    except Exception:
        return False

def format_address(address: str, chars: int = 8) -> str:
    """
    Format address for display (e.g., "ABC...XYZ")
    
    Args:
        address: Full address
        chars: Number of characters to show at start and end
    """
    if not address:
        return "Unknown"
    
    if len(address) <= chars * 2:
        return address
    
    return f"{address[:chars]}...{address[-chars:]}"

def format_number(num: float, decimals: int = 2) -> str:
    """
    Format large numbers with K, M, B suffixes
    
    Examples:
        1,234 -> 1.23K
        1,234,567 -> 1.23M
        1,234,567,890 -> 1.23B
    """
    if num is None:
        return "0"
    
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.{decimals}f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.{decimals}f}M"
    elif num >= 1_000:
        return f"{num/1_000:.{decimals}f}K"
    else:
        return f"{num:.{decimals}f}"

def format_usd(amount: float) -> str:
    """
    Format USD amount with appropriate suffix
    
    Examples:
        123 -> $123.00
        1,234 -> $1.23K
        1,234,567 -> $1.23M
    """
    if amount is None:
        return "$0"
    
    if amount >= 1_000_000_000:
        return f"${amount/1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"${amount/1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"${amount/1_000:.2f}K"
    else:
        return f"${amount:.2f}"

def format_timestamp(timestamp: datetime) -> str:
    """
    Format timestamp as relative time (e.g., "5 minutes ago")
    """
    if not timestamp:
        return "Unknown"
    
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=30):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return timestamp.strftime("%Y-%m-%d %H:%M")

def extract_addresses(text: str) -> List[str]:
    """
    Extract all Solana addresses from text
    
    Returns:
        List of unique addresses found
    """
    # Solana addresses are base58 strings of 32-44 characters
    pattern = r'[1-9A-HJ-NP-Za-km-z]{32,44}'
    matches = re.findall(pattern, text)
    
    # Validate each match
    valid_addresses = []
    for match in matches:
        if validate_solana_address(match):
            valid_addresses.append(match)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_addresses = []
    for addr in valid_addresses:
        if addr not in seen:
            seen.add(addr)
            unique_addresses.append(addr)
    
    return unique_addresses

def safe_float(value, default: float = 0.0) -> float:
    """
    Safely convert value to float
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    """
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum allowed length
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def is_contract_address(address: str) -> bool:
    """
    Check if an address is likely a contract/program
    
    Known program IDs on Solana:
    - Token Program: TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA
    - Associated Token Account: ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL
    - System Program: 11111111111111111111111111111111
    """
    known_programs = [
        "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # Token Program
        "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",  # Associated Token
        "11111111111111111111111111111111",  # System Program
        "Vote111111111111111111111111111111111111111",  # Vote Program
        "Stake11111111111111111111111111111111111111",  # Stake Program
        "ComputeBudget111111111111111111111111111111",  # Compute Budget
        "AddressLookupTab1e1111111111111111111111111",  # Address Lookup Table
    ]
    
    return address in known_programs

def calculate_percentage_change(old: float, new: float) -> float:
    """
    Calculate percentage change between two values
    
    Returns:
        Percentage change (e.g., 10.5 for 10.5% increase)
    """
    if old == 0:
        return 0.0
    
    return ((new - old) / old) * 100

def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram Markdown
    """
    if not text:
        return ""
    
    # Characters that need escaping in Telegram Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def chunk_text(text: str, max_length: int = 4000) -> List[str]:
    """
    Split long text into chunks for Telegram message limits
    
    Args:
        text: Text to split
        max_length: Maximum chunk length (Telegram limit is 4096)
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by lines to avoid breaking mid-line
    lines = text.split('\n')
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= max_length:
            if current_chunk:
                current_chunk += '\n' + line
            else:
                current_chunk = line
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def get_risk_level(risk_score: float) -> dict:
    """
    Get risk level and emoji based on score
    
    Args:
        risk_score: 0-100 risk score
    
    Returns:
        Dict with level, emoji, and description
    """
    if risk_score >= 80:
        return {
            'level': 'CRITICAL',
            'emoji': '🔴',
            'description': 'Extremely high risk - Likely scam'
        }
    elif risk_score >= 60:
        return {
            'level': 'HIGH',
            'emoji': '🟠',
            'description': 'High risk - Multiple red flags'
        }
    elif risk_score >= 30:
        return {
            'level': 'MEDIUM',
            'emoji': '🟡',
            'description': 'Medium risk - Exercise caution'
        }
    else:
        return {
            'level': 'LOW',
            'emoji': '🟢',
            'description': 'Low risk - Standard token'
        }