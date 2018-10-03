from django.shortcuts import render
from .models import *
from django.contrib.auth.decorators import login_required

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
@login_required
def playlist(request):
    playlists = Playlist.objects.filter(user=request.user)
    return render(request, "control/playlists.html", {"playlists": playlists})

@login_required
def clips_of_playlist(request, spec_playlist):
    playlist_of_clips = Playlist.objects.get(name=spec_playlist)
    clips = playlist_of_clips.clip_set.all()
    aliases = {}
    for clip in clips:
        aliases[clip.name] = clip.alias_set.all()
    return render(request, "control/playlistclips.html", {"playlist": spec_playlist,
                                                          "clips": clips,
                                                          "aliases": aliases})