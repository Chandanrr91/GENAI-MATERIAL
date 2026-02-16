import contextlib
import logging
import pathlib
import traceback

import psycopg2

import config


ECOMMERCE_TABLES = ['ecommerce.customers', 'ecommerce.geolocation', 'ecommerce.order_items',
                    'ecommerce.order_payments',
                    'ecommerce.order_reviews', 'ecommerce.orders', 'ecommerce.products',
                    'ecommerce.sellers', 'ecommerce.product_category_name_translations']

MARKETING_TABLES = ['marketing.closed_deals', 'marketing.marketing_qualified_leads']
# MARKETING_TABLES = ['marketing.closed_deals']



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


def create_schema(schema_script):
    """Creates the database schemas"""
    with open(pathlib.Path(__file__).parent / schema_script) as file:
        script = file.read()

    with postgres_cursor_context() as cursor:
        cursor.execute(script)


def insert_data(dataset):
    try:
        """Inserts the the csv files in PostgreSQL"""
        sql_statement = """
        COPY {table_name} FROM STDIN WITH
            CSV
            HEADER
            DELIMITER AS ','
            QUOTE '"'
        """

        table_names = ECOMMERCE_TABLES if 'olist-ecommerce' in dataset else MARKETING_TABLES
        print(dataset)
        pathlist = list(pathlib.Path(f"/Users/shahan.shaik/Shahan/Personal/Mylearning/GENAI-PRUDHVI/PROJECT-DB-AGENT/mara-olist-ecommerce-data_copy/data/{dataset}").glob(
            '**/*.csv'))

        print(f"count_pathlist:{len(list(pathlist))},count_table_name:{len(list(table_names))}")
        print(f"pathlist:{list(pathlist)},count_table_name:{list(table_names)}")
        ziped_data = list(zip(sorted(pathlist), table_names))
        print(f"ziped_data:{list(ziped_data)}")
        for csv_file, table_name in list(ziped_data):
            print("Inside for")
            print(f"file_name:{csv_file},table_name:{table_name}")
            with open(csv_file) as file:
                with postgres_cursor_context() as cursor:
                    cursor.copy_expert(sql=sql_statement.format(table_name=table_name), file=file)
    except Exception as ex:
        print(f"Error with code:{traceback.format_exc()}")


def load_data():
    create_schema('create_ecommerce_schema.sql')
    insert_data('olist-ecommerce')
    print('Schema "ecommerce" created successfully. Tables created: [{}]'.format(', '.join(ECOMMERCE_TABLES)))
    create_schema('create_marketing_schema.sql')
    insert_data('olist-marketing-funnel')
    print('Schema "marketing" created successfully. Tables created: [{}]'.format(', '.join(MARKETING_TABLES)))


load_data()
