#!/usr/bin/env python3
import os
import sys

# Set environment before importing config
os.environ.setdefault('DATA_DIR', '/app/backend/data')

try:
    from open_webui.config import DEFAULT_SYSTEM_PROMPT, DEFAULT_LEGAL_SYSTEM_PROMPT
    
    print("=" * 80)
    print("DEFAULT_LEGAL_SYSTEM_PROMPT (first 200 chars):")
    print(DEFAULT_LEGAL_SYSTEM_PROMPT[:200])
    print("\n" + "=" * 80)
    print("DEFAULT_SYSTEM_PROMPT.value (first 200 chars):")
    print(DEFAULT_SYSTEM_PROMPT.value[:200])
    print("\n" + "=" * 80)
    print("Are they the same?", DEFAULT_SYSTEM_PROMPT.value == DEFAULT_LEGAL_SYSTEM_PROMPT)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
