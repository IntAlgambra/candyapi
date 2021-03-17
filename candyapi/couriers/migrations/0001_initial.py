# Generated by Django 3.1.7 on 2021-03-12 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('region_id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Interval',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.IntegerField()),
                ('end', models.IntegerField()),
            ],
            options={
                'unique_together': {('start', 'end')},
            },
        ),
        migrations.CreateModel(
            name='Courier',
            fields=[
                ('courier_id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('courier_type', models.CharField(max_length=4)),
                ('rating', models.FloatField(default=5)),
                ('earnings', models.FloatField(default=0)),
                ('last_deliver_time', models.DateTimeField(null=True)),
                ('intervals', models.ManyToManyField(related_name='couriers', to='couriers.Interval')),
                ('regions', models.ManyToManyField(related_name='couriers', to='couriers.Region')),
            ],
        ),
    ]
