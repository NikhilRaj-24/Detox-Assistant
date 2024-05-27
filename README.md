# Amazon Assistant Chatbot

## Overview

This project is a Streamlit-based chatbot application designed to assist Amazon customers with inquiries related to product returns, order status and general questions about products or services. The chatbot ensures that conversations remain respectful and free from harmful language by detecting and cleaning bad or toxic comments.

## Features
• Real-time detection and cleaning of bad/toxic comments

• Maintains the overall context of the original messages

• User-friendly interface built with Streamlit

• Pre-defined conversation flow for initial interaction

• SQL query generation and natural language response based on database schema

## How It Works
Start of the app: The app starts with a welcome message from Velraj, the Amazon agent. Users connect to a SQL database using credentials provided in the sidebar.

Detoxification: When a user inputs a message, the text is processed to remove any offensive or inappropriate content.

Response Generation: The chatbot generates SQL queries based on user questions and the database schema. Responses are crafted based on SQL query results and provided in natural language.

Conversation History: The app maintains a conversation history to ensure contextually relevant responses.
