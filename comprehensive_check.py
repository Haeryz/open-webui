#!/usr/bin/env python3
"""
Check what system prompt is actually being used by the application
"""
import sys
import os

# Change to backend directory to import modules
sys.path.insert(0, '/app/backend')
os.chdir('/app/backend')

print("Checking system prompt configuration...")
print("=" * 80)

# Check environment variable
print("\n1. ENABLE_PERSISTENT_CONFIG environment variable:")
print(f"   {os.environ.get('ENABLE_PERSISTENT_CONFIG', 'True')}")

print("\n2. DEFAULT_SYSTEM_PROMPT environment variable:")
env_prompt = os.environ.get('DEFAULT_SYSTEM_PROMPT', 'NOT SET')
if env_prompt != 'NOT SET':
    print(f"   {env_prompt[:100]}...")
else:
    print(f"   {env_prompt}")

# Now import and check the config
try:
    from open_webui.config import (
        DEFAULT_LEGAL_SYSTEM_PROMPT, 
        DEFAULT_SYSTEM_PROMPT,
        ENABLE_PERSISTENT_CONFIG
    )
    
    print("\n3. ENABLE_PERSISTENT_CONFIG from config module:")
    print(f"   {ENABLE_PERSISTENT_CONFIG}")
    
    print("\n4. DEFAULT_LEGAL_SYSTEM_PROMPT (hardcoded in config.py):")
    print(f"   First 200 chars: {DEFAULT_LEGAL_SYSTEM_PROMPT[:200]}")
    
    print("\n5. DEFAULT_SYSTEM_PROMPT.value (actual runtime value):")
    print(f"   First 200 chars: {DEFAULT_SYSTEM_PROMPT.value[:200]}")
    
    print("\n6. Comparison:")
    if DEFAULT_SYSTEM_PROMPT.value == DEFAULT_LEGAL_SYSTEM_PROMPT:
        print("   ✓ DEFAULT_SYSTEM_PROMPT.value MATCHES DEFAULT_LEGAL_SYSTEM_PROMPT")
        print("   The new prompt IS being used!")
    else:
        print("   ✗ DEFAULT_SYSTEM_PROMPT.value DOES NOT MATCH DEFAULT_LEGAL_SYSTEM_PROMPT")
        print("   Something is overriding the default...")
        
    # Check if it's the old prompt
    old_prompt_start = "Anda adalah ahli hukum yang bertugas mengekstrak"
    if DEFAULT_SYSTEM_PROMPT.value.startswith(old_prompt_start):
        print("   ✗ This appears to be the OLD prompt!")
    
    new_prompt_start = "# Sistem Ekstraksi Petunjuk/Barang"
    if DEFAULT_SYSTEM_PROMPT.value.startswith(new_prompt_start):
        print("   ✓ This appears to be the NEW prompt!")
        
except Exception as e:
    print(f"\nError importing config: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
