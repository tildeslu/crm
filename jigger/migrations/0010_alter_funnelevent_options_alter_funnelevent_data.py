# Generated by Django 4.1.7 on 2023-03-12 13:22

import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jigger', '0009_campaign_provider_campaign_settings'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='funnelevent',
            options={'get_latest_by': 'timestamp', 'ordering': ['timestamp']},
        ),
        migrations.AlterField(
            model_name='funnelevent',
            name='data',
            field=models.JSONField(blank=True, encoder=django.core.serializers.json.DjangoJSONEncoder, null=True),
        ),
    ]
