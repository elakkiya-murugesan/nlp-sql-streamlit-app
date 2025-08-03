from google import genai
from google.genai import types

project_id = "bigquery-public-data"
model = "gemini-2.0-flash-001" 
# model= "gemini-2.5-pro-preview-06-05"

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
    response_mime_type = "application/json"
  )


def simplify_query(user_query: str, schema: str):
    instruction = f"""You are a Query Simplifier. Your task is to take a natural language user query and convert it into a concise, unambiguous version suitable for generating SQL.

Follow these steps:

1. Identify the **intent** of the query (e.g., count, compare, retrieve).
2. Determine the **target entity** (e.g., request type, neighborhood, agency).
3. Extract any **filters or constraints** (e.g., time range, specific values).
4. Translate the natural phrasing into a format that uses **clear and analytical language**.
5. Ensure the final query is **complete, logical, and easily translatable to SQL**.

User Query:
{user_query}

You have access to this dataset:
`bigquery-public-data.san_francisco_311.311_service_requests`

**Important Rules**:
- Use `requested_datetime` for date filtering or extracting components (day, hour, month).
- Use `neighborhood` for location-specific analysis.
- Do not include actual column names in the simplified query.
- Simplify the query in a way that's **logical and easy for an LLM to convert into SQL**.

**Examples**:

Input: "Which neighborhood had the most complaints in January 2023?"
→ simplified_user_query: "Find the neighborhood with the highest number of service requests in January 2023"

Input: "Compare number of street cleaning complaints vs pothole repair in 2022"
→ simplified_user_query: "Compare the total number of street cleaning and pothole repair requests in 2022"

Input: "When do most noise complaints occur during the day?"
→ simplified_user_query: "Find the hour of the day when noise complaints are most frequent"

Input: "List agencies with the longest average resolution time"
→ simplified_user_query: "Find agencies ranked by average time taken to resolve service requests"

Return result as:
{{"simplified_user_query": "final-simplified-query"}}
"""

    full_prompt = instruction + "\n\n simplify the user query."
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
    print(response_text)
    return response_text
