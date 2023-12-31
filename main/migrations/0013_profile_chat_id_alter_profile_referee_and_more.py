# Generated by Django 4.2.5 on 2023-12-29 11:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0012_alter_match_created_alter_profile_referee_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='chat_id',
            field=models.CharField(default='admin', max_length=200),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='profile',
            name='referee',
            field=models.ForeignKey(blank=True, default=6, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='referral', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='user',
            field=models.ForeignKey(default=6, on_delete=django.db.models.deletion.SET_DEFAULT, to=settings.AUTH_USER_MODEL),
        ),
    ]
