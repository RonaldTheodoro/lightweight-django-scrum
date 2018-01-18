# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Sprint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=100, blank=True, default='')),
                ('description', models.TextField(verbose_name='description', blank=True, default='')),
                ('end', models.DateField(verbose_name='end', unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=100)),
                ('description', models.TextField(verbose_name='description', blank=True, default='')),
                ('status', models.SmallIntegerField(verbose_name='status', default=1, choices=[(1, 'Not Started'), (2, 'In Progress'), (3, 'Testing'), (4, 'Done')])),
                ('order', models.SmallIntegerField(verbose_name='order', default=0)),
                ('started', models.DateField(verbose_name='started', blank=True, null=True)),
                ('due', models.DateField(verbose_name='due', blank=True, null=True)),
                ('completed', models.DateField(verbose_name='completed', blank=True, null=True)),
                ('assigned', models.ForeignKey(verbose_name='assigned', blank=True, null=True, to=settings.AUTH_USER_MODEL)),
                ('sprint', models.ForeignKey(verbose_name='sprint', blank=True, default='', to='board.Sprint')),
            ],
        ),
    ]
