import os
import time
import random
import requests
from requests_oauthlib import OAuth1
from openai import AzureOpenAI  # Ensure you have the correct OpenAI SDK installed
import logging

# Optional: Setup logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Twitter API credentials
api_key = "[insert]"
api_secret_key = "[insert]"
access_token = "[insert]"
access_token_secret = "[insert]"

# Azure OpenAI credentials
azure_endpoint = "https://usnorthamericaeastus2.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2023-03-15-preview"
azure_api_key = "[insert]"
deployment_name = "gpt-4o"  # Replace with your deployment name
# Variable to store the last tweet
last_tweet = None

# Hashtag categories and their corresponding hashtags
HASHTAG_CATEGORIES = {
    "inspiration": ["#Inspiration", "#Motivation", "#Believe", "#DreamBig", "#StayPositive"],
    "technology": ["#Tech", "#AI", "#Innovation", "#Future", "#TechTrends"],
    "nature": ["#Nature", "#Earth", "#Outdoors", "#Wildlife", "#Environment"],
    "humor": ["#Humor", "#Funny", "#Smile", "#Laugh", "#Comedy"],
    "space": ["#Space", "#Universe", "#Astronomy", "#Cosmos", "#Stars"],
    "animals": ["#Animals", "#Pets", "#Wildlife", "#Cute", "#AnimalLovers"],
    "art": ["#Art", "#ASCIIArt", "#Creativity", "#Design", "#DigitalArt"],
    "success": ["#Success", "#Achievement", "#Goals", "#Winning", "#Progress"],
    "life": ["#Life", "#Mindfulness", "#Wellness", "#SelfCare", "#PersonalGrowth"],
    "education": ["#Learning", "#Education", "#Knowledge", "#Growth", "#Teach"],
    # Add more categories and hashtags as needed
}

def generate_tweet(prompt, last_tweet=None):
    """
    Generate tweet content using Azure OpenAI GPT-4o
    """
    try:
        client = AzureOpenAI(
            api_version="2023-03-15-preview",
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key
        )

        # Flatten the hashtags into a single list
        all_hashtags = [hashtag for hashtags in HASHTAG_CATEGORIES.values() for hashtag in hashtags]
        hashtags_text = ', '.join(all_hashtags)

        messages = [
            {
                "role": "system",
                "content": f"""You are a creative ASCII art expert tasked with generating engaging and diverse ASCII art messages for Twitter. Your goal is to create ASCII art that spans a broad range of themes and topics, ensuring variety and surprise for the audience.

Each ASCII art should:

1. **Be within 280 characters**: Ensure the entire message fits within Twitter's character limit.

2. **Cover diverse themes**: Randomly select from a wide array of positive and engaging topics such as nature, technology, space, motivation, humor, animals, celebrations, abstract designs, and more.

3. **Incorporate engaging messages**: Pair the ASCII art with a short, uplifting, or thought-provoking message or quote relevant to the art.

4. **Utilize social media engagement strategies**:
   - **Emotional Appeal**: Evoke positive emotions like joy, inspiration, or amusement.
   - **Visual Appeal**: Craft visually attractive ASCII art that stands out in text form.
   - **Relevance**: Align with trending topics or universal themes that resonate widely.
   - **Calls to Action**: Encourage interaction, such as sharing, liking, or commenting.
   - **Simplicity and Clarity**: Ensure the art and message are easily understandable at a glance.
   - **Use of Hashtags**: Include 1-2 relevant and popular hashtags from the following list to increase visibility:
     {hashtags_text}

5. **Maintain professionalism**: Content should be appropriate for all audiences and free from offensive or controversial material.

6. **Randomness**: Randomly vary the themes and styles to keep the content fresh and unpredictable.

**Additional Guidelines**:

- Do not repeat the same art or messages; ensure each tweet is unique.
- Avoid overly complex art that may not render well on all devices.
- Consider the limitations of monospaced fonts when designing the art.
- Keep line lengths compatible with typical screen widths to prevent wrapping issues.
- **Do not include backticks (`) or code block markers in the output. The ASCII art should be plain text without any surrounding formatting characters.**

Use these guidelines to create an engaging and varied ASCII art tweet.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        if last_tweet:
            # Include the last tweet in the system message as context
            messages[0]["content"] += f"\n\nPrevious Tweet:\n{last_tweet}"
            logging.info(f"Included last tweet in prompt:\n{last_tweet}")

        response = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            temperature=0.9,  # Increased for more creativity and randomness
            max_tokens=200  # Adjusted token limit
        )

        tweet_content = response.choices[0].message.content.strip()
        logging.info("Generated Tweet:\n" + tweet_content)

        # Remove backticks from the tweet content
        tweet_content = tweet_content.replace('`', '')

        # Ensure the content is within Twitter's character limit
        if len(tweet_content) > 280:
            logging.warning("Generated tweet exceeds 280 characters. Truncating.")
            tweet_content = tweet_content[:280]

        return tweet_content

    except Exception as e:
        logging.error(f"Error generating tweet: {str(e)}")
        return None

def post_tweet(tweet_text):
    """
    Post the tweet to Twitter using OAuth1 authentication
    """
    # OAuth 1.0a authentication setup
    auth = OAuth1(api_key, api_secret_key, access_token, access_token_secret)

    # Twitter API URL for posting tweets
    url = "https://api.twitter.com/2/tweets"

    # The tweet content
    payload = {
        "text": tweet_text
    }

    try:
        # Make the POST request to Twitter API
        response = requests.post(url, json=payload, auth=auth)

        # Check the response
        if response.status_code in [200, 201, 202]:
            logging.info("Tweet posted successfully!")
            return True
        else:
            logging.error(f"Failed to post tweet. Status code: {response.status_code}, Error: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error posting tweet: {str(e)}")
        return False

def main():
    global last_tweet  # Declare as global to modify the variable outside the function

    # Load last_tweet from file if it exists
    if last_tweet is None and os.path.exists("last_tweet.txt"):
        with open("last_tweet.txt", "r", encoding="utf-8") as f:
            last_tweet = f.read()
        logging.info("Loaded last tweet from file.")

    # Define your prompt for GPT-4o
    prompt = "Create a new and engaging ASCII art tweet."

    # Generate tweet using Azure OpenAI GPT-4o, passing the last tweet as context
    tweet = generate_tweet(prompt, last_tweet)

    if tweet:
        # Post the generated tweet to Twitter
        success = post_tweet(tweet)
        if success:
            logging.info("Tweet posted successfully.")
            # Update the last_tweet variable with the new tweet
            last_tweet = tweet
            # Save last_tweet to file
            with open("last_tweet.txt", "w", encoding="utf-8") as f:
                f.write(last_tweet)
        else:
            logging.error("Failed to post tweet.")
    else:
        logging.error("Tweet generation failed. Tweet not posted.")

if __name__ == "__main__":
    # Calculate sleep intervals to achieve 20-30 tweets per day
    # 24 hours = 86400 seconds
    min_tweets = 20
    max_tweets = 30
    min_interval = 86400 / max_tweets  # 86400 / 30 ≈ 2880 seconds (48 minutes)
    max_interval = 86400 / min_tweets  # 86400 / 20 ≈ 4320 seconds (72 minutes)

    logging.info("Tweet bot started. It will tweet between 20-30 times per day at random intervals.")
    while True:
        main()
        # Calculate a random sleep time between min_interval and max_interval
        sleep_time = random.randint(int(min_interval), int(max_interval))
        logging.info(f"Sleeping for {sleep_time / 60:.2f} minutes before next tweet.")
        time.sleep(sleep_time)
