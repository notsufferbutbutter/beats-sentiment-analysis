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

# Define a dictionary to hold fixed data
FIX_DATA = {
    "Product Name": "Beats Studio Pro",
    "Source": "Reddit",
    "Launch Date": "July 19th, 2023",
}

# The model is a fine-tuned version of RoBERTa for sentiment analysis
SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment"
# Load the sentiment analysis model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL)
model = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL)
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

# Define a list to hold all rows of data
all_rows = []
# Define a list of Reddit URLs to analyze
url1WeekPost = "https://www.reddit.com/r/beatsbydre/comments/1hch8sa/1week_review_of_beats_studio_pro/"
urlBeatsImpression = "https://www.reddit.com/r/beatsbydre/comments/1554cui/beats_studio_pro_impressions/"
urlBeatsThoughts = "https://www.reddit.com/r/beatsbydre/comments/15emhk0/beats_studio_pro_reviewthoughts/"
# Iterate through the list of URLs and analyze comments from each URL
for url in [url1WeekPost, urlBeatsImpression, urlBeatsThoughts]:
    all_rows.extend(commentAnalyzingThroughRedditURL(url))

# Create a DataFrame from the list of rows
df = pd.DataFrame(all_rows)
output_path = Path("./data_output") / "BeatsScraper.xlsx"
df.to_excel(output_path, index=False, engine="openpyxl")