from django.db import models
from constrainedfilefield.fields import ConstrainedFileField
from django.core.exceptions import ValidationError
from django.core.exceptions import NON_FIELD_ERRORS

def board_upload_handler(instance,filename):
    return '{bname}/{file}'.format(bname=instance.name,file=filename)

def clip_upload_handler(instance,filename):
    return '{bname}/{file}'.format(bname=instance.board.name,file=filename)

class Board(models.Model):
    name = models.CharField(max_length=20,primary_key=True)
    cover = ConstrainedFileField(null=True,
                                 blank=True,
                                 max_upload_size=512000,
                                 content_types=['image/jpeg',
                                               'image/png'],
                                 upload_to=board_upload_handler
                                 )
    def __str__(self):
        return self.name

class Clip(models.Model):
    name = models.CharField(max_length=20)
    board = models.ForeignKey(Board,on_delete=models.CASCADE)
    sound = ConstrainedFileField(max_upload_size=250000,
                                 content_types=['audio/mpeg',
                                                'audio/mp3'],
                                 upload_to=clip_upload_handler
                                 )
    def __str__(self):
        return self.name

    class Meta:
        unique_together = ("name","board")

class Alias(models.Model):
    name = models.CharField(max_length=15)
    clip = models.ForeignKey(Clip,on_delete=models.CASCADE)

    def validate_unique(self, *args, **kwargs):
        super(Alias, self).validate_unique(*args,**kwargs)
        if self.__class__.objects.filter(clip__board__name=
                                        self.clip.board.name,name=
                                        self.name).exists():
            raise ValidationError(
                {
                    NON_FIELD_ERRORS: [
                        'Alias with same name already exists in this board.'
                        ],
                }
            )

    def __str__(self):
        return self.name