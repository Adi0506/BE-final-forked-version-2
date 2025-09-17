# backend/app/services/crypto_service.py
import os, json
from typing import Union
import base58
import nacl.public
import nacl.signing
import nacl.bindings
import nacl.exceptions
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class CryptoError(Exception):
    pass

class CryptoService:
    """ Hybrid: AES-GCM for file, SealedBox (X25519) wrapping using Ed25519 → X25519 conversion. """

    @staticmethod
    def generate_aes_key(length: int = 32) -> bytes:
        if length not in (16, 24, 32):
            raise CryptoError("AES key length must be 16, 24, or 32 bytes.")
        return os.urandom(length)

    def aes_encrypt(self, plaintext: bytes, key: bytes) -> dict:
        if not isinstance(plaintext, (bytes, bytearray)):
            raise CryptoError("plaintext must be bytes")
        if len(key) not in (16, 24, 32):
            raise CryptoError("AES key length invalid")
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        combined = aesgcm.encrypt(nonce, plaintext, associated_data=None)
        tag = combined[-16:]
        ciphertext = combined[:-16]
        return {"ciphertext": ciphertext, "nonce": nonce, "tag": tag}

    def aes_decrypt(self, ciphertext: bytes, key: bytes, nonce: bytes, tag: bytes) -> bytes:
        aesgcm = AESGCM(key)
        combined = ciphertext + tag
        return aesgcm.decrypt(nonce, combined, associated_data=None)

    # helpers
    @staticmethod
    def _ensure_bytes(key_in: Union[str, bytes]) -> bytes:
        if isinstance(key_in, str):
            # try base58
            try:
                return base58.b58decode(key_in)
            except Exception:
                try:
                    return bytes.fromhex(key_in)
                except Exception:
                    # if it looks like a path, caller should pass path directly to unwrap helper
                    raise CryptoError("Unsupported key string format; expected base58 or hex.")
        if isinstance(key_in, (bytes, bytearray)):
            return bytes(key_in)
        raise CryptoError("Unsupported key type")

    @staticmethod
    def ed25519_pub_to_x25519_pub(ed_pub: bytes) -> bytes:
        if len(ed_pub) != 32:
            raise CryptoError("Ed25519 public key must be 32 bytes")
        return nacl.bindings.crypto_sign_ed25519_pk_to_curve25519(ed_pub)

    @staticmethod
    def ed25519_priv_to_x25519_priv(ed_priv: bytes) -> bytes:
        if len(ed_priv) == 64:
            return nacl.bindings.crypto_sign_ed25519_sk_to_curve25519(ed_priv)
        if len(ed_priv) == 32:
            signing_key = nacl.signing.SigningKey(ed_priv)
            sk64 = signing_key._seed + signing_key.verify_key.encode()
            return nacl.bindings.crypto_sign_ed25519_sk_to_curve25519(sk64)
        raise CryptoError("Ed25519 private key must be 32 or 64 bytes")

    # Key wrap (SealedBox)
    def wrap_key_to_ed25519_pub(self, ed25519_pub: Union[str, bytes], aes_key: bytes) -> bytes:
        ed_pub_bytes = self._ensure_bytes(ed25519_pub)
        x_pub = self.ed25519_pub_to_x25519_pub(ed_pub_bytes)
        recipient_pk = nacl.public.PublicKey(x_pub)
        sealed = nacl.public.SealedBox(recipient_pk).encrypt(aes_key)
        return sealed

    def unwrap_key_with_ed25519_priv(self, ed25519_priv_input: Union[str, bytes], sealed_key: bytes) -> bytes:
        # If argument is path to a solana keypair (json list), load it
        if isinstance(ed25519_priv_input, str) and os.path.exists(os.path.expanduser(ed25519_priv_input)):
            with open(os.path.expanduser(ed25519_priv_input), "r") as f:
                arr = json.load(f)
            priv_bytes = bytes(arr[:64]) if len(arr) >= 64 else bytes(arr[:32])
        else:
            priv_bytes = self._ensure_bytes(ed25519_priv_input)
        x_priv = self.ed25519_priv_to_x25519_priv(priv_bytes)
        privkey_obj = nacl.public.PrivateKey(x_priv)
        try:
            key = nacl.public.SealedBox(privkey_obj).decrypt(sealed_key)
            return key
        except nacl.exceptions.CryptoError as e:
            raise CryptoError("Failed to unwrap sealed AES key") from e

    @staticmethod
    def verify_ed25519_signature(ed25519_pub: Union[str, bytes], message: bytes, signature: bytes) -> bool:
        pub_bytes = CryptoService._ensure_bytes(ed25519_pub)
        if len(pub_bytes) != 32:
            raise CryptoError("Ed25519 public key must be 32 bytes for verification")
        try:
            verify_key = nacl.signing.VerifyKey(pub_bytes)
            verify_key.verify(message, signature)
            return True
        except Exception as e:
            raise CryptoError("Signature verification failed") from e
