from cryptography.fernet import Fernet

# Store key locally in file
KEY_PATH = "secret.key"

def load_key():
    try:
        return open(KEY_PATH, "rb").read()
    except FileNotFoundError:
        key = Fernet.generate_key()
        with open(KEY_PATH, "wb") as f:
            f.write(key)
        return key

fernet = Fernet(load_key())

def encrypt(data: bytes) -> bytes:
    return fernet.encrypt(data)

def decrypt(token: bytes) -> bytes:
    return fernet.decrypt(token)