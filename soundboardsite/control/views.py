from django.shortcuts import render_to_response
from django.http import HttpResponse
from .models import *
import requests
import os
from .milton_script.milton import *

def boards(request):
    board_list = Board.objects.all()
    return render_to_response("control/boards.html", {"boards":board_list})

def clips_of_board(request, spec_board):
    board_of_clips = Board.objects.get(pk__exact=spec_board)
    clips = board_of_clips.clip_set.all()
    aliases = {}
    for clip in clips:
        aliases[clip.name] = clip.alias_set.all()
    return render_to_response("control/clips.html",{"board":board_of_clips,
                                                    "clips":clips,
                                                    "aliases":aliases})
    

def index(request):
    return HttpResponse("Testing index success")

def authstate(request):
    if request.method == 'POST' and 'state' in request.POST:
        user_hash = request.POST['state']
        u = DiscordAppUser(user_hash=user_hash)
        u.save()

def authcode(request):
    if request.method == 'GET' and 'state' in request.GET:
        hash_to_check = request.GET['state']
        if DiscordAppUser.objects.filter(user_hash=hash_to_check).exists() and 'code' in request.GET:
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

            u = DiscordAppUser.objects.filter(user_hash=hash_to_check)
            #GET req to disc api to find @me id and store
            u.save()

def callmilton(request):
    if request.method == 'POST' and 'state' in request.POST:



# Create your views here.
