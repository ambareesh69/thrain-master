from google.cloud import storage

# Function to upload file to GCS
def upload_to_gcs(local_file_path, bucket_name, gcs_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(gcs_file_name)
    blob.upload_from_filename(local_file_path)

    return f'gs://{bucket_name}/{gcs_file_name}'

