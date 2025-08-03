from google import genai
from google.genai import types
import plotly.express as px
import ast 
import pandas as pd

project_id = "bigquery-public-data"
model = "gemini-2.0-flash-001"

client = genai.Client(project=project_id, location="global", vertexai=True)

def generate_chart_suggestion(df_head: str, df_dtypes: str,user_query: str,insight:str):
    prompt =f"""
You are a data visualization expert.

Your task is to recommend the most appropriate chart type for visualizing the given data extracted from a BigQuery query.

Use the information below:

1. User Query:
{user_query}

2. Sample Rows (first few rows of the result dataframe):
{df_head}

3. Column Types (data types for each column):
{df_dtypes}

---------------------
Instructions:
WHEN THE DATA CONTAINS ONLY ONE QUANTITY WHICH DOESNT NEED VISUALISATION DONT GIVE VISUALISATION JUST RETURN VISUALISATION NOT NEEDED 

1. Understand the user's intent by analyzing the query.
2. Use the sample data and column types to determine which chart type best conveys the user's intent.
3. Only choose from the following chart types:
   - bar
   - line
   - scatter
   - pie
   - histogram
   - stacked_doughnut

4. Use these rules to guide chart type selection:
   -  **Bar chart** → When comparing values across categories (e.g., compare averages, totals for different houses, dates, actions).
   -  **Line chart** → When analyzing trends over time (e.g., months, days, timestamps).
   -  **Scatter plot** → When showing the relationship or correlation between two numerical variables.
   -  **Pie chart** → When showing proportions of a whole using categorical + numeric data (e.g., % share by category).
   -  **Histogram** → When analyzing the distribution of a single numeric column (e.g., time durations, age, scores).

5. Additional rule for comparisons:
   - If the user asks to **compare two or more values**, prefer a **bar chart** or **histogram**.
   - If the user asks to **show trends or progression over time**, use a **line chart**.

6. Column selection guidance:
   - For **bar, line, scatter**: select an X-axis (typically a category or time) and a Y-axis (numeric value).
   - For **pie and histogram**: specify the single column to be used as **Values**.
7. For binary or grouped category comparisons:
   - When the user query or sample data involves comparing two or more categories (e.g., 'dishcloth' vs 'hand' usage) **within the same group** (e.g., a household or location), choose a **bar chart** or **histogram**.
   - This helps to visually highlight significant differences or preferences.
   - Example: If usage values like 'dishcloth': 201 and 'hand': 15 appear, return a bar chart with the categories on the X-axis and the usage values on the Y-axis.
8. **Comparison-focused queries:**
Use **bar** or **histogram** charts when the user asks to compare two or more values:
- Comparing two categories (e.g., dishcloth vs hand) →  **Bar chart**
- Comparing usage across multiple types or locations →  **Bar chart**
- Comparing distributions or frequency of a numeric column →  **Histogram**
Examples:
- "Compare dishcloth vs hand usage in Adonia D" → **Bar chart**  
- "Show wiping time distribution across houses" → **Bar chart**  
- "Compare number of tasks across rooms" → **Bar chart**  
- "Show distribution of total cleaning time" → **Histogram**

9. **Trend-focused queries:**
Use a **line chart** when analyzing change over time:
- Monthly, daily, weekly changes
- Timestamp-based values
- Trend of a metric over time

Examples:
- "How has wiping time changed from Jan to March?" → **Line chart**  
- "Show monthly dishcloth usage" → **Line chart**

10. **Correlation-focused queries:**
Use a **scatter plot** when showing relationships between two numeric variables:
- Performance vs time
- Usage vs cost
- Duration vs count
Examples:
- "Show relationship between number of tasks and duration" → **Scatter plot**

11. **Proportion-focused queries:**
Use a **pie chart** when showing parts of a whole using categorical + numeric data:
- Proportion of total tasks by room
- Usage share across categories

Examples:
- "Show share of cleaning tools used in a house" → **Pie chart**

12. **Distribution of single numeric column:**
Use a **histogram** when analyzing how values are distributed:
- Time durations
- Counts
- Scores
Examples:
- "Show distribution of wiping times" → **Histogram**

13. If the data has multiple columns representing different categories or time periods (e.g., 'avg_duration_may', 'avg_duration_jan'), and a single row:
   - Treat column names as categorical values on the X-axis.
   - Use their corresponding values as Y-axis values.
   - Use a **bar chart** to visualize them.
   - The X-axis should represent the column names (e.g., 'May', 'Jan'), not a literal 'month' column.
Examples:
- If Chart type is bar → X-axis = ['May', 'Jan'], Y-axis = [296.53, 273.90], Values = N/A

14.If a single-row result contains multiple numeric columns representing categories or time periods (e.g., avg_duration_jan, avg_duration_may):
- Treat column names as X-axis categories.
- Use their corresponding values as Y-axis.
- Use a bar chart for side-by-side comparison.
- Format output with actual values in Y-axis (not a column name).

15. **Stacked Doughnut (Sunburst Chart)**:
Use this when the data has **hierarchical categorical structure** — e.g., category → sub-category → sub-sub-category — and a corresponding numeric value.

Examples:
- class → surface_type → implement_type → total_count
- department → team → employee → salary

Use:
- Chart type: stacked_doughnut
- X-axis: N/A
- Y-axis: N/A
- Values: total_count
- Labels: [class, surface_type, implement_type]

Format for response:
- Chart type: stacked_doughnut  
- X-axis: N/A  
- Y-axis: N/A  
- Values: [numeric_column]  
- Labels: [list of categorical columns in inner → outer order]  
---------------------
Final Output Format (strictly follow this):

Chart type: [bar / line / scatter / pie / histogram]  
X-axis: [column_name or 'N/A']  
Y-axis: [column_name or 'N/A']  
Values: [column_name or 'N/A']  
Labels: [column_name or 'N/A']  ← Include this only if Chart type is pie

Rules:
- If Chart type is bar, line, or scatter → Values = 'N/A'
- - If Chart type is pie:
   - Labels: [categorical_column]
   - Values: [numeric_column]
   - X-axis: N/A
   - Y-axis: N/A.
- If Chart type is histogram → X-axis = N/A, Y-axis = N/A, Values = [column_name].
- If Chart type is bar and you're comparing usage types → X-axis = usage_type, Y-axis = usage_count, Values = N/A.
- If Chart type is stacked_doughnut:
  - Labels: [list of hierarchical categorical columns, e.g., ['class', 'surface_type', 'implement_type']]
  - Values: [numeric_column]
  - X-axis: N/A
  - Y-axis: N/A
Return only this structured answer. Do not explain or include any comments or justification.
""" 

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    response = client.models.generate_content(contents=contents, model=model)
    return response.text.strip()
def generate_chart(df, suggestion):
    lines = suggestion.split('\n')
    chart_type, x_col, y_col, values_col, label_col = None, None, None, None, None

    for line in lines:
        if line.startswith('Chart type:'):
            chart_type = line.split(':')[1].strip().lower()
        elif line.startswith('X-axis:'):
            x_col = line.split(':', 1)[1].strip()
        elif line.startswith('Y-axis:'):
            y_col = line.split(':', 1)[1].strip()
        elif line.startswith('Values:'):
            values_col = line.split(':', 1)[1].strip()
        elif line.startswith('Labels:'):
            label_col = line.split(':', 1)[1].strip()

    fig = None

    # Drop rows with nulls in relevant columns
    def drop_nulls(columns):
        return df.dropna(subset=columns)

    if chart_type in ['bar','scatter'] and x_col in df.columns and y_col in df.columns:
        df_clean = drop_nulls([x_col, y_col])
        if chart_type == 'bar':
            fig = px.bar(df_clean, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
        elif chart_type == 'scatter':
            fig = px.scatter(df_clean, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
    elif chart_type == 'line':
        df_clean = drop_nulls([x_col, y_col])
        # Check if there's a categorical column for hue (e.g., not x_col or y_col)
        hue_col = None
        for col in df_clean.columns:
            if col not in [x_col, y_col] and df_clean[col].dtype == 'object':
                hue_col = col
                break
        if hue_col:
            fig = px.line(df_clean, x=x_col, y=y_col, color=hue_col, title=f"{y_col} over {x_col} by {hue_col}")
        else:
            fig = px.line(df_clean, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
    elif chart_type == 'stacked_doughnut':
        # Identify label columns (categorical) and a numeric value column
        categorical_cols = df.select_dtypes(include='object').columns.tolist()
        numeric_cols = df.select_dtypes(include='number').columns.tolist()

        if len(categorical_cols) >= 2 and numeric_cols:
            # Use top N categorical columns for hierarchy
            hierarchy = categorical_cols[:min(3, len(categorical_cols))]
            value_col = numeric_cols[0]

            df_clean = df.dropna(subset=hierarchy + [value_col])
            fig = px.sunburst(
                df_clean,
                path=hierarchy,
                values=value_col,
                title='Hierarchical Breakdown',
            )


    elif chart_type == 'pie' and label_col in df.columns and values_col in df.columns:
        df_clean = drop_nulls([label_col, values_col])
        fig = px.pie(df_clean, names=label_col, values=values_col, title=f"Distribution of {label_col}")

    elif chart_type == 'histogram' and values_col in df.columns:
        df_clean = drop_nulls([values_col])
        fig = px.histogram(df_clean, x=values_col, title=f"Histogram of {values_col}")

    elif chart_type in ['bar', 'line'] and x_col.startswith('[') and y_col.startswith('['):
        try:
            x_values = ast.literal_eval(x_col)
            y_values = ast.literal_eval(y_col)
            temp_df = pd.DataFrame({'Category': x_values, 'Value': y_values})
            temp_df = temp_df.dropna(subset=['Category', 'Value'])
            if chart_type == 'bar':
                fig = px.bar(temp_df, x='Category', y='Value', title="Comparison")
            elif chart_type == 'line':
                fig = px.line(temp_df, x='Category', y='Value', title="Trend Comparison")
        except Exception as e:
            print(f"Error parsing literal lists: {e}")

    return fig
