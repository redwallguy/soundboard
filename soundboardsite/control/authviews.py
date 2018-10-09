from .models import *
import requests
import os
import json
from . import token
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from jwt import InvalidTokenError

logging.basicConfig(level=logging.DEBUG)

#TODO convert HttpResponses to JSONResponses (django.http -> JSONResponse)


def create_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('boards')
    else:
        form = UserCreationForm()
    return render(request, 'control/registration/new_user.html', {'form': form})

@csrf_exempt
def app_login(request):
    if request.method == 'POST':
        err_dict_args = {"body": "Username and password must be provided."}
        err_dict_creds = {"body": "Invalid credentials."}
        try:
            username = request.POST['user']
            password = request.POST['password']
        except KeyError:
            return HttpResponse(content=json.dumps(err_dict_args), content_type='application/json', status=400)
        user = authenticate(username=username,password=password)
        if user is not None:
            app_token = token.tokenize(user.username)
            ok_dict = {"body": "Login successful", "token": app_token}
            return HttpResponse(content=json.dumps(ok_dict),content_type='application/json')
        else:
            return HttpResponse(content=json.dumps(err_dict_creds), content_type='application/json', status=400)

@csrf_exempt
def test_token(request):
    if request.method == 'POST':
        try:
            username = token.validate_token(token.token_from_header(request.META['HTTP_AUTHORIZATION']))
        except (KeyError, InvalidTokenError) as e:
            logging.debug(e)
            return HttpResponse(content=json.dumps({"body": "Bad token"}), content_type='application/json', status=400)
        return HttpResponse(content=json.dumps({"user": username}), content_type='application/json')

@login_required
def discord_view(request):
    return render(request, 'control/discord.html')

def authcode(request):
    if request.method == 'GET' and 'state' in request.GET:
        logging.info('request being handled')
        try:
            user = User.objects.get(username=request.GET['state'])
            logging.info('token request in progress')
            code = request.GET['code']
            client_id = os.environ.get('DISCORD_CLIENT_ID')
            client_secret = os.environ.get('DISCORD_CLIENT_SECRET')
            redirect_uri = os.environ.get('REDIRECT_URI')
            api_endpoint = 'https://discordapp.com/api/oauth2/token'

            data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
                'scope': 'identify'
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            r = requests.post(api_endpoint,data,headers)
            r.raise_for_status()
            result = r.json()
            logging.info('token retrieved')

            if AppUser.objects.filter(user=user).exists():
                u = AppUser.objects.get(user=user)
                u.token = result["access_token"]
                u.refresh_token = result["refresh_token"]
                u.save()
                logging.info('tokens saved in existing AppUser')
            else:
                u = AppUser(user=user, token=result['access_token'], refresh_token=result['refresh_token'])
                u.save()
                logging.info("Tokens saved in new AppUser")
            return HttpResponse("Nice job.")
        except (KeyError, User.DoesNotExist) as e:
            logging.debug("User does not exist.")
    else:
        logging.info(request.GET)
