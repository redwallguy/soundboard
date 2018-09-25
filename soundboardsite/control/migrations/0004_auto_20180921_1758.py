# Generated by Django 2.0.1 on 2018-09-21 17:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('control', '0003_appuser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appuser',
            name='password_hash',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='appuser',
            name='refresh_token',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='appuser',
            name='token',
            field=models.CharField(default='', max_length=100),
        ),
    ]
