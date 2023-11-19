# Generated by Django 4.2.5 on 2023-10-08 12:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0003_remove_profile_referee_alter_profile_referral_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='referee',
            field=models.ForeignKey(default=5, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='referral', to=settings.AUTH_USER_MODEL),
        ),
    ]
