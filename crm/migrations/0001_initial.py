# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-24 08:23
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=140, verbose_name='First name')),
                ('middle_name', models.CharField(blank=True, max_length=140, verbose_name='Middle name')),
                ('last_name', models.CharField(max_length=140, verbose_name='Last name')),
                ('email', models.EmailField(max_length=254)),
                ('date_arrived', models.DateTimeField(auto_now_add=True)),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('starting_level', models.CharField(choices=[('A1', 'A1'), ('B1', 'B1'), ('C1', 'C1'), ('A2', 'A2'), ('B2', 'B2'), ('C2', 'C2')], db_index=True, default='A1', max_length=2)),
                ('current_level', models.CharField(db_index=True, default='A1', max_length=2)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
