# Generated by Django 4.2.2 on 2023-07-26 03:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brolympics', '0015_alter_event_h2h_max_score_alter_event_h2h_min_score_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event_h2h',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event_ind',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='event_team',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
