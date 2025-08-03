import streamlit as st
from google.cloud import bigquery
import pandas as pd 
from sql_generation import generate_sql, get_bigquery_table_schema_text
from query_verification import verify_query
from chart_generation import generate_chart_suggestion, generate_chart
from streamlit_option_menu import option_menu
from query_scanning import get_query_cost_estimate,bytes_to_human_readable
import json
from insights_generation import insights
from query_simplifier import simplify_query
import plotly.io as pio
from io import BytesIO
import streamlit.components.v1 as components 

USER_CREDENTIALS = {
    "admin": "admin123",
    "user": "user123"
}

project_id = "bigquery-public-data"
dataset_id = "san_francisco_311"
table_name = "311_service_requests"

client = bigquery.Client()


def login_page():
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(
            """
            <div style="background: linear-gradient(90deg, #0072ff, #00c6ff); 
                        height: 100vh; 
                        color: white; 
                        padding: 8rem 2rem;
                        font-size: 2rem;
                        font-weight: 600;
                        display: flex;
                        align-items: center;">
                Insights Platform
            </div>
            """, unsafe_allow_html=True
        )

    with col2:
        st.markdown("<h3 style='margin-top: 0;'>Login</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: gray;'>Please enter your email and password to continue</p>", unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center;'>Login</h3>", unsafe_allow_html=True)
            username = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Login successful! Please proceed to the SQL Generator page.")
                else:
                    st.error("Invalid username or password")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()


def run_query_in_bigquery(project_id, query):
    client = bigquery.Client(project=project_id)
    query_job = client.query(query)
    result = query_job.result()
    df = result.to_dataframe()
    # df = df.dropna(inplace=True)
    return df


def main():
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("user_query_input", "")
    st.session_state.setdefault("query_submitted", False)
    st.session_state.setdefault("sql_query", "")
    st.session_state.setdefault("verified_sql", "")
    st.session_state.setdefault("query_ready_to_run", False)
    st.session_state.setdefault("query_result_df", None)
    st.session_state.setdefault("chart_fig", None)
    st.session_state.setdefault("chart_html_bytes", None)

    with st.sidebar:
        choice = option_menu(
                "",
                options=["Login","SQL Generator","Logout"],
                icons=["box-arrow-in-right","database","box-arrow-left"],
                menu_icon="cast",
                default_index=0,
            )

    if choice == "Login": 
        login_page()

    elif choice == "Logout":
        if not st.session_state.logged_in:
            st.warning("🔐 You are not logged in.")
        else: 
            st.subheader("Ready to leave?")
            if st.button("🔓 Click here to logout"):
                st.success("👋 You’ve been logged out.")
                logout()
                

    elif choice == "SQL Generator":
        st.title("SQL Generator and Visualizer for BigQuery")
        
        if not st.session_state.logged_in:
            st.warning("🔐 Please login to access the SQL Generator.")
            return

        # Input field for user's natural language question
        user_query = st.text_input("Enter your question", value=st.session_state.user_query_input)

        # Handle Submit button
        if st.button("Submit Query",key="submit_query_button"):
            if user_query.strip():
                st.session_state.user_query_input = user_query
                st.session_state.query_submitted = True
                st.session_state.query_ready_to_run = False
                st.session_state.query_result_df = None
                st.session_state.chart_fig = None
                st.session_state.chart_html_bytes = None

                schema = get_bigquery_table_schema_text()
                simplified_user_query = simplify_query(user_query, schema)
                st.session_state.simplified_user_query = simplified_user_query
                
                sql_query = generate_sql(simplified_user_query)
                st.session_state.sql_query = sql_query

                if sql_query:
                    correct_query = verify_query(user_query, sql_query, schema)
                    response = json.loads(correct_query)
                    st.session_state.verified_sql = response.get("correct_query", sql_query)
                else:
                    st.session_state.verified_sql = ""
                    st.error("Couldn't verify or improve the generated query.")
            else:
                st.warning("Please enter a question before submitting.")
        
        
        # Show SQL and verification if query was submitted
        if st.session_state.query_submitted:

            estimated_bytes = get_query_cost_estimate(st.session_state.verified_sql,project_id)
            if estimated_bytes is not None:
                readable = bytes_to_human_readable(estimated_bytes)
                st.subheader("Query Resource Usage") 
                st.markdown(f"""
    <div style=" 
        background-color: rgba(66, 133, 244, 0.1);
        color: var(--text-color);
        padding: 1rem;
        border-left: 6px solid #4285f4;
        border-radius: 8px;
        font-size: 1.05rem;
        font-weight: 500;">
        This query will process approximately <strong>{readable}</strong> of data when run.
    </div>
    """,
    unsafe_allow_html=True
)
            # Run query button
            if st.button("Run This Query",key="run_query_button"):
                st.session_state.query_ready_to_run = True
                st.session_state.chart_fig = None
                st.session_state.chart_html_bytes = None

            # Run query if approved and no cached result
            if st.session_state.query_ready_to_run:
                df = run_query_in_bigquery(project_id, st.session_state.verified_sql)
                df=df.dropna()
                if df.empty:
                    st.warning("No data found")
                    return 
                else:
                    st.session_state.query_result_df = df.dropna()
                    st.success("Query ran successfully! Here's your data:")
                    print(df.head(2))

                    df_display = df.copy()
                    df_display = df_display.astype(str)
                    # st.dataframe(df)
                    st.dataframe(df_display,use_container_width=True)
                    # st.table(df)
                    # st.table(df_display)

                    df_json = df.head(250).to_json(orient="records")
                    print(df_json)
                    insight = insights(user_query, df_json)
                    st.session_state.insight = insight
                    st.subheader("Insights:")
                    st.write(insight)


                # # Show cached results if available
                # if st.session_state.query_result_df is not None:
                #     st.success("Query ran successfully! Here's your data:")
                #     st.dataframe(st.session_state.query_result_df)
                    #df = st.session_state.query_result_df
                    df_head = df.head(25).to_string()
                    df_dtypes = str(df.dtypes)
                    suggestion = generate_chart_suggestion(df_head, df_dtypes, user_query, st.session_state.get("insight", ""))
                    df = df.dropna()
                    fig = generate_chart(df, suggestion)
                    if fig:
                        fig.update_layout(template="plotly")
                        st.session_state.chart_fig = fig
                        st.session_state.chart_html_bytes = BytesIO(pio.to_html(fig, full_html=True, include_plotlyjs='cdn').encode("utf-8"))

                    # Display chart if available
                    if st.session_state.chart_fig:
                        st.subheader("Generated Chart")
                        st.plotly_chart(st.session_state.chart_fig, use_container_width=True)

                        st.download_button(
                            label="Download Chart",
                            data=st.session_state.chart_html_bytes,
                            file_name="interactive_chart.html",
                            mime="text/html",
                            key="download_chart_button"
                        )
                    else:
                        st.warning("Couldn’t create a chart based on the data.")

if __name__ == "__main__":
    main()
