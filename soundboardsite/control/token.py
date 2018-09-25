import jwt
import os

secret = os.environ.get('MILTON_SECRET_KEY')

def tokenize(user):
    return jwt.encode({'user': user},secret).decode("utf-8")

def validate_token(token):
    try:
        dec_jwt = jwt.decode(token.encode("utf-8"), secret)
        if 'user' in dec_jwt:
            return dec_jwt['user']
        else:
            raise ValueError("User not specified in token.")
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError("Token could not be decoded.")

def token_from_header(token_str):
    if 'Bearer' in token_str:
        token_str = token_str.strip()
        return token_str.replace("Bearer ", "")
