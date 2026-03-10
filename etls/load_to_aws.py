"""
AWS Upload Module
Handles uploading data to S3 and creating Athena tables or loading to Redshift
"""

import boto3
import pandas as pd
from datetime import datetime
import os
from io import StringIO
import time


class AWSDataLoader:
    """
    Handles all AWS operations for the Shopify data pipeline
    """

    def __init__(self, aws_access_key=None, aws_secret_key=None, region=None, bucket_name=None):
        """
        Initialize AWS clients

        Args:
            aws_access_key: AWS Access Key ID
            aws_secret_key: AWS Secret Access Key
            region: AWS region (e.g., 'us-east-1')
            bucket_name: S3 bucket name
        """
        access_key_raw = aws_access_key or os.getenv('AWS_ACCESS_KEY_ID')
        secret_key_raw = aws_secret_key or os.getenv('AWS_SECRET_ACCESS_KEY')

        # Check for None just in case before stripping
        self.aws_access_key = access_key_raw.strip() if access_key_raw else None
        self.aws_secret_key = secret_key_raw.strip() if secret_key_raw else None

        # Region/Bucket can also be stripped for robustness
        self.region = (region or os.getenv('AWS_REGION', 'us-east-1')).strip()
        self.bucket_name = (bucket_name or os.getenv('S3_BUCKET_NAME')).strip()

        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )

        # Initialize Athena client (for querying S3 data)
        self.athena_client = boto3.client(
            'athena',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )

        # Initialize Glue client (for data catalog)
        self.glue_client = boto3.client(
            'glue',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )

        print(f"AWS clients initialized")
        print(f"   Region: {self.region}")
        print(f"   Bucket: {self.bucket_name}")

    def upload_to_s3(self, df, file_name, folder='raw'):
        """
        Upload DataFrame to S3 as CSV

        Args:
            df: pandas DataFrame
            file_name: Name for the file (without .csv)
            folder: Folder in bucket (e.g., 'raw', 'processed')

        Returns:
            str: S3 URI of uploaded file
        """
        try:
            # Add timestamp to filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            s3_key = f"{folder}/{file_name}_{timestamp}.csv"

            # Convert DataFrame to CSV string
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False, quoting=1)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=csv_buffer.getvalue(),
                ContentType='text/csv'
            )

            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            print(f"Uploaded to S3: {s3_uri}")

            return s3_uri

        except Exception as e:
            print(f"Error uploading to S3: {e}")
            raise

    def _wait_for_query(self, query_execution_id):
        """Wait for Athena query to complete"""
        max_wait = 30  # seconds
        wait_time = 0

        while wait_time < max_wait:
            result = self.athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            status = result['QueryExecution']['Status']['State']

            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                if status == 'FAILED':
                    reason = result['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
                    raise Exception(f"Query failed: {reason}")
                return status == 'SUCCEEDED'

            time.sleep(1)
            wait_time += 1

        raise Exception("Query timeout")

    def create_athena_database(self, database_name='shopify_data'):
        """
        Create Athena database if it doesn't exist

        Args:
            database_name: Name of the Athena database
        """
        try:
            query = f"CREATE DATABASE IF NOT EXISTS {database_name}"

            response = self.athena_client.start_query_execution(
                QueryString=query,
                ResultConfiguration={
                    'OutputLocation': f's3://{self.bucket_name}/athena-results/'
                }
            )

            self._wait_for_query(response['QueryExecutionId'])
            print(f"Athena database '{database_name}' ready")
            return database_name

        except Exception as e:
            print(f"Error creating Athena database: {e}")
            raise

    def create_athena_table(self, table_name, s3_location, database_name='shopify_data'):
        """
        Create external Athena table pointing to S3 data

        Args:
            table_name: Name of the table (WITHOUT database prefix)
            s3_location: S3 path where CSV files are stored (e.g., s3://bucket/folder/)
            database_name: Athena database name
        """
        try:
            # Table schemas for Athena - customize these based on your Shopify data needs
            # Add or remove columns to match the fields you extract from the Shopify API
            if 'orders' in table_name.lower():
                schema = """
                    id BIGINT,
                    email STRING,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    total_price DOUBLE,
                    subtotal_price DOUBLE,
                    total_tax DOUBLE,
                    financial_status STRING,
                    fulfillment_status STRING
                """
            elif 'products' in table_name.lower():
                schema = """
                    product_id BIGINT,
                    product_title STRING,
                    variant_id BIGINT,
                    variant_title STRING,
                    sku STRING,
                    price DOUBLE,
                    inventory_quantity INT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                """
            elif 'customers' in table_name.lower():
                schema = """
                    customer_id BIGINT,
                    email STRING,
                    first_name STRING,
                    last_name STRING,
                    orders_count INT,
                    total_spent DOUBLE,
                    state STRING,
                    tags STRING,
                    city STRING,
                    province STRING,
                    country STRING,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                """
            elif 'line_items' in table_name.lower():
                schema = """
                    order_id BIGINT,
                    order_created_at TIMESTAMP,
                    order_email STRING,
                    financial_status STRING,
                    fulfillment_status STRING,
                    line_item_id BIGINT,
                    product_id BIGINT,
                    variant_id BIGINT,
                    product_title STRING,
                    variant_title STRING,
                    sku STRING,
                    quantity INT,
                    price DOUBLE,
                    total_discount DOUBLE,
                    line_total DOUBLE
                """

            else:
                schema = None

            drop_query = f"DROP TABLE IF EXISTS {table_name}"

            response = self.athena_client.start_query_execution(
                QueryString=drop_query,
                QueryExecutionContext={'Database': database_name},
                ResultConfiguration={
                    'OutputLocation': f's3://{self.bucket_name}/athena-results/'
                }
            )

            self._wait_for_query(response['QueryExecutionId'])

            if schema:
                create_query = f"""
                CREATE EXTERNAL TABLE IF NOT EXISTS {table_name} (
                    {schema}
                )
                ROW FORMAT DELIMITED
                FIELDS TERMINATED BY ','
                STORED AS TEXTFILE
                LOCATION '{s3_location}'
                TBLPROPERTIES ('skip.header.line.count'='1')
                """
            else:
                create_query = f"""
                CREATE EXTERNAL TABLE IF NOT EXISTS {table_name}
                ROW FORMAT DELIMITED
                FIELDS TERMINATED BY ','
                STORED AS TEXTFILE
                LOCATION '{s3_location}'
                TBLPROPERTIES ('skip.header.line.count'='1')
                """

            response = self.athena_client.start_query_execution(
                QueryString=create_query,
                QueryExecutionContext={'Database': database_name},
                ResultConfiguration={
                    'OutputLocation': f's3://{self.bucket_name}/athena-results/'
                }
            )

            self._wait_for_query(response['QueryExecutionId'])
            print(f"Created Athena table: {database_name}.{table_name}")
            print(f"   Location: {s3_location}")

            return response['QueryExecutionId']

        except Exception as e:
            print(f"Error creating Athena table: {e}")
            raise

    def upload_dataframe_to_athena(self, df, table_name, folder='raw', database_name='shopify_data'):
        """
        Complete pipeline: DataFrame → S3 → Athena Table

        Args:
            df: pandas DataFrame
            table_name: Table name for Athena (without database prefix)
            folder: S3 folder
            database_name: Athena database name

        Returns:
            tuple: (s3_uri, full_table_name)
        """
        try:
            print(f"\n{'=' * 70}")
            print(f"Uploading {len(df)} rows to Athena table: {table_name}")
            print(f"{'=' * 70}")

            # Step 1: Ensure database exists
            self.create_athena_database(database_name)

            # Step 2: Upload to S3
            s3_uri = self.upload_to_s3(df, table_name, folder)

            # Step 3: Get S3 folder location (without filename)
            s3_folder = f"s3://{self.bucket_name}/{folder}/"

            # Step 4: Create Athena table
            self.create_athena_table(table_name, s3_folder, database_name)

            full_table_name = f"{database_name}.{table_name}"

            print(f"{'=' * 70}")
            print(f"SUCCESS! Data available in Athena")
            print(f"   Table: {full_table_name}")
            print(f"   Rows: {len(df)}")
            print(f"   Query in Athena: SELECT * FROM {full_table_name} LIMIT 10;")
            print(f"{'=' * 70}\n")

            return s3_uri, full_table_name

        except Exception as e:
            print(f"Error in upload pipeline: {e}")
            raise

    def query_athena(self, query, database_name='shopify_data'):
        """
        Execute a query in Athena and return results as DataFrame

        Args:
            query: SQL query string
            database_name: Athena database name

        Returns:
            pandas DataFrame with query results
        """
        try:
            response = self.athena_client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': database_name},
                ResultConfiguration={
                    'OutputLocation': f's3://{self.bucket_name}/athena-results/'
                }
            )

            query_execution_id = response['QueryExecutionId']

            # Wait for query to complete
            self._wait_for_query(query_execution_id)

            # Get results
            result = self.athena_client.get_query_results(
                QueryExecutionId=query_execution_id
            )

            # Convert to DataFrame
            columns = [col['Label'] for col in result['ResultSet']['ResultSetMetadata']['ColumnInfo']]
            rows = []

            for row in result['ResultSet']['Rows'][1:]:  # Skip header
                rows.append([field.get('VarCharValue', '') for field in row['Data']])

            df = pd.DataFrame(rows, columns=columns)
            print(f"Query returned {len(df)} rows")
            return df

        except Exception as e:
            print(f"Error querying Athena: {e}")
            raise

    # In load_to_aws.py (Add this method inside the AWSDataLoader class)
        # In load_to_aws.py (Inside class AWSDataLoader)

    def execute_athena_query(self, query_string, database_name='shopify_data'):
        """
        Executes a non-SELECT Athena query (DDL like CREATE/DROP TABLE).
        """
        try:
            response = self.athena_client.start_query_execution(
                QueryString=query_string,
                QueryExecutionContext={'Database': database_name},
                ResultConfiguration={
                    'OutputLocation': f's3://{self.bucket_name}/athena-results/'
                }
            )
            query_execution_id = response['QueryExecutionId']

            # Wait for query to complete (assumes _wait_for_query is already defined)
            self._wait_for_query(query_execution_id)
            print(f"Successfully executed Athena query: {query_string.splitlines()[1].strip()}...")
            return query_execution_id
        except Exception as e:
            print(f"Error executing Athena query: {e}")
            raise

    def create_athena_table_dynamic(self, df_schema, table_name, database, s3_path):
        """
        Creates an external Athena table using dynamic schema based on Pandas dtypes.
        """

        # 1. Define Athena SQL type mapping from Pandas dtype
        def pandas_to_athena_type(dtype):
            if 'int' in str(dtype):
                return 'INT'
            if 'float' in str(dtype):
                return 'DOUBLE'
            if 'datetime' in str(dtype):
                return 'TIMESTAMP'
            return 'STRING'

        # 2. Build the COLUMN definitions
        column_defs = []
        for col, dtype in df_schema.items():
            athena_type = pandas_to_athena_type(dtype)
            # Ensure column names are Athena-safe
            safe_col = col.lower().replace('.', '_').replace('-', '_').strip()
            column_defs.append(f"{safe_col} {athena_type}")

        columns_sql = ',\n    '.join(column_defs)

        # 3. Construct the CREATE TABLE statement
        create_table_sql = f"""
            CREATE EXTERNAL TABLE IF NOT EXISTS {database}.{table_name} (
                {columns_sql}
            )
            ROW FORMAT DELIMITED
            FIELDS TERMINATED BY ','
            STORED AS PARQUET
            LOCATION '{s3_path}/'
            TBLPROPERTIES ('classification'='csv', 'skip.header.line.count'='1')
        """

        # 4. Execute the query
        print(f"Creating Athena Table: {database}.{table_name} (Dynamic Schema)")
        self.execute_athena_query(create_table_sql)
        print("Athena table created/verified.")

        return True  # Return success


def load_data_to_aws(df, file_name, folder='raw'):
    """
    Convenience function to load DataFrame to AWS
    Uses environment variables for credentials

    Args:
        df: pandas DataFrame
        file_name: Name for the file/table
        folder: S3 folder (raw/processed)
    """
    loader = AWSDataLoader()
    return loader.upload_dataframe_to_athena(df, file_name, folder)