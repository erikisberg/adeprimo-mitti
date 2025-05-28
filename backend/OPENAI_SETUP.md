# Setting Up OpenAI Assistant for Content Analysis

This guide provides step-by-step instructions for creating and configuring the OpenAI Assistant that will be used for content analysis in the Content Monitor system.

## Prerequisites

- An OpenAI account with API access
- API credits or a payment method set up for your account

## Steps to Create the Assistant

1. **Log in to your OpenAI account**
   - Go to [https://platform.openai.com/](https://platform.openai.com/)
   - Sign in with your credentials

2. **Navigate to the Assistants section**
   - In the left sidebar, click on "Assistants"
   - Click the "Create" button to create a new assistant

3. **Configure your Assistant**
   - **Name**: Content Analyzer
   - **Model**: Select either gpt-4 (recommended for best results) or gpt-3.5-turbo (faster, lower cost)
   - **Instructions**: Copy and paste the following instructions:

   ```
   You are a content analysis assistant that evaluates web content based on newsworthiness, relevance, and importance. 
   
   Rate content on a scale of 1-5, where:
   1 = Not interesting (routine updates)
   2 = Slightly interesting
   3 = Moderately interesting
   4 = Very interesting (significant development)
   5 = Extremely interesting (major development)
   
   For each analysis, provide:
   1. Your numerical rating (1-5)
   2. A brief explanation for your rating (2-3 sentences)
   
   Consider factors such as:
   - Is this information new or significant?
   - Does it represent a major change or development?
   - Would this information be valuable to someone monitoring this topic?
   - Is this a routine update or a significant announcement?
   
   Focus your analysis on content from the Sollentuna area, considering its relevance to local residents and businesses. Pay special attention to municipal decisions, housing developments, community events, and sports news that might be of broad interest.
   
   Be consistent in your ratings across different types of content, maintaining the same standards for what constitutes interesting content regardless of the source.
   ```

4. **Additional Settings**
   - **Knowledge Retrieval**: No need to enable
   - **Code Interpreter**: No need to enable
   - **File Upload**: No need to enable 

5. **Create the Assistant**
   - Click the "Create" button at the bottom of the page

6. **Get the Assistant ID**
   - After creating the assistant, you'll be taken to the assistant details page
   - The Assistant ID is shown at the top of the page or in the URL
   - Copy this ID as you'll need it for the configuration

## Updating Your Configuration

Once you have the Assistant ID, you need to add it to your configuration:

1. **Edit the `.env` file**
   - Open the `.env` file in the project directory
   - Replace `your_assistant_id_here` with the actual ID you copied
   - Also set your OpenAI API key if you haven't already

   Example:
   ```
   OPENAI_API_KEY=sk-...your-actual-api-key...
   OPENAI_ASSISTANT_ID=asst_...your-assistant-id...
   ```

2. **Test the connection**
   - Run the setup test to verify the configuration:
   ```
   source venv/bin/activate
   python setup_test.py
   ```

## Troubleshooting

- **API Key Issues**: Ensure your OpenAI API key has sufficient permissions and is correctly entered
- **Billing Issues**: Check if your OpenAI account has proper billing set up
- **Rate Limiting**: If you encounter rate limit errors, the script includes retry logic, but you may need to adjust request frequency

## Cost Considerations

- The OpenAI Assistant API usage incurs costs based on the model used and the amount of text processed
- GPT-4 is more expensive but provides better analysis
- GPT-3.5-turbo is less expensive but may provide less nuanced analysis
- The script is designed to only send content for analysis when significant changes are detected, helping to control costs