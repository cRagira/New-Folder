# Generated by Django 4.2.5 on 2023-12-26 06:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_alter_ethertransaction_txreceipt_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='address',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
