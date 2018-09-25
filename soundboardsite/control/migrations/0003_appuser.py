# Generated by Django 2.0.1 on 2018-09-19 01:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('control', '0002_auto_20180617_0216'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppUser',
            fields=[
                ('user', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('password_hash', models.CharField(max_length=64)),
                ('token', models.CharField(default='', max_length=64)),
                ('refresh_token', models.CharField(default='', max_length=64)),
                ('token_time', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]