# Generated by Django 4.1.7 on 2023-03-12 15:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jigger', '0011_rename_provider_campaign_driver'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaignlead',
            name='campaign',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leads', to='jigger.campaign'),
        ),
    ]
