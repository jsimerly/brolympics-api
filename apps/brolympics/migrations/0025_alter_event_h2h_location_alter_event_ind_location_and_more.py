# Generated by Django 4.2.2 on 2024-09-11 00:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brolympics', '0024_alter_team_img'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event_h2h',
            name='location',
            field=models.CharField(blank=True, max_length=260, null=True),
        ),
        migrations.AlterField(
            model_name='event_ind',
            name='location',
            field=models.CharField(blank=True, max_length=260, null=True),
        ),
        migrations.AlterField(
            model_name='event_team',
            name='location',
            field=models.CharField(blank=True, max_length=260, null=True),
        ),
    ]
