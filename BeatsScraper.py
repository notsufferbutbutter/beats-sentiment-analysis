from typing import List, Tuple
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd
# Import praw library to access Reddit API
import praw
from praw.models import Comment
# Use a pipeline as a high-level helper
from transformers import pipeline
# Load model directly
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import streamlit as st


# Set the title of the Streamlit app
st.title("Product Sentiment Analysis Based on Reddit Comments")
# Set the description of the Streamlit app
st.markdown(
    '''created by Hoang Linh Pham
    \n
    This app analyzes the sentiment of comments on Reddit posts about a product based on a given URL.
    It uses the PRAW library to access Reddit API and fetch comments.
    The comments are then analyzed using a pre-trained sentiment analysis model.
    The app provides a summary of the sentiment of the comments'''
)
# Set the url input field for the user to enter a Reddit URL
#url_input = st.text_input("Enter Reddit URL")
product_name = st.text_input("Enter Product Name:")

# Define a dictionary to hold fixed data
FIX_DATA = {
    "Product Name": "Beats Studio Pro",
    "Source": "Reddit",
    "Launch Date": "July 19th, 2023",
}

# The model is a fine-tuned version of RoBERTa for sentiment analysis
model_name = "yangheng/deberta-v3-base-absa-v1.1"
# Load the sentiment analysis model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
# Create pipeline for sentiment analysis
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=model,
    tokenizer=tokenizer,
)
# Define a function to analyze sentiment of a given text
def analyze(text: str) -> Tuple[str, float]:
    # Use the sentiment pipeline to analyze the text
    # The model returns a list of dictionaries with labels and scores
    # The labels are in the format "LABEL_X" where X is the class index
    # The scores are the probabilities for each class
    # The model is trained on 3 classes: negative, neutral, and positive
    # The labels are "LABEL_0" for negative, "LABEL_1" for neutral, and "LABEL_2" for positive
    # The scores are in the range [0, 1] and sum to 1
    sen = sentiment_pipeline(text)[0]
    label = sen["label"]
    score = sen["score"]
    match label:  
        case "LABEL_0":
            return "Negative", score
        case "LABEL_1":
            return "Neutral", score
        case "LABEL_2":
            return "Positive", score
    # If the label is not recognized, return "Unknown"
    return "Unknown", -1.0

# Load environment variables from .env file
load_dotenv()

#Collect url based on product name
def collect_url(product_name:str) -> List[str]:
    # Use the Reddit API to search for posts related to the product name
    # The search is limited to the last 1000 posts
    # The search is sorted by relevance
    # The search is limited to the "all" subreddit
    url = []
    for submission in redditData.subreddit("all").search(product_name, limit=10, sort='revelence'):
        url.append(submission.url)
    return url

# Access Reddit API
redditData = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
    username=os.getenv("REDDIT_USERNAME"),
)

# Define a function to analyze comments from a given Reddit URL
def commentAnalyzingThroughRedditURL(url: str) -> List[dict]:
    # Create a list to hold the rows of data
    # The rows will be dictionaries with fixed data and comment data
    rows = []
    # Get the submission object from the URL
    # The submission object contains the post and its comments
    submission = redditData.submission(url=url)
    # Replace "more comments" with actual comments
    submission.comments.replace_more(limit=None)
    # Iterate through the comments in the submission
    # For each comment, analyze its sentiment and create a row of data holding the fixed data and comment data
    # The comment data includes the date of conversation, username, main topic, sentiment, conversation snippet, and sentiment score
    for comment in submission.comments.list():
        # Skip comments that does not contain product name
        if product_name.lower() not in comment.body.lower():
            continue
        # Analyze the sentiment of the comment
        # The analyze function returns a tuple with the sentiment label and score
        sentimentTuple = analyze(comment.body)
        rows.append({
            **FIX_DATA,
            "Date of Conversation": datetime.fromtimestamp(comment.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
            "Username": comment.author.name if comment.author else "[deleted]",
            "Main Topic": submission.title,
            "Sentiment": sentimentTuple[0],
            "Conversation Snippet": comment.body[:100]
                        + ("…" if len(comment.body) > 100 else ""),
            "Sentiment Score": sentimentTuple[1],
        })
    return rows

# Get the URL from the user input
url_input = collect_url(product_name)
# Define a list to hold all rows of data
all_rows = []

if st.button("Analyze"):
    duck_holder = st.empty()
    # If the user enters a URL, analyze comments from that URL
    with st.spinner("Analyzing... Wanna take a coffee break?"):
        with duck_holder:
            st.markdown(
                '''
                <div style="display: flex; justify-content: center;">
                    <img src="https://i.gifer.com/XOsX.gif" alt="Loading...">
                </div>
                ''',
                unsafe_allow_html=True
            )
        # Call the function to analyze comments from the URL
        # and extend the list of all rows with the all_row object
        for url in url_input:
            all_rows.extend(commentAnalyzingThroughRedditURL(url_input))
    duck_holder.empty()
    st.success("Analysis complete!")
    st.balloons()
    # Create a DataFrame from the list of rows
    df = pd.DataFrame(all_rows)
    st.dataframe(df)


#output_path = Path("./data_output") / "BeatsScraper.xlsx"
#df.to_excel(output_path, index=False, engine="openpyxl")
