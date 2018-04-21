from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("Testing index success")

def base(request):
    return render(request, 'control/base.html')
# Create your views here.
