# Generated by Django 4.1.7 on 2023-03-04 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teaser', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='textmessage',
            name='recipient',
            field=models.CharField(max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='textmessage',
            name='status',
            field=models.IntegerField(choices=[(0, 'New'), (1, 'Sent'), (2, 'En Route'), (3, 'Delivered'), (4, 'Expired'), (5, 'Rejected')], default=0),
        ),
    ]
