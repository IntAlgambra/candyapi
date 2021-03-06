# Generated by Django 3.1.7 on 2021-03-18 09:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('utils', '0001_initial'),
        ('couriers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Delievery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_time', models.DateTimeField()),
                ('last_delievery_time', models.DateTimeField()),
                ('completed', models.BooleanField(default=False)),
                ('courier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='delieveries', to='couriers.courier')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('order_id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('weight', models.FloatField()),
                ('delievered', models.BooleanField(default=False)),
                ('delievery_time', models.DateTimeField(null=True)),
                ('completion_time', models.IntegerField(null=True)),
                ('delievery', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='orders.delievery')),
                ('intervals', models.ManyToManyField(to='utils.Interval')),
                ('region', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='utils.region')),
            ],
        ),
    ]
