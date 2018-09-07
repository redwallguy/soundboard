from django.http import HttpResponse
from . import token
import jwt
from .models import *
import datetime
import os
import requests
import json

def callmilton(request):
    err_dict_bad_token = {"body": "Bad/no token."}
    err_dict_user_dne = {"body": "User does not exist."}
    err_dict_wrong_args = {"body": "Incorrect args"}
    err_dict_disc = {"body": "Discord not authorized."}
    try:
        user = token.validate_token(token.token_from_header(request['Authorization']))
    except (KeyError, jwt.InvalidTokenError):
        print("Bad token")
        return HttpResponse(content=json.dumps(err_dict_bad_token),content_type='application/json',status=400)

    if request.method == 'POST' and user:
        try:
            user_obj = AppUser.objects.get(user__exact=user)
        except AppUser.DoesNotExist as e:
            print(e)
            return HttpResponse(content=json.dumps(err_dict_user_dne),content_type='application/json',status=400)

        disc_token = user_obj.token
        date = user_obj.token_time
        refresh_token = user_obj.refresh_token
        if 'clip' not in request.POST or 'board' not in request.POST:
            print("Incorrect args")
            return HttpResponse(content=json.dumps(err_dict_wrong_args),content_type='application/json',status=400)
        else:
            clip = request.POST['clip']
            board = request.POST['board']
        if disc_token == "":
            print("No discord token")
            return HttpResponse(content=json.dumps(err_dict_disc),content_type='application/json',status=409)
        elif datetime.datetime.now(datetime.timezone.utc) - date > datetime.timedelta(seconds=604800):
            client_id = os.environ.get('DISCORD_CLIENT_ID')
            client_secret = os.environ.get('DISCORD_CLIENT_SECRET')
            redirect_uri = 'https://digest-soundboard.herokuapp.com/auth/'
            api_endpoint = 'https://discordapp.com/api/oauth2/token'

            data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'redirect_uri': redirect_uri
            }
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            r = requests.post(api_endpoint, data=data, headers=headers)
            r.raise_for_status()
            result = r.json()

            user_obj.token = result["access_token"]
            user_obj.save()
            disc_token = user_obj.token
        else:
            pass
        r = requests.get("https://discordapp.com/api/users/@me", headers={"Authorization": "Bearer " + disc_token})
        r.raise_for_status()
        j = r.json()
        discid = j["id"]

        r = requests.post(os.environ.get("MILTON_WEBHOOK"), headers={"Content-Type": "application/json"},
                          json={"content": "!milton " + clip + " " + board + " " + discid})

def api(request):
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