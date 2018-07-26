import requests
import control.models as models
import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        clip = args[0]
        board = args[1]
        uid = args[2]

        try:
            token = models.DiscordAppUser.objects.get(user_hash__exact=uid).token
        except models.DiscordAppUser.DoesNotExist as e:
            self.stderr(e)
            return

        r = requests.get("https://discordapp.com/api/users/@me", headers={"Authorization": "Bearer " + token})
        r.raise_for_status()
        j = r.json()
        discid = j["id"]

        r = requests.post(os.environ.get("MILTON_WEBHOOK"), headers={"Content-Type":"application/json"},
                          json={"content": "!milton " + clip + " " + board + " " + discid})


