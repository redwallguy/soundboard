from django.shortcuts import render
from .models import *
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import logging

logging.basicConfig(level=logging.DEBUG)

def boards(request):
    board_list = Board.objects.all()
    return render(request, "control/boards.html", {"boards":board_list})

def clips_of_board(request, spec_board):
    board_of_clips = Board.objects.get(pk__exact=spec_board)
    clips = board_of_clips.clip_set.all()
    aliases = {}
    for clip in clips:
        aliases[clip.name] = clip.alias_set.all()
    return render(request, "control/clips.html",{"board":board_of_clips,
                                                    "clips":clips,
                                                    "aliases":aliases})

def app_user(view):
    def not_user():
        data = {"error": "Not an app user. Please register through WEBSITE_NAME/discord."}
        return JsonResponse(data)
    def wrapper(request):
        try:
            user = AppUser.objects.get(user=request.user)
        except AppUser.DoesNotExist as e:
            return not_user()
        return view(request, user=user)
    return wrapper

@login_required
@app_user
def playlist(request, **kwargs):
    playlists = Playlist.objects.filter(user=kwargs["user"])
    return render(request, "control/playlists/playlists.html", {"playlists": playlists})

@login_required
@app_user
def clips_of_playlist(request, spec_playlist, **kwargs):
    try:
        playlist_of_clips = Playlist.objects.get(name=spec_playlist, user=kwargs["user"])
    except Playlist.DoesNotExist as e:
        data = {"error": "Playlist does not exist."}
        return JsonResponse(data)
    plclips = playlist_of_clips.playlistclip_set.all()
    clips = [clip.clip for clip in plclips]
    aliases = {}
    for clip in clips:
        aliases[clip.name] = clip.alias_set.all()
    return render(request, "control/playlists/playlistclips.html", {"playlist": spec_playlist,
                                                          "clips": clips,
                                                          "aliases": aliases})

@login_required
@app_user
def new_playlist(request, **kwargs):
    if request.method == 'POST':
        if Playlist.objects.filter(name__iexact=request.POST["name"],user=kwargs["user"]).exists():
            data = {"error": "Playlist with this name already exists."}
            return JsonResponse(data)
        else:
            try:
                p = Playlist(name=request.POST["name"], user=kwargs["user"])
                p.save()
                data = {"name": p.name}
                return JsonResponse(data)
            except ValidationError:
                data = {"error": "Name is too long. Max length is 20."}
                return JsonResponse(data)

@login_required
@app_user
def new_clip_of_playlist(request, **kwargs):
    if request.method == 'POST':
        if PlaylistClip.objects.filter(clip__name=request.POST["clip"],playlist__name=request.POST["playlist_name"],
                                       playlist__user=kwargs["user"]).exists():
            data = {"error": "This clip already exists on this playlist."}
            return JsonResponse(data)
        else:
            try:
                clip = Clip.objects.get(name=request.POST["clip"],board__name=request.POST["board"])
                playlist_of_clip = Playlist.get(name=request.POST["playlist"],user=kwargs["user"])
            except Clip.DoesNotExist as e:
                logging.info("Clip DNE: name, board = %s, %s", (request.POST["clip"], request.POST["board"]))
                data = {"error": "Clip does not exist."}
                return JsonResponse(data)
            except Playlist.DoesNotExist as e:
                logging.info("Playlist DNE: name, user = %s, %s", (request.POST["playlist"], kwargs["user"]))
                data = {"error": "Playlist does not exist."}
                return JsonResponse(data)
            c = PlaylistClip(clip=clip,playlist=playlist_of_clip)
            c.save()
            success_msg = c.clip.name + " from " + c.clip.board.name + " added to playlist!"
            data = {"clip": success_msg}
            return JsonResponse(data)


