from google import genai
from google.genai import types

project_id = "bigquery-public-data"
model = "gemini-2.0-flash-001"

client = genai.Client(project=project_id, location="global", vertexai=True)

generate_content_config = types.GenerateContentConfig(
    temperature = 0,
    top_p = 1,
    seed = 0,
    max_output_tokens = 1000,
    safety_settings = [types.SafetySetting(
      category="HARM_CATEGORY_HATE_SPEECH",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_DANGEROUS_CONTENT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_HARASSMENT",
      threshold="OFF"
    )],
  )


def insights(question,df_json):
    instruction = f"""You are an advanced data analysis assistant. Your task is to analyze the provided JSON dataset and generate insights based on the user's question.

**Instructions**:
1. Carefully review the dataset provided in JSON format.
2. Ensure your analysis directly addresses the user's question.
3. Provide accurate, concise, and actionable insights based on the data.
4. If relevant, include statistics, trends, or patterns observed in the dataset.

**Column Descriptions (from bigquery-public-data.san_francisco_311.311_service_requests)**:
- service_request_id (STRING): Unique identifier for the request
- status (STRING): Current status of the request (e.g., open, closed)
- status_notes (STRING): Additional status details
- agency_responsible (STRING): Department handling the request
- service_name (STRING): Type of city service requested
- service_subtype (STRING): More specific category of the request
- requested_datetime (TIMESTAMP): Time when the request was created
- updated_datetime (TIMESTAMP): Last update timestamp
- expected_datetime (TIMESTAMP): Expected resolution date
- closed_date (TIMESTAMP): When the request was marked as closed
- address (STRING): Request location
- street (STRING): Street name
- supervisor_district (STRING): Supervisor district of the address
- neighborhood (STRING): Neighborhood in San Francisco
- point (GEOGRAPHY): Geographical coordinates
- source (STRING): How the request was submitted (e.g., mobile app, phone)
- media_url (STRING): Link to media related to the request
- lat (FLOAT64): Latitude
- long (FLOAT64): Longitude
- created_at (TIMESTAMP): When the record was added
- closed_at (TIMESTAMP): When the request was closed (duplicate of closed_date)

**User's Question**:
{question}

**JSON Dataset**:
{df_json}

**Output Format**:
Provide the insights as a clear and concise explanation in natural language. Do **not** mention phrases like “based on the provided JSON data.” Just write the insight directly. Always mention units such as dates or counts wherever relevant.
"""

    full_prompt = instruction + "\n\n Generate insigths."
    contents = [
    {
        "role": "user",
        "parts": [{"text": full_prompt}]
    }]
    response = client.models.generate_content(
        contents=contents,
        model=model,
        config=generate_content_config
    )
    response_text = response.text
    return response_text
