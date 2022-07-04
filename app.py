import os, logging, json, time, boto3, psycopg2
from botocore.exceptions import ClientError
from psycopg2 import Error

AWS_REGION = os.getenv('AWS_REGION')
PSQL_USER = os.getenv('PSQL_USER')
PSQL_PASSWORD = os.getenv('PSQL_PASSWORD')
PSQL_HOST = os.getenv('PSQL_HOST')
PSQL_PORT = os.getenv('PSQL_PORT')
PSQL_DATABASE = os.getenv('PSQL_DATABASE')

# logger config
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s')

sqs_client = boto3.client("sqs", region_name=AWS_REGION)

def get_no_messages(queue_url):
    try:
        response = sqs_client.get_queue_attributes(QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages'])
    except ClientError:
        logger.exception(
            f'Could not receive the queue attribute from the - {queue_url}.')
        raise
    else:
        return int(response['Attributes']['ApproximateNumberOfMessages'])

def receive_queue_message(queue_url):
    try:
        response = sqs_client.receive_message(QueueUrl=queue_url)
    except ClientError:
        logger.exception(
            f'Could not receive the message from the - {queue_url}.')
        raise
    else:
        return response

def delete_queue_message(queue_url, receipt_handle):
    try:
        response = sqs_client.delete_message(QueueUrl=queue_url,
                                             ReceiptHandle=receipt_handle)
    except ClientError:
        logger.exception(
            f'Could not delete the meessage from the - {queue_url}.')
        raise
    else:
        return response

def connect_database(user, password, host, port, database):
    try:
        connection = psycopg2.connect(user=user, password=password, host=host,
                                    port=port, database=database)
        return connection
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)

def create_table():
    connection = connect_database(PSQL_USER, PSQL_PASSWORD, PSQL_HOST, PSQL_PORT,
        PSQL_DATABASE)
    cursor = connection.cursor()
    create_table_query = """CREATE TABLE IF NOT EXISTS items
        (ID TEXT PRIMARY KEY     NOT NULL,
        NAME            TEXT    NOT NULL,
        QUANTITY        INT);"""
    cursor.execute(create_table_query)
    connection.commit()

    insert_data = """INSERT INTO items (ID, NAME, QUANTITY) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;"""
    item_tuple = ('2', 'apple', 1)
    cursor.execute(insert_data, item_tuple)
    connection.commit()
    if connection:
        cursor.close()
        connection.close()

def insert_data(data):
    connection = connect_database(PSQL_USER, PSQL_PASSWORD, PSQL_HOST, PSQL_PORT,
        PSQL_DATABASE)
    cursor = connection.cursor()
    insert_query = """INSERT INTO items (ID, NAME, QUANTITY) VALUES (%s, %s, %s);"""
    item_tuple = (data['client_timestamp'], data['item'], data['quantity'])
    cursor.execute(insert_query, item_tuple)
    connection.commit()
    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")

if __name__ == '__main__':
    # CONSTANTS
    QUEUE_URL = os.getenv('QUEUE_URL')
    create_table()
    while True:
        if (get_no_messages(QUEUE_URL) > 5):
            messages = receive_queue_message(QUEUE_URL)
            for msg in messages['Messages']:
                msg_body = msg['Body']
                receipt_handle = msg['ReceiptHandle']
                data = json.loads(msg_body)
                try:
                    insert_data(data)
                except Exception as e:
                    print(f"exception while processing message: {repr(e)}")
                    continue
            logger.info(f'The message body: {msg_body}')
            logger.info('Deleting message from the queue...')
            delete_queue_message(QUEUE_URL, receipt_handle)
            logger.info(f'Received and deleted message(s) from {QUEUE_URL}.')
        
        time.sleep(10)