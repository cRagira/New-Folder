# Generated by Django 4.2.5 on 2023-12-02 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_ethertransaction_alter_profile_referee_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ethertransaction',
            old_name='blockHash',
            new_name='hash',
        ),
        migrations.AlterField(
            model_name='ethertransaction',
            name='timeStamp',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='ethertransaction',
            name='value',
            field=models.FloatField(),
        ),
    ]