import requests
import control.models as models
import os
from django.core.management.base import BaseCommand
import datetime

class Command(BaseCommand):
    def handle(self, *args, **options):
        clip = args[0]
        board = args[1]
        uid = args[2]

        try:
            token_obj = models.AppUser.objects.get(user__exact=uid)
        except models.DiscordAppUser.DoesNotExist as e:
            self.stderr(e)
            return

        token = token_obj.token
        date = token_obj.token_time
        refresh_token = token_obj.refresh_token

        if token == "":
            self.stderr("No token")
            return
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

            r = requests.post(api_endpoint,data=data,headers=headers)
            r.raise_for_status()
            result = r.json()

            token_obj.token = result["access_token"]
            token_obj.save()
        else:
            r = requests.get("https://discordapp.com/api/users/@me", headers={"Authorization": "Bearer " + token})
            r.raise_for_status()
            j = r.json()
            discid = j["id"]

            r = requests.post(os.environ.get("MILTON_WEBHOOK"), headers={"Content-Type":"application/json"},
                              json={"content": "!milton " + clip + " " + board + " " + discid})


