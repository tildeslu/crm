# Generated by Django 4.1.7 on 2023-02-28 19:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='CampaignLead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.IntegerField(choices=[(0, 'Dead'), (1, 'New'), (2, 'In Funnel'), (3, 'Converted'), (4, 'Cancelled')])),
                ('stage', models.CharField(max_length=15)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jigger.campaign')),
            ],
        ),
        migrations.CreateModel(
            name='ContactTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
            ],
        ),
        migrations.CreateModel(
            name='FunnelEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('source', models.CharField(max_length=15)),
                ('action', models.CharField(max_length=15)),
                ('data', models.JSONField()),
                ('seen', models.BooleanField(default=False)),
                ('incoming', models.BooleanField(default=False)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jigger.campaignlead')),
            ],
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('msisdn', models.CharField(max_length=15)),
                ('tags', models.ManyToManyField(to='jigger.contacttag')),
            ],
        ),
        migrations.AddField(
            model_name='campaignlead',
            name='contact',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jigger.contact'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='contacts',
            field=models.ManyToManyField(through='jigger.CampaignLead', to='jigger.contact'),
        ),
    ]
