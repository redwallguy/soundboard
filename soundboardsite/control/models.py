from django.db import models
import storages.backends.s3boto

protected_storage = storages.backends.s3boto.S3BotoStorage(
  acl='private',
  querystring_auth=True,
  querystring_expire=600, # 10 minutes, try to ensure people won't/can't share
)

class Board(models.Model):
    name = models.CharField(max_length=20,primary_key=True)
    cover = models.ImageField(upload_to=self.name)

class Clip(models.Model):
    name = models.CharField(max_length=20,primary_key=True)
    board = models.ForeignKey(Board,on_delete=models.CASCADE)
