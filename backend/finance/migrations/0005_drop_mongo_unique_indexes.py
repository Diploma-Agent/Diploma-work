from django.db import migrations


def drop_unique_mongo_indexes(apps, schema_editor):
    """
    Фізично видаляємо MongoDB compound-індекси (user_id, bank_name) та (user_id, exchange_name).
    Django AlterUniqueTogether не видаляє їх з MongoDB, тому робимо це через PyMongo напряму.
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

        for coll_name, target_fields in targets:
            try:
                coll = db[coll_name]
                indexes = list(coll.list_indexes())
                for idx in indexes:
                    idx_fields = set(idx['key'].keys()) - {'_id'}
                    if idx_fields == target_fields:
                        coll.drop_index(idx['name'])
                        print(f"[migration 0005] Dropped index '{idx['name']}' on '{coll_name}'")
                        break
                else:
                    print(f"[migration 0005] No matching index found on '{coll_name}' — skipping")
            except Exception as e:
                print(f"[migration 0005] Error on '{coll_name}': {e}")

        client.close()
    except Exception as e:
        print(f"[migration 0005] Skipped: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0004_multi_connections_and_connection_id'),
    ]

    operations = [
        migrations.RunPython(
            drop_unique_mongo_indexes,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
