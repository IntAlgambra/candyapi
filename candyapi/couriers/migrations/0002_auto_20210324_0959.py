# Generated by Django 3.1.7 on 2021-03-24 09:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('couriers', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='courier',
            name='earnings',
        ),
        migrations.RemoveField(
            model_name='courier',
            name='last_deliver_time',
        ),
        migrations.RemoveField(
            model_name='courier',
            name='rating',
        ),
    ]
