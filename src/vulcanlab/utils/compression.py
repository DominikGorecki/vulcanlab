"""
Compression utilities for markdown content storage.

Automatically compresses content >1MB to save database space.
Handles both string and byte inputs robustly.
"""
import gzip
import logging
from typing import Union

logger = logging.getLogger(__name__)

# Compression threshold: 1MB
COMPRESSION_THRESHOLD = 1024 * 1024


def compress_if_large(content: Union[str, bytes]) -> bytes:
    """
    Compress content if larger than threshold.

    Args:
        content: Markdown string or raw bytes

    Returns:
        Compressed bytes (if > threshold) or original bytes
    """
    if content is None:
        return b''

    # Standardize to bytes
    if isinstance(content, str):
        content_bytes = content.encode('utf-8')
    else:
        content_bytes = content

    if len(content_bytes) > COMPRESSION_THRESHOLD:
        compressed = gzip.compress(content_bytes)
        logger.debug(f"Compressed {len(content_bytes)} bytes to {len(compressed)} bytes")
        return compressed

    return content_bytes


def decompress_if_needed(data: Union[bytes, str]) -> str:
    """
    Decompress data if it was compressed, otherwise decode.

    Args:
        data: Bytes from database or string

    Returns:
        Decompressed markdown string
    """
    if data is None:
        return ''

    # If it's already a string, return it
    if isinstance(data, str):
        return data

    # Try to decompress; if it fails, assume it's uncompressed
    try:
        decompressed = gzip.decompress(data)
        logger.debug(f"Decompressed {len(data)} bytes to {len(decompressed)} bytes")
        return decompressed.decode('utf-8')
    except (gzip.BadGzipFile, OSError):
        # OSError can occur with truncated or invalid gzip data
        # Assume it's uncompressed utf-8 text
        return data.decode('utf-8')
