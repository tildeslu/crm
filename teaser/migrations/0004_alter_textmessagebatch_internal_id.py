# Generated by Django 4.1.7 on 2023-03-05 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teaser', '0003_alter_textmessage_batch_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textmessagebatch',
            name='internal_id',
            field=models.BigIntegerField(blank=True, null=True),
        ),
    ]
