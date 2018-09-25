from .models import *
import requests
import os
import json
from . import token
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

logging.basicConfig(level=logging.DEBUG)


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
            app_token = request.POST['token']
        except KeyError:
            return HttpResponse("No token", status=400)
        return HttpResponse(token.validate_token(app_token))

def authcode(request):
    if request.method == 'GET' and 'state' in request.GET:
        logging.info('request being handled')
        u_to_check = request.GET['state']
        if AppUser.objects.filter(user=u_to_check).exists() and 'code' in request.GET:
            logging.info('token request in progress')
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
            logging.info('token retrieved')

            u = AppUser.objects.get(user=u_to_check)
            u.token = result["access_token"]
            u.refresh_token = result["refresh_token"]
            u.save()
            logging.info('tokens saved')