from django.http import HttpResponse
from . import token
import jwt
from .models import *
import datetime
import os
import requests
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import logging

logging.basicConfig(level=logging.DEBUG)

@csrf_exempt
@token.token_required
def callmilton(request, **kwargs):
    err_dict_user_dne = {"body": "User does not exist."}
    err_dict_wrong_args = {"body": "Incorrect args"}
    err_dict_disc = {"body": "Discord not authorized."}

    if request.method == 'POST':
        try:
            user = User.objects.get(username__exact=kwargs['username'])
            app_user_obj = AppUser.objects.get(user__exact=user)
        except User.DoesNotExist as e:
            logging.debug(e)
            return HttpResponse(content=json.dumps(err_dict_user_dne), content_type='application/json', status=400)
        except AppUser.DoesNotExist as e:
            logging.debug(e)
            return HttpResponse(content=json.dumps(err_dict_disc),content_type='application/json',status=400)

        disc_token = app_user_obj.token
        date = app_user_obj.token_time
        refresh_token = app_user_obj.refresh_token
        if 'clip' not in request.POST or 'board' not in request.POST:
            print("Incorrect args")
            return HttpResponse(content=json.dumps(err_dict_wrong_args),content_type='application/json',status=400)
        else:
            clip = request.POST['clip']
            board = request.POST['board']
        if datetime.datetime.now(datetime.timezone.utc) - date > datetime.timedelta(seconds=604800):
            client_id = os.environ.get('DISCORD_CLIENT_ID')
            client_secret = os.environ.get('DISCORD_CLIENT_SECRET')
            redirect_uri = os.environ.get('REDIRECT_URI')
            api_endpoint = 'https://discordapp.com/api/oauth2/token'

            data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'redirect_uri': redirect_uri,
                'scope': 'identify'
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            r = requests.post(api_endpoint, data=data, headers=headers)
            r.raise_for_status()
            result = r.json()

            app_user_obj.token = result["access_token"]
            app_user_obj.save()
            disc_token = app_user_obj.token
        r = requests.get("https://discordapp.com/api/users/@me", headers={"Authorization": "Bearer " + disc_token})
        r.raise_for_status()
        j = r.json()
        discid = j["id"]

        r = requests.post(os.environ.get("MILTON_WEBHOOK"), headers={"Content-Type": "application/json"},
                          json={"content": "+milton " + clip + " " + board + " " + discid})
        return HttpResponse("Well done.")

def board_api(request):
    if request.method == 'GET':
        board_manager = Board.objects.all()
        bds = {}
        for bd in board_manager:
            board_clips = bd.clip_set.all()
            bds[bd.name] = []
            for clip in board_clips:
                bds[bd.name].append(clip.name)
        bds_json = json.dumps(bds)
        return HttpResponse(content=bds_json,content_type='application/json')

@token.token_required
def playlist_api(request, **kwargs):
    if request.method == 'GET':
        err_dict_user_dne = {"body": "User does not exist."}
        err_dict_no_playlists = {"body": "No playlists made yet."}
        try:
            user = User.objects.get(username__exact=kwargs['username'])
        except User.DoesNotExist as e:
            logging.debug(e)
            return HttpResponse(content=json.dumps(err_dict_user_dne), content_type='application/json', status=400)
        if user.playlist_set.all().exists():
            playlist_manager = user.playlist_set.all()
            pls = {}
            for pl in playlist_manager:
                playlist_clips = pl.playlistclip_set.all()
                pls[pl.name] = []
                for clip in playlist_clips:
                    pls[pl.name].append(clip.name)
            pls_json = json.dumps(pls)
            return HttpResponse(content=pls_json,content_type='application/json')
        else:
            return HttpResponse(content=json.dumps(err_dict_no_playlists), content_type='application/json', status=404)