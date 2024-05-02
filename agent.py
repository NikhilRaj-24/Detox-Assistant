from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
import streamlit as st
from datetime import datetime
import os 

os.environ["GROQ_API_KEY"] = "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"
def init_database(user: str, password: str, database: str):
  db = SQLDatabase.from_uri("sqlite:///new.db")
  return db

def get_sql_chain(db):
  template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
    Based on the table schema below, write a SQL query that would answer the user's question. Take the conversation history into account.
    
    <SCHEMA>{schema}</SCHEMA>
    
    Conversation History: {chat_history}
    
    Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.
    table details :
    Table Name: products

    product_id (TEXT): Unique identifier for each product.
    product_name (TEXT): Name/title of the product.
    category (TEXT): Type or category of the product.
    discounted_price (REAL): Price after discounts are applied.
    actual_price (REAL): Original price before discounts.
    discount_percentage (INTEGER): Percentage of discount applied.
    rating (REAL): Overall rating of the product.
    rating_count (INTEGER): Total number of ratings received.
    bought_date (TEXT): Date when the product was purchased.

    For example:
    Question: What are the top 5 products with the highest discount percentages?
    SQL Query: SELECT product_name, discount_percentage FROM products ORDER BY discount_percentage DESC LIMIT 5;

    Question:  How many products have a rating above 4.5?
    SQL Query: SELECT COUNT(*) as count_high_rating FROM products WHERE rating > 4.5;

    Question: What is the average discount percentage of products in each category?
    SQL Query: SELECT category, AVG(discount_percentage) as avg_discount_percentage FROM products GROUP BY category;

    Question: What is the most costliest product i bought?
    SQL Query: SELECT product_name, actual_price FROM products ORDER BY actual_price DESC LIMIT 1;

    Question: What is the total price of all products bought?
    SQL Query: SELECT SUM(actual_price) as total_price FROM products;


    Question: Can I replace a product named "product_name" if it was bought within the last 30 days?

    sql query: 
        " SELECT
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM products p
                WHERE p.bought_date >= DATE('now', '-30 day')
                  AND p.product_name LIKE '%' || 'product_name' || '%'
                ORDER BY p.bought_date DESC
                LIMIT 1
            )
            THEN 'Replacement is possible'
            ELSE 'Replacement is not possible'
        END AS replacement_status; "

    Your turn:
    
    Question: {question}
    SQL Query:
    """
    
  prompt = ChatPromptTemplate.from_template(template)
  
  llm = ChatGroq(model="llama3-70b-8192", groq_api_key="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",temperature=0)
  
  def get_schema(_):
    return db.get_table_info()
  
  return (
    RunnablePassthrough.assign(schema=get_schema)
    | prompt
    | llm
    | StrOutputParser()
  )


def detox_text(user_input: str,chat_history: list):
  llm = ChatGroq(model="llama3-70b-8192",temperature=0.5)
  template = """
  You role to detoxify the text by removing any offensive or inappropriate content.
  If the text does not contain any offensive or inappropriate content, provide the same text as the response.
  Also consider the conversation history:
    Conversation History: {chat_history}
  examples:
  Input: "I will fuck you!"
  response: "Thank you"

  Input: "What the fuck are you speaking"
  response: "what are you speaking"

  Input: "Can I return this product"
  response: "can I return this product"

  Input: "Fuck you"
  response: "Thank You"

  Input: "What did I buy at last"
  response: "What did I buy at last"

  Input: "Hi"
  response: "Hi"

  Input: "you are a piece of shit, return my tv right now"
  response: "return my tv right now"

  note :Dont add any preamble in the response
  Input:{user_input}
  response:
  
  """
  prompt = ChatPromptTemplate.from_template(template)

  chain = prompt | llm | StrOutputParser()

  return chain.invoke({
    "user_input": user_input,
    "chat_history": chat_history,
  
  })


def get_response(user_query: str, db: SQLDatabase, chat_history: list):
  current_date = datetime.now().date()
  sql_chain = get_sql_chain(db)
  
  template = """
    You are Velraj, a customer service agent for Amazon. Your role is to assist customers with inquiries related to products they have purchased. Respond only to product-related queries and refrain from acknowledging or responding to any other questions. Maintain the persona of Velraj, ensuring that your responses are helpful and informative regarding product-related issues.
    Based on the table schema below, question, sql query, and sql response, write a natural language response.
    If the reponse doesnt require any sql query, provide the response as it is.
    <SCHEMA>{schema}</SCHEMA>
    

    Conversation History: {chat_history}
    SQL Query: <SQL>{query}</SQL>
    User question: {question}
    SQL Response: {response}"""
  
  prompt = ChatPromptTemplate.from_template(template)
  
  llm = ChatGroq(model= "llama3-70b-8192", temperature=0)
  
  chain = (
    RunnablePassthrough.assign(query=sql_chain).assign(
      schema=lambda _: db.get_table_info(),
      response=lambda vars: db.run(vars["query"]),
    )
    | prompt
    | llm
    | StrOutputParser()
  )
  
  return chain.invoke({
    "question": user_query,
    "chat_history": chat_history,
  
  })
    
  
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
      AIMessage(content="Hello! I'm Velraj. Your Amazon agent. Let me know if you have any issues."),
    ]


st.set_page_config(page_title="Amazon Assistant", page_icon=":speech_balloon:")

st.title("Amazon Agent")

with st.sidebar:
    st.subheader("Settings")
    st.write("connect the database to start chatting with your agent")
    
    st.text_input("User", value="root", key="User")
    st.text_input("Password", type="password", value="admin", key="Password")
    st.text_input("Database", value="new", key="Database")
    
    if st.button("Connect"):
        with st.spinner("Connecting to database..."):
            db = init_database(
                st.session_state["User"],
                st.session_state["Password"],
                st.session_state["Database"]
            )
            st.session_state.db = db
            st.success("Connected to database!")
    
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)

user_query = st.chat_input("Type a message...")
if user_query is not None and user_query.strip() != "":
    user_query = detox_text(user_query, st.session_state.chat_history)
    print("Detoxified Text --------- ", user_query)
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    

    with st.chat_message("Human"):
        st.markdown(user_query)
        
    with st.chat_message("AI"):

        response = get_response(user_query, st.session_state.db, st.session_state.chat_history)
        st.markdown(response)
        
    st.session_state.chat_history.append(AIMessage(content=response))