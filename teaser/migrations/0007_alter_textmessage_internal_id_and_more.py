# Generated by Django 4.1.7 on 2023-03-05 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teaser', '0006_alter_textmessagebatch_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textmessage',
            name='internal_id',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='textmessagebatch',
            name='internal_id',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]