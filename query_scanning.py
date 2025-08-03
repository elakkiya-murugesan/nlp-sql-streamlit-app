from google.cloud import bigquery

def get_query_cost_estimate(query_sql: str, project_id: str) -> float:
    client = bigquery.Client(project=project_id)
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

    try:
        query_job = client.query(query_sql, job_config=job_config)
        if query_job.errors:
            print(f"Dry run failed with errors: {query_job.errors}")
            return None
        return query_job.total_bytes_processed
    except Exception as e:
        print(f"An error occurred during dry run: {e}")
        return None

def bytes_to_human_readable(bytes_value: int) -> str:
    """Converts bytes to a human-readable format (KB, MB, GB, TB)."""
    if bytes_value is None:
        return "N/A"
    
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"  
