from typing import Tuple
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Cipher._mode_ecb import EcbMode
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64

BLOCK_SIZE = 16
KEY_SIZE = 16
RSA_SIZE = 2048

def generate_session_key() -> str:
    return encode_base64(get_random_bytes(16))

def generate_aes_cipher(key: str) -> EcbMode:
    decoded_key = decode_base64(key)
    cipher = AES.new(decoded_key, AES.MODE_ECB)
    return cipher

def generate_rsa_key() -> Tuple[str, str]:
    rsa_key = RSA.generate(RSA_SIZE)
    private_key = rsa_key.export_key().decode()
    public_key = rsa_key.public_key().export_key().decode()
    return private_key, public_key

def generate_rsa_cipher(key: bytes) -> PKCS1_OAEP.PKCS1OAEP_Cipher:
    """Generate cipher object for encryption and decryption

    Must provide either public key or private key

    If private_key is provided then resulting cipher object will be able to be used for decrypting
    """
    return PKCS1_OAEP.new(key)

def encrypt_with_aes(sk: str, message: str) -> str:
    cipher = generate_aes_cipher(sk)
    encrypted_message = cipher.encrypt(pad(message.encode(), BLOCK_SIZE))
    return encode_base64(encrypted_message)

def decrypt_with_aes(sk: str, encoded_message: str) -> str:
    message = decode_base64(encoded_message)
    cipher = generate_aes_cipher(sk)
    decrypted_message = unpad(cipher.decrypt(message), 16)
    return decrypted_message.decode()

def encrypt_with_rsa(input_key: str, message: str) -> str:
    """
    Key can be either private key or public key
    """
    key = RSA.import_key(input_key.encode())
    cipher = generate_rsa_cipher(key)
    ciphertext = cipher.encrypt(message.encode())
    return encode_base64(ciphertext)

def decrypt_with_rsa(private_key: str, message: str) -> str:
    "Key must be private"
    key = RSA.import_key(private_key.encode())
    cipher = generate_rsa_cipher(key)
    ciphertext = decode_base64(message)
    decrypted_text = cipher.decrypt(ciphertext).decode()
    return decrypted_text


def encode_base64(data) -> str:
    return base64.b64encode(data).decode()

def decode_base64(data) -> str:
    return base64.b64decode(data)