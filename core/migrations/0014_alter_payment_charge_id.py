# Generated by Django 4.0.3 on 2022-04-04 08:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_address_id_alter_coupon_id_alter_item_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='charge_id',
            field=models.CharField(max_length=24),
        ),
    ]
