# Generated by Django 4.1.7 on 2023-03-10 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jigger', '0008_campaignlead_status_alter_campaignlead_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='provider',
            field=models.CharField(default='warmup001', max_length=15),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='campaign',
            name='settings',
            field=models.JSONField(blank=True, null=True),
        ),
    ]