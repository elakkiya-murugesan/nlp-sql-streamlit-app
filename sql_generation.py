from google.cloud import bigquery
from google import genai
from google.genai import types
import json

# Set the public dataset details
project_id = "bigquery-public-data"
dataset_id = "san_francisco_311"
table_name = "311_service_requests"

model = "gemini-2.0-flash-001" 

client = genai.Client(project=project_id, location="global", vertexai=True)


def get_bigquery_table_schema_text():
    bq_client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_name}"
    table = bq_client.get_table(table_ref)
    schema_text = f"Table: {table.table_id}\n"
    for column in table.schema:
        schema_text += f"    - {column.name} ({column.field_type})\n"
    return schema_text

def get_sample_rows(limit=10):
    bq_client = bigquery.Client(project=project_id)
    query = f"SELECT * FROM `{project_id}.{dataset_id}.{table_name}` LIMIT {limit}"
    rows = bq_client.query(query).result()
    return json.dumps([dict(row) for row in rows], indent=2, default=str)



def generate_sql(question: str):
    schema = get_bigquery_table_schema_text()
    sample_rows = get_sample_rows()

    instruction =  f"""You are a BigQuery SQL generator.

Your task is to convert natural language questions into valid BigQuery SQL queries using the dataset:
`bigquery-public-data.san_francisco_311.311_service_requests`


### Instructions:

1. **Understand the intent** of the user — e.g., count, group by, filter, compare, sort.
2. **Generate a syntactically correct BigQuery SQL query** based on the user's request.
3. Use the correct **field names** and **functions** (e.g., `EXTRACT(DATE FROM...)`, `TIMESTAMP_DIFF`, `COUNT`, etc.).
4. Include **LIMIT 100** by default unless the user specifies otherwise.
5. Handle time filtering using `created_at` (request timestamp) and `closed_date` (resolution timestamp).
6. Use `service_subtype` or `service_name` for request types like potholes, graffiti, noise, etc.
7. Use `agency_responsible`, `status`, and `source` as needed.
8. Do not hallucinate fields that don’t exist.


### Field Reference (partial):

- `service_request_id`: unique request ID  
- `service_name`: high-level service category (e.g., "Street and Sidewalk")  
- `service_subtype`: specific issue (e.g., "Pothole")  
- `created_at`: when the request was made  
- `closed_date`: when the request was resolved  
- `status`: request status ("Open", "Closed", etc.)  
- `agency_responsible`: agency assigned to the request  
- `source`: submission channel ("Mobile App", "Phone", etc.)  
- `neighborhood`: name of the neighborhood  
- `address`: address of the request  
- `lat` and `long`: coordinates


### Examples:

**Input:** "Which neighborhood had the most pothole complaints last year?"  
**Output:**
```sql
SELECT neighborhood, COUNT(*) AS pothole_requests
FROM `bigquery-public-data.san_francisco_311.311_service_requests`
WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE()) - 1
  AND LOWER(service_subtype) LIKE '%pothole%'
GROUP BY neighborhood
ORDER BY pothole_requests DESC
LIMIT 100
"""

 
    generate_content_config = types.GenerateContentConfig(
        temperature=0.3,
        top_p=1,
        max_output_tokens=8000,
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
        system_instruction=[types.Part.from_text(text=instruction)],
    )

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=question)]
        )
    ]
  
    response = client.models.generate_content(contents=contents, config=generate_content_config, model=model)
    sql_query = response.text.strip()
    return sql_query.replace("```sql", "").replace("```", "").strip()
