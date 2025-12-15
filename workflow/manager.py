import boto3
import psycopg2
import yaml
import hashlib
import json
from psycopg2.extras import Json

class StorageManager:
   def __init__(self, db_config, s3_bucket_name):
       self.db_config = db_config
       self.bucket_name = s3_bucket_name
       # Initialize S3 Client
       self.s3_client = boto3.client('s3')

   def _get_db_conn(self):
       return psycopg2.connect(**self.db_config)

   def _generate_hash(self, cov_configuration):
       """
       Creates a stable SHA-256 hash of the configuration.
       sort_keys=True is vital for ensuring consistency.
       """
       yaml_str = yaml.dump(cov_configuration, sort_keys=True, default_flow_style=False)
       hash_id = hashlib.sha256(yaml_str.encode('utf-8')).hexdigest()
       return hash_id, yaml_str

   def save_snapshot(self, user_id, cov_configuration, meta=None):
       """
       Saves the config snapshot and logs the run event.
       Returns the unique Run ID.
       """
       config_hash, yaml_content = self._generate_hash(cov_configuration)
       s3_key = f"configs/{config_hash}.yaml"
       
       conn = self._get_db_conn()
       try:
           with conn:
               with conn.cursor() as cur:
                   # --- 1. Deduplication / Storage ---
                   # Check if this exact config has been seen before
                   cur.execute("SELECT 1 FROM model_configs WHERE config_hash = %s", (config_hash,))
                   if not cur.fetchone():
                       # It's new: Upload to S3
                       self.s3_client.put_object(
                           Bucket=self.bucket_name,
                           Key=s3_key,
                           Body=yaml_content,
                           ContentType='application/x-yaml'
                       )
                       # Register in DB
                       cur.execute("""
                           INSERT INTO model_configs (config_hash, s3_key, config_json)
                           VALUES (%s, %s, %s)
                       """, (config_hash, s3_key, Json(config_dict)))

                   # --- 2. Audit Logging ---
                   # Always log the run, even if the config is old
                   cur.execute("""
                       INSERT INTO model_runs (user_id, config_hash, meta_json)
                       VALUES (%s, %s, %s)
                       RETURNING run_id
                   """, (user_id, config_hash, Json(meta or {})))
                   
                   run_id = cur.fetchone()[0]
                   return run_id
       except Exception as e:
           print(f"Storage Error: {e}")
           raise
       finally:
           conn.close()

   def restore_snapshot(self, run_id):
       """
       Given a Run ID, retrieves the exact YAML configuration used.
       Prioritises the DB JSON for speed, falls back to S3 for raw file integrity.
       """
       conn = self._get_db_conn()
       try:
           with conn:
               with conn.cursor() as cur:
                   cur.execute("""
                       SELECT c.s3_key, c.config_json 
                       FROM model_runs r
                       JOIN model_configs c ON r.config_hash = c.config_hash
                       WHERE r.run_id = %s
                   """, (run_id,))
                   
                   result = cur.fetchone()
                   if not result:
                       raise ValueError(f"Run ID {run_id} not found.")
                   
                   s3_key, config_json = result

                   # OPTION A: Fast Return (Trust the DB)
                   if config_json:
                       return config_json
                   
                   # OPTION B: Integrity Return (Download from S3)
                   # Use this if config_json is empty or you need to verify the raw file
                   print(f"Fetching raw file from S3: {s3_key}")
                   response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                   yaml_content = response['Body'].read().decode('utf-8')
                   return yaml.safe_load(yaml_content)

       finally:
           conn.close()
