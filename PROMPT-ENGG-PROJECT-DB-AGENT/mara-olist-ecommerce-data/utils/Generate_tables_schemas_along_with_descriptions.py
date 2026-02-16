import psycopg2
import openai
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# Set OpenAI API Key
openai.api_key = "your_openai_api_key"

# Domain-Specific Contexts
DOMAIN_CONTEXT = {
    "ecommerce": """
    This database contains tables related to an e-commerce platform. Common entities include:
    - Customers (user details, orders, addresses, preferences)
    - Orders (products, payments, shipping info, reviews)
    - Products (categories, pricing, inventory, sellers)
    - Transactions (payments, refunds)
    - Locations (geographical details of customers and sellers)
    """,
    "marketing": """
    This database contains tables related to a marketing platform. Common entities include:
    - Leads (prospective customers for marketing campaigns)
    - Deals (closed sales or business deals resulting from marketing efforts)
    """
}

# Table Categories
ECOMMERCE_TABLES = ['ecommerce.customers', 'ecommerce.geolocation', 'ecommerce.order_items',
                    'ecommerce.order_payments', 'ecommerce.order_reviews', 'ecommerce.orders',
                    'ecommerce.products', 'ecommerce.sellers', 'ecommerce.product_category_name_translations']

MARKETING_TABLES = ['marketing.closed_deals', 'marketing.marketing_qualified_leads']


def fetch_table_schema(dbname, user, password, host, port, schema_name, table_name):
    """
    Fetches schema (column names, data types, and descriptions) from PostgreSQL.
    """
    try:
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = conn.cursor()

        # Query to fetch column details and descriptions
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

        # Build schema dictionary
        schema = [{"column_name": col, "data_type": dtype, "description": desc if desc else None} for col, dtype, desc
                  in cursor.fetchall()]

        # Fetch table description if available
        cursor.execute("""
            SELECT obj_description(pgclass.oid, 'pg_class')
            FROM pg_catalog.pg_class pgclass
            JOIN pg_catalog.pg_namespace pgns
                ON pgclass.relnamespace = pgns.oid
            WHERE pgns.nspname = %s
              AND pgclass.relname = %s
        """, (schema_name, table_name))
        table_description = cursor.fetchone()
        table_description = table_description[0] if table_description and table_description[0] else None

        cursor.close()
        conn.close()

        return schema, table_description

    except Exception as e:
        print(f"Error fetching schema for {schema_name}.{table_name}: {e}")
        return None, None


def generate_table_description_using_gpt(table_name, schema_name, domain_context):
    """
    Generates a description for the table using GPT.
    """
    try:
        llm = ChatOpenAI(model_name="gpt-4", temperature=0.2)

        prompt = f"""
        {domain_context}

        The table `{schema_name}.{table_name}` does not have a description.
        Provide a concise and meaningful description for this table based on its name and domain.
        """

        response = llm([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        print(f"Error generating description for table {schema_name}.{table_name}: {e}")
        return "Auto-generated description not available"


def enrich_and_generate_all_schemas(db_config, table_list, domain_context, output_list):
    """
    Iterates over all tables, fetches schemas, and enriches with descriptions.
    """
    for table in table_list:
        schema_name, table_name = table.split('.')
        schema, table_description = fetch_table_schema(**db_config, schema_name=schema_name, table_name=table_name)

        # If table description is missing, generate it using GPT
        if not table_description:
            table_description = generate_table_description_using_gpt(table_name, schema_name, domain_context)

        # Enrich column descriptions using GPT if missing
        for column in schema:
            if not column["description"]:
                column["description"] = generate_description_using_gpt(
                    full_schema=schema,
                    column_name=column["column_name"],
                    data_type=column["data_type"],
                    table_name=table_name,
                    schema_name=schema_name,
                    domain_context=domain_context,
                    table_relationships="",
                )

        # Append enriched table schema to output
        output_list.append({
            "table_name": f"{schema_name}.{table_name}",
            "table_description": table_description,
            "columns": schema
        })


# Main Execution
db_config = {
    "dbname": "olist_ecommerce",
    "user": "root",
    "password": "",
    "host": "localhost",
    "port": "5432"
}

# Initialize output list
output_schemas = []

# Process e-commerce tables
enrich_and_generate_all_schemas(
    db_config=db_config,
    table_list=ECOMMERCE_TABLES,
    domain_context=DOMAIN_CONTEXT["ecommerce"],
    output_list=output_schemas
)

# Process marketing tables
enrich_and_generate_all_schemas(
    db_config=db_config,
    table_list=MARKETING_TABLES,
    domain_context=DOMAIN_CONTEXT["marketing"],
    output_list=output_schemas
)

# Print final enriched schemas
for table_info in output_schemas:
    print(f"Table: {table_info['table_name']}")
    print(f"Description: {table_info['table_description']}")
    print("Columns:")
    for column in table_info["columns"]:
        print(f"  - {column['column_name']} ({column['data_type']}): {column['description']}")
    print("\n")