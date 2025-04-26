import re

def validate_username(u):
    return bool(re.match(r"^[A-Za-z0-9]{8,}$",u))

def validate_password(p):
    return bool(re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\\W).{8,}$",p))