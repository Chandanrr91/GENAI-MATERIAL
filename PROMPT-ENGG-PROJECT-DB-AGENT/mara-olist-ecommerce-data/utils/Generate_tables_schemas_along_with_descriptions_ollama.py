# import psycopg2
# import requests
# import json
#
# # Ollama API endpoint
# OLLAMA_API_URL = "http://localhost:11434/api/generate"
#
# # Domain-Specific Contexts
# DOMAIN_CONTEXT = {
#     "ecommerce": """
#     This database contains tables related to an e-commerce platform. Common entities include:
#     - Customers (user details, orders, addresses, preferences)
#     - Orders (products, payments, shipping info, reviews)
#     - Products (categories, pricing, inventory, sellers)
#     - Transactions (payments, refunds)
#     - Locations (geographical details of customers and sellers)
#     """,
#     "marketing": """
#     This database contains tables related to a marketing platform. Common entities include:
#     - Leads (prospective customers for marketing campaigns)
#     - Deals (closed sales or business deals resulting from marketing efforts)
#     """
# }
#
# # Table Categories
# ECOMMERCE_TABLES = ['ecommerce.customers', 'ecommerce.geolocation', 'ecommerce.order_items',
#                     'ecommerce.order_payments', 'ecommerce.order_reviews', 'ecommerce.orders',
#                     'ecommerce.products', 'ecommerce.sellers', 'ecommerce.product_category_name_translations']
#
# MARKETING_TABLES = ['marketing.closed_deals', 'marketing.marketing_qualified_leads']
#
#
# def fetch_table_schema(dbname, user, password, host, port, schema_name, table_name):
#     """
#     Fetches schema (column names, data types, and descriptions) from PostgreSQL.
#     """
#     try:
#         conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
#         cursor = conn.cursor()
#
#         # Query to fetch column details and descriptions
#         cursor.execute("""
#             SELECT
#                 cols.column_name,
#                 cols.data_type,
#                 pgdesc.description
#             FROM information_schema.columns cols
#             LEFT JOIN pg_catalog.pg_class pgclass
#                 ON cols.table_name = pgclass.relname
#             LEFT JOIN pg_catalog.pg_namespace pgns
#                 ON pgclass.relnamespace = pgns.oid
#             LEFT JOIN pg_catalog.pg_attribute pgattr
#                 ON pgclass.oid = pgattr.attrelid
#                 AND cols.column_name = pgattr.attname
#             LEFT JOIN pg_catalog.pg_description pgdesc
#                 ON pgattr.attrelid = pgdesc.objoid
#                 AND pgattr.attnum = pgdesc.objsubid
#             WHERE cols.table_schema = %s
#               AND cols.table_name = %s
#         """, (schema_name, table_name))
#
#         schema = [{"column_name": col, "data_type": dtype, "description": desc if desc else None}
#                   for col, dtype, desc in cursor.fetchall()]
#
#         # Fetch table description if available
#         cursor.execute("""
#             SELECT obj_description(pgclass.oid, 'pg_class')
#             FROM pg_catalog.pg_class pgclass
#             JOIN pg_catalog.pg_namespace pgns
#                 ON pgclass.relnamespace = pgns.oid
#             WHERE pgns.nspname = %s
#               AND pgclass.relname = %s
#         """, (schema_name, table_name))
#         table_description = cursor.fetchone()
#         table_description = table_description[0] if table_description and table_description[0] else None
#
#         cursor.close()
#         conn.close()
#
#         return schema, table_description
#
#     except Exception as e:
#         print(f"Error fetching schema for {schema_name}.{table_name}: {e}")
#         return None, None
#
#
# def generate_description_using_ollama(prompt):
#     """
#     Sends a prompt to Ollama and retrieves the complete response as a single JSON.
#     """
#     try:
#         response = requests.post(
#             OLLAMA_API_URL,
#             json={
#                 "model": "llama2",
#                 "prompt": prompt,
#                 "stream": False,
#                 "temperature": 0.3,  # Force deterministic responses
#                 "max_tokens": 100  # Limit response length to avoid verbosity
#             }
#         )
#         response.raise_for_status()
#         print(response.text)
#         response_json = response.json()
#         return response_json.get("response", "No response content available").strip()
#
#     except Exception as e:
#         print(f"Error generating description using Ollama: {e}")
#         return "Auto-generated description not available"
#
#
# def enrich_and_generate_all_schemas(db_config, table_list, domain_context, output_list):
#     """
#     Iterates over all tables, fetches schemas, and enriches with descriptions.
#     """
#     for table in table_list:
#         schema_name, table_name = table.split('.')
#         schema, table_description = fetch_table_schema(**db_config, schema_name=schema_name, table_name=table_name)
#
#         # Generate table description using Ollama if missing
#         if not table_description:
#             table_description_prompt = f"""
#             {domain_context}
#
#             Define the purpose of the `{schema_name}.{table_name}` table in a **concise, technical, and professional** manner.
#             - Explain what data it stores and how it's used.
#             - Keep it structured and to the point.
#             - Avoid redundant phrases like 'this table stores...' and focus on its business significance.
#             """
#             table_description = generate_description_using_ollama(table_description_prompt)
#
#         # Enrich column descriptions using Ollama if missing
#         for column in schema:
#             if not column["description"]:
#                 column_description_prompt = f"""
#                 {domain_context}
#
#                 The `{schema_name}.{table_name}` table contains these columns:
#                 {', '.join([f'{col["column_name"]} ({col["data_type"]})' for col in schema])}.
#
#                 Describe the **column `{column["column_name"]}`** (data type: `{column["data_type"]}`):
#                 - Explain its **role** in the table.
#                 - Keep it **concise** and **to the point**.
#                 - Avoid redundant phrases like 'this column stores...'
#                 """
#                 column["description"] = generate_description_using_ollama(column_description_prompt)
#
#         output_list.append({
#             "table_name": f"{schema_name}.{table_name}",
#             "table_description": table_description,
#             "columns": schema
#         })
#
#
# def save_output_to_json(output_schemas, file_path):
#     """
#     Saves the enriched schema output to a JSON file.
#     """
#     try:
#         with open(file_path, "w") as json_file:
#             json.dump(output_schemas, json_file, indent=4)
#         print(f"Schema saved successfully to {file_path}")
#     except Exception as e:
#         print(f"Error saving schema to JSON: {e}")
#
#
# # Main Execution
# db_config = {
#     "dbname": "olist_ecommerce",
#     "user": "root",
#     "password": "",
#     "host": "localhost",
#     "port": "5432"
# }
#
# # Initialize output list
# output_schemas = []
#
# # Process e-commerce tables
# enrich_and_generate_all_schemas(
#     db_config=db_config,
#     table_list=ECOMMERCE_TABLES,
#     domain_context=DOMAIN_CONTEXT["ecommerce"],
#     output_list=output_schemas
# )
#
# # Process marketing tables
# enrich_and_generate_all_schemas(
#     db_config=db_config,
#     table_list=MARKETING_TABLES,
#     domain_context=DOMAIN_CONTEXT["marketing"],
#     output_list=output_schemas
# )
#
# # Save enriched schemas to JSON
# save_output_to_json(output_schemas, "enriched_schemas.json")
#
# print("Schema enrichment and saving complete!")
#----- updated version
import psycopg2
import requests
import json

# Ollama API endpoint for LLM-powered description generation
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Domain-Specific Contexts (Predefined Knowledge for LLM)
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

# List of Tables for Different Domains
ECOMMERCE_TABLES = [
    'ecommerce.customers', 'ecommerce.geolocation', 'ecommerce.order_items',
    'ecommerce.order_payments', 'ecommerce.order_reviews', 'ecommerce.orders',
    'ecommerce.products', 'ecommerce.sellers', 'ecommerce.product_category_name_translations'
]

MARKETING_TABLES = ['marketing.closed_deals', 'marketing.marketing_qualified_leads']


def fetch_table_schema(dbname, user, password, host, port, schema_name, table_name):
    """
    Fetches the schema details of a table from PostgreSQL.

    Args:
        dbname (str): Database name.
        user (str): Username for authentication.
        password (str): Password for authentication.
        host (str): Database host.
        port (str): Database port.
        schema_name (str): Schema containing the table.
        table_name (str): Table name for which schema is required.

    Returns:
        tuple: A list of column details (column_name, data_type, description) and a table description.
    """
    try:
        # Establish PostgreSQL connection
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = conn.cursor()

        # Fetch column details (column name, data type, and description if available)
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

        # Store retrieved column details in a structured format
        schema = [{"column_name": col, "data_type": dtype, "description": desc if desc else None}
                  for col, dtype, desc in cursor.fetchall()]

        # Fetch table-level description if available
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

        # Close DB connection
        cursor.close()
        conn.close()

        return schema, table_description

    except Exception as e:
        print(f"❌ Error fetching schema for {schema_name}.{table_name}: {e}")
        return None, None


def generate_description_using_ollama(prompt):
    """
    Uses Ollama's API to generate descriptions for tables or columns.

    Args:
        prompt (str): The prompt containing details of what needs to be described.

    Returns:
        str: The generated description or an error message if API fails.
    """
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": "llama2",
                "prompt": prompt,
                "stream": False,  # Ensure the response is not streamed
                "temperature": 0.3,  # Make responses deterministic
                "max_tokens": 100  # Limit response length to avoid unnecessary verbosity
            }
        )
        response.raise_for_status()
        response_json = response.json()
        return response_json.get("response", "No response content available").strip()

    except Exception as e:
        print(f"❌ Error generating description using Ollama: {e}")
        return "Auto-generated description not available"


def enrich_and_generate_all_schemas(db_config, table_list, domain_context, output_list):
    """
    Iterates over all tables, fetches schemas, and enriches with AI-generated descriptions.

    Args:
        db_config (dict): Database connection details.
        table_list (list): List of tables to process.
        domain_context (str): Domain-specific context to assist the LLM in generating relevant descriptions.
        output_list (list): List to store enriched schema details.
    """
    for table in table_list:
        schema_name, table_name = table.split('.')
        schema, table_description = fetch_table_schema(**db_config, schema_name=schema_name, table_name=table_name)

        # Generate table description using Ollama if missing
        if not table_description:
            table_description_prompt = f"""
            {domain_context}

            Define the purpose of the `{table_name}` table in a **concise and structured** manner.
            - Explain what data it holds and how it is used.
            - Avoid redundant phrases like 'this table stores...' and focus on its significance.
            
            """
            table_description = generate_description_using_ollama(table_description_prompt)

        # Enrich column descriptions using Ollama if missing
        for column in schema:
            if not column["description"]:
                column_description_prompt = f"""
                {domain_context}

                The `{table_name}` table contains these columns:
                {', '.join([f'{col["column_name"]} ({col["data_type"]})' for col in schema])}.

                Describe **{column["column_name"]}** ({column["data_type"]}):
                - Explain its **role** in the table.
                - Keep it **concise** and **to the point**.
                - Avoid redundant phrases like 'this column stores...'
                """
                column["description"] = generate_description_using_ollama(column_description_prompt)

        output_list.append({
            "table_name": f"{schema_name}.{table_name}",
            "table_description": table_description,
            "columns": schema
        })


def save_output_to_json(output_schemas, file_path):
    """
    Saves the enriched schema output to a JSON file.

    Args:
        output_schemas (list): List of enriched schemas.
        file_path (str): Path where the JSON file will be saved.
    """
    try:
        with open(file_path, "w") as json_file:
            json.dump(output_schemas, json_file, indent=4)
        print(f"✅ Schema saved successfully to {file_path}")
    except Exception as e:
        print(f"❌ Error saving schema to JSON: {e}")


# Main Execution Configuration
db_config = {
    "dbname": "olist_ecommerce",
    "user": "root",
    "password": "",
    "host": "localhost",
    "port": "5432"
}

# Initialize Output List
output_schemas = []

# Process Tables
enrich_and_generate_all_schemas(db_config, ECOMMERCE_TABLES, DOMAIN_CONTEXT["ecommerce"], output_schemas)
enrich_and_generate_all_schemas(db_config, MARKETING_TABLES, DOMAIN_CONTEXT["marketing"], output_schemas)

# Save Enriched Schema to JSON
save_output_to_json(output_schemas, "enriched_schemas.json")

print("✅ Schema enrichment and saving complete!")