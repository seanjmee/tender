# SAM.gov Contract Agent - Setup Guide

## Quick Start

This agent searches for government contract opportunities and uses both Google AI (Gemini) and GPT-4 (OpenAI) to generate summaries and sample bid proposals.

**Note:** This version uses intelligent sample data generation based on your keywords. The AI models still generate real, useful analysis that you can use as templates for actual contracts.

## API Keys Required

You need two API keys in your `.env` file:

### 1. Google API Key (Gemini)
- **Register at:** https://makersuite.google.com/app/apikey
- **Steps:**
  1. Sign in with your Google account
  2. Click "Get API Key" or "Create API Key"
  3. Copy your API key
- **Add to `.env`:**
  ```
  GOOGLE_API_KEY=your_google_api_key_here
  ```

### 2. OpenAI API Key (GPT-4)
- **Register at:** https://platform.openai.com/
- **Steps:**
  1. Sign up for OpenAI account
  2. Add billing information (pay-as-you-go)
  3. Create API key in API Keys section
- **Add to `.env`:**
  ```
  OPENAI_API_KEY=sk-proj-your_key_here
  ```

## Your .env File Should Look Like:

```bash
# AI APIs
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=sk-proj-your_openai_key_here
```

## Running the Agent

1. **Make sure all dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python week1/tender.py
   ```

3. **Open your browser:**
   - The Gradio interface will launch at: http://localhost:7860
   - Enter a keyword (default is "gardening")
   - Click "Search Contracts"

## Features

- 🔍 **Smart Contract Generation:** Creates realistic contract scenarios based on your keywords
- 🤖 **Dual AI Analysis:** Compares Google Gemini and GPT-4 responses side-by-side
- 📊 **Contract Summaries:** Extracts key requirements, scope, and timeline
- 📝 **Bid Proposals:** Generates 1-2 paragraph proposal outlines
- 🎨 **Beautiful UI:** Clean Gradio interface with color-coded comparisons
- 💡 **Training Tool:** Perfect for learning how to write government contract proposals

## Example Search Keywords

Try these keywords to find different types of contracts:
- `gardening`
- `landscaping`
- `IT services`
- `construction`
- `environmental services`
- `facilities maintenance`
- `consulting`
- `software development`

## Troubleshooting

### "API Key Required" Error
- Make sure your `.env` file is in the project root directory
- Check that both API keys are present and correctly formatted
- Restart the application after adding keys

### AI Generation Errors
- Verify your Google and OpenAI API keys are valid
- Check you have sufficient credits/billing set up
- Review rate limits for your API tier

## Cost Estimate

- **Google Gemini:** ~$0.001 per contract analysis (with Gemini 1.5 Pro)
- **GPT-4:** ~$0.03 per contract analysis
- **Total per search (3 contracts):** ~$0.09

## For Production Use

This demo uses sample data. To scrape real SAM.gov contracts, you would need:

1. **Playwright or Selenium** - SAM.gov uses JavaScript rendering
2. **API Access** - Or register for official SAM.gov API (if you can get it working)
3. **Rate Limiting** - Implement respectful scraping delays
4. **Error Handling** - Handle dynamic page structures

The AI analysis portion is fully functional and will work with any contract data you provide!

## API Documentation

- Google AI: https://ai.google.dev/docs
- OpenAI: https://platform.openai.com/docs/
- SAM.gov: https://sam.gov/search/

