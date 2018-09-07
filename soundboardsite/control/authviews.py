from django.http import HttpResponse
from .models import *
import requests
import os
import json
from . import token
from passlib.hash import pbkdf2_sha256
from django.core.exceptions import ValidationError

def create_user(request):
    if request.method == 'POST' and 'user' in request.POST:
        err_dict_no_pass = {"body": "No password provided."}
        ok_dict = {"body": "User successfully created."}

        user = request.POST['user']
        try:
            password = request.POST['password']
        except KeyError:
            return HttpResponse(content=json.dumps(err_dict_no_pass),content_type='application/json', status=400)
        p_hash = pbkdf2_sha256.hash(password)

        try:
            u = AppUser(user=user,password_hash=p_hash)
            u.save()
            return HttpResponse(content=json.dumps(ok_dict), content_type='application/json')
        except ValidationError:
            err_dict = {"body": "Bad data types. Make sure 'user' and 'password' fields are strings."}
            return HttpResponse(content=json.dumps(err_dict), content_type='application/json',status=400)

def login(request):
    if request.method == 'POST':
        err_dict_no_uandp = {"body": "Must provide username and password."}
        err_dict_bad_cred = {"body": "Incorrect username or password."}

        try:
            user = request.POST['user']
            password = request.POST['password']
        except KeyError:
            return HttpResponse(content=json.dumps(err_dict_no_uandp),content_type='application/json',status=400)

        if not AppUser.objects.filter(user=user).exists():
            return HttpResponse(content=json.dumps(err_dict_bad_cred),content_type='application/json', status=400)
        elif pbkdf2_sha256.verify(password, AppUser.objects.filter(user=user).password_hash):
            user_token = token.tokenize(user=user)
            ok_dict = {"token": user_token, "body": "Successful login."}
            return HttpResponse(content=json.dumps(ok_dict),content_type='application/json')
        else:
            return HttpResponse(content=json.dumps(err_dict_bad_cred),content_type='application/json',status=400)

def auth(request):
    return

def authcode(request):
    if request.method == 'GET' and 'state' in request.GET:
        u_to_check = request.GET['state']
        if AppUser.objects.filter(user=u_to_check).exists() and 'code' in request.GET:
            code = request.GET['code']
            client_id = os.environ.get('DISCORD_CLIENT_ID')
            client_secret = os.environ.get('DISCORD_CLIENT_SECRET')
            redirect_uri = 'https://digest-soundboard.herokuapp.com/auth/'
            api_endpoint = 'https://discordapp.com/api/oauth2/token'

            data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            r = requests.post(api_endpoint,data,headers)
            r.raise_for_status()
            result = r.json()

            u = AppUser.objects.get(user=u_to_check)
            u.token = result["access_token"]
            u.refresh_token = result["refresh_token"]
            u.save()