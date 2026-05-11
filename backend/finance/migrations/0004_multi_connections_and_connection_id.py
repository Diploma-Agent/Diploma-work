from django.db import migrations, models


def drop_unique_mongo_indexes(apps, schema_editor):
    """
    Djongo не завжди фізично видаляє MongoDB-індекси через AlterUniqueTogether.
    Видаляємо їх вручну через PyMongo, щоб дозволити кілька з'єднань одного типу.
    """
    try:
        from django.conf import settings
        from pymongo import MongoClient

        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DATABASE]

        targets = [
            ('bank_connections',  {'user_id', 'bank_name'}),
            ('crypto_exchanges',  {'user_id', 'exchange_name'}),
        ]

        for coll_name, field_set in targets:
            coll = db[coll_name]
            try:
                for idx in coll.list_indexes():
                    idx_keys = set(idx['key'].keys()) - {'_id'}
                    if idx_keys == field_set:
                        coll.drop_index(idx['name'])
                        print(f"[migration] Dropped index {idx['name']} on {coll_name}")
                        break
            except Exception as e:
                print(f"[migration] Could not drop index on {coll_name}: {e}")

        client.close()
    except Exception as e:
        print(f"[migration] drop_unique_mongo_indexes skipped: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0003_userprofile_bio_userprofile_date_of_birth_and_more'),
    ]

    operations = [
        # Прибираємо unique_together з BankConnection на рівні Django ORM
        migrations.AlterUniqueTogether(
            name='bankconnection',
            unique_together=set(),
        ),

        # Прибираємо unique_together з CryptoExchange на рівні Django ORM
        migrations.AlterUniqueTogether(
            name='cryptoexchange',
            unique_together=set(),
        ),

        # Фізично видаляємо MongoDB-індекси через PyMongo
        migrations.RunPython(
            drop_unique_mongo_indexes,
            reverse_code=migrations.RunPython.noop,
        ),

        # Додаємо connection_id до Transaction для прив'язки до конкретного підключення
        migrations.AddField(
            model_name='transaction',
            name='connection_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
