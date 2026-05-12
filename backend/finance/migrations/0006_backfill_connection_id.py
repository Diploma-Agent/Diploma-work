from django.db import migrations


def backfill_connection_ids(apps, schema_editor):
    """
    Старі транзакції (синхронізовані до додавання поля connection_id) мають connection_id = null.
    Для кожного користувача та типу джерела (monobank, binance, ...)
    присвоюємо null-транзакції найстарішому підключенню цього типу.
    """
    try:
        from django.conf import settings
        from pymongo import MongoClient
        from collections import defaultdict

        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DATABASE]

        tx_coll = db['transactions']

        # ── Банківські підключення ────────────────────────────────────────────
        bank_conns = list(
            db['bank_connections'].find({}).sort('created_at', 1)
        )
        # Групуємо по (user_id, bank_name), беремо перше (найстаріше)
        oldest_bank = {}
        for conn in bank_conns:
            user_id   = conn.get('user_id')
            bank_name = conn.get('bank_name', '')
            conn_id   = conn.get('id') or conn.get('_id')
            key = (user_id, bank_name)
            if key not in oldest_bank:
                oldest_bank[key] = conn_id

        for (user_id, bank_name), conn_id in oldest_bank.items():
            # Транзакції без connection_id (null або поле відсутнє)
            for query in [
                {'user_id': user_id, 'source': bank_name, 'connection_id': None},
                {'user_id': user_id, 'source': bank_name, 'connection_id': {'$exists': False}},
            ]:
                result = tx_coll.update_many(query, {'$set': {'connection_id': conn_id}})
                if result.modified_count:
                    print(f"[migration 0006] bank {bank_name} user={user_id} conn={conn_id}: "
                          f"backfilled {result.modified_count} transactions")

        # ── Біржові підключення ───────────────────────────────────────────────
        exchange_conns = list(
            db['crypto_exchanges'].find({}).sort('created_at', 1)
        )
        oldest_exchange = {}
        for conn in exchange_conns:
            user_id       = conn.get('user_id')
            exchange_name = conn.get('exchange_name', '')
            conn_id       = conn.get('id') or conn.get('_id')
            key = (user_id, exchange_name)
            if key not in oldest_exchange:
                oldest_exchange[key] = conn_id

        for (user_id, exchange_name), conn_id in oldest_exchange.items():
            for query in [
                {'user_id': user_id, 'source': exchange_name, 'connection_id': None},
                {'user_id': user_id, 'source': exchange_name, 'connection_id': {'$exists': False}},
            ]:
                result = tx_coll.update_many(query, {'$set': {'connection_id': conn_id}})
                if result.modified_count:
                    print(f"[migration 0006] exchange {exchange_name} user={user_id} conn={conn_id}: "
                          f"backfilled {result.modified_count} transactions")

        client.close()
        print("[migration 0006] backfill_connection_ids completed")

    except Exception as e:
        print(f"[migration 0006] ERROR: {e}")
        import traceback
        traceback.print_exc()


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0005_drop_mongo_unique_indexes'),
    ]

    operations = [
        migrations.RunPython(
            backfill_connection_ids,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
