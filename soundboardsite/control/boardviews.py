from django.shortcuts import render
from .models import *

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