from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
from core.config import DATA_ENCRYPTION_KEY
import json
from core.config import os
from typing import Union, Dict

class SecurityService:
    def __init__(self):
        self.encryption_key = base64.b64decode(DATA_ENCRYPTION_KEY)
        self.aesgcm = AESGCM(self.encryption_key)

    def encrypt_field(
        self,
        plaintext: Union[str, Dict]
    ) -> str:
        """encrypt AES-GCM which has 12 bytes length for nonce, and remaind 12 bytes for ciphertext"""
        if isinstance(plaintext, Dict):
            plaintext = json.dumps(plaintext)

        nonce = os.urandom(12)
        ct =  self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ct).decode()

    def decrypt_field(self, ciphertext_b64: str) -> str | Dict:
        """descrypt AES-GCM which has 12 bytes length for nonce, and remaind 12 bytes for ciphertext"""
        data = base64.b64decode(ciphertext_b64)
        nonce, ct = data[:12], data[12:]
        pt =  self.aesgcm.decrypt(nonce, ct, None)
        try:
            return json.loads(pt.decode())
        except Exception:
            return pt.decode()