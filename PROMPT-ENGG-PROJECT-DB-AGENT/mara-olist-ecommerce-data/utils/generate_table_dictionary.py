import contextlib

import psycopg2
from psycopg2.extras import DictCursor

from olist_ecommerce import config

ECOMMERCE_TABLES = ['ecommerce.customers', 'ecommerce.geolocation', 'ecommerce.order_items',
                    'ecommerce.order_payments',
                    'ecommerce.order_reviews', 'ecommerce.orders', 'ecommerce.products',
                    'ecommerce.sellers', 'ecommerce.product_category_name_translations']

MARKETING_TABLES = ['marketing.closed_deals', 'marketing.marketing_qualified_leads']


@contextlib.contextmanager
def postgres_cursor_context() -> 'psycopg2.extensions.cursor':
    """Creates a context with a psycopg2 cursor for a database alias"""
    import psycopg2
    import psycopg2.extensions

    connection = psycopg2.connect(dbname=config.db_name(), user=config.db_user(), password=config.db_password(),
                                  host=config.db_host(), port=config.db_port())  # type: psycopg2.extensions.connection
    cursor = connection.cursor()  # type: psycopg2.extensions.cursor
    try:
        yield cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()

def fetch_table_dictcursor(schema_table_name):
    try:
        with postgres_cursor_context() as cursor:

            schema_name, table_name = tuple(schema_table_name.split('.'))
            # Query to get column names and data types
            cursor.execute("""
                        SELECT 
                            cols.column_name, 
                            cols.data_type,
                            pgdesc.description
                        FROM information_schema.columns cols
                        LEFT JOIN pg_catalog.pg_class pgclass 
                            ON cols.table_name = pgclass.relname
                        LEFT JOIN pg_catalog.pg_namespace pgns
                            ON pgclass.relnamespace = pgns.oid
                        LEFT JOIN pg_catalog.pg_attribute pgattr
                            ON pgclass.oid = pgattr.attrelid 
                            AND cols.column_name = pgattr.attname
                        LEFT JOIN pg_catalog.pg_description pgdesc
                            ON pgattr.attrelid = pgdesc.objoid 
                            AND pgattr.attnum = pgdesc.objsubid
                        WHERE cols.table_schema = %s 
                          AND cols.table_name = %s
                    """, (schema_name, table_name))

            schema_dict = (schema_table_name,{col: {"data_type": dtype, "description": desc if desc else "No description"} for col, dtype, desc in cursor.fetchall()})
            return schema_dict
    except Exception as e:
        print(f"Error: {e}")
        return None

table_dicts = []

try:
    for table in ECOMMERCE_TABLES:
        table_dicts.append(fetch_table_dictcursor(table))

    for table in MARKETING_TABLES:
        table_dicts.append(fetch_table_dictcursor(table))
except Exception as ex:
    raise ex

print(table_dicts)