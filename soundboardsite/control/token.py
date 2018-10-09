import jwt
import os
import datetime
import logging
from django.http import HttpResponse
import json

logging.basicConfig(level=logging.DEBUG)

secret = os.environ.get('MILTON_SECRET_KEY')

def validate_from_iso(date):
    try:
        year = int(date[:4])
        month = int(date[5:7])
        day = int(date[8:10])
        hour = int(date[11:13])
        constructed_date = datetime.datetime(year, month, day, hour)
    except ValueError:
        raise ValueError("Ill-formatted datetime.")
    return datetime.datetime.now() < constructed_date

def tokenize(user):
    return jwt.encode({'user': user, 'expires': (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()},secret).decode("utf-8")

def validate_token(token):
    try:
        dec_jwt = jwt.decode(token.encode("utf-8"), secret)
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError("Token could not be decoded.")
    try:
        if not validate_from_iso(dec_jwt['expires']):
            raise jwt.InvalidTokenError("Token expired. Token expiration time: %s", (dec_jwt['expires']))
        return dec_jwt['user']
    except KeyError:
        raise jwt.InvalidTokenError("Invalid args.")


def token_from_header(token_str):
    if 'Bearer' in token_str:
        token_str = token_str.strip()
        return token_str.replace("Bearer ", "")

def token_required(view):
    def bad_token():
        return HttpResponse(content=json.dumps({"body": "Bad token"}), content_type='application/json', status=400)
    def wrapper(request): #look at decorator bookmark and kwargs docs to remember thought process
        try:
            username = validate_token(token_from_header(request.META['HTTP_AUTHORIZATION']))
        except (KeyError, jwt.InvalidTokenError):
            return bad_token()
        return view(request, username=username)
    return wrapper