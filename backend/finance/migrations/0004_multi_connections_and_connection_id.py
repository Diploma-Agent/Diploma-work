from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0003_userprofile_bio_userprofile_date_of_birth_and_more'),
    ]

    operations = [
        # Прибираємо unique_together з BankConnection — дозволяємо кілька з'єднань одного банку
        migrations.AlterUniqueTogether(
            name='bankconnection',
            unique_together=set(),
        ),

        # Прибираємо unique_together з CryptoExchange — дозволяємо кілька з'єднань однієї біржі
        migrations.AlterUniqueTogether(
            name='cryptoexchange',
            unique_together=set(),
        ),

        # Додаємо connection_id до Transaction для прив'язки до конкретного підключення
        migrations.AddField(
            model_name='transaction',
            name='connection_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
