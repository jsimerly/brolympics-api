# Generated by Django 4.2.2 on 2024-09-03 21:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_firebaseuser_imgurl'),
    ]

    operations = [
        migrations.RenameField(
            model_name='firebaseuser',
            old_name='imgUrl',
            new_name='img_url',
        ),
    ]
