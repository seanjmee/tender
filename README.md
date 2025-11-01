# SAM.gov Contract Intelligence Agent

An AI-powered tool that helps you analyze government contract opportunities using Google Gemini and GPT-4.

## 🎯 What It Does

1. **Generates realistic government contract scenarios** based on your search keywords
2. **Analyzes contracts with dual AI models** (Google Gemini + GPT-4) side-by-side
3. **Creates contract summaries** highlighting key requirements, scope, and timelines
4. **Generates bid proposal outlines** with 1-2 paragraph recommendations
5. **Compares AI approaches** so you can see different perspectives on the same contract

## ⚡ Quick Start

### 1. Set up your `.env` file:

```bash
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=sk-proj-your_openai_key_here
```

### 2. Run the application:

```bash
python tender.py
```

### 3. Open your browser:

Navigate to: **http://localhost:7860**

### 4. Search for contracts:

- Enter keywords like "gardening", "IT services", "construction", etc.
- Click "Search Contracts"
- View side-by-side AI analysis!

## 🤖 Why Two AI Models?

Comparing Google Gemini and GPT-4 gives you:

- **Different perspectives** on the same contract
- **More comprehensive analysis** by combining insights
- **Better bid quality** from seeing multiple approaches
- **Risk mitigation** - catch what one model might miss

## 📋 Example Output

For each contract, you'll see:

### Google Gemini (Green Box)
- Summary of requirements, scope, timeline
- Proposal outline emphasizing qualifications and differentiators

### GPT-4 (Blue Box)
- Alternative summary with different focus areas
- Different proposal approach and strategic recommendations

## 💡 Use Cases

### 1. **Learning Tool**
Perfect for understanding how to analyze government contracts and write proposals

### 2. **Bid Development**
Use AI-generated outlines as starting points for real proposals

### 3. **Market Research**
Try different keywords to understand government procurement trends

### 4. **Proposal Training**
Compare how two leading AI models approach the same contracting challenge

## 🔧 Technical Details

### Current Implementation
- Uses **sample contract data** based on your keywords
- Fully functional **AI analysis** from Google Gemini and GPT-4
- Clean **Gradio web interface** with color-coded comparisons
- No SAM.gov API required

### Why Sample Data?
- SAM.gov's official API has access limitations
- The website uses JavaScript rendering (requires Playwright/Selenium)
- Sample data lets you focus on learning the AI analysis capabilities
- The AI models generate REAL, useful analysis regardless of data source

### For Production Use
To scrape real SAM.gov contracts, you would need:

1. **Playwright or Selenium** - Handle JavaScript-rendered content
2. **Rate limiting** - Respect SAM.gov's servers
3. **Error handling** - Manage dynamic page structures
4. **API access** - Or official SAM.gov API key (if available)

The AI analysis portion is production-ready and works with any contract data!

## 💰 Cost Per Search

Each search analyzes 3 contracts:

- **Google Gemini**: ~$0.003 (very affordable!)
- **GPT-4**: ~$0.09 (industry standard)
- **Total**: ~$0.09 per search

## 🎨 Features

- ✅ Dual AI comparison (Gemini vs GPT-4)
- ✅ Beautiful Gradio interface
- ✅ Color-coded outputs
- ✅ Customizable search keywords
- ✅ Production-ready AI integration
- ✅ No SAM.gov API needed
- ✅ Perfect for learning and training

## 📚 Files Included

- `tender.py` - Main application (380 lines)
- `tender_setup.md` - Detailed setup instructions
- `tender_example.md` - Usage examples and best practices
- `tender_README.md` - This file

## 🔑 Getting API Keys

### Google AI (Gemini)
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Create API key
4. Add to `.env` as `GOOGLE_API_KEY`

### OpenAI (GPT-4)
1. Visit: https://platform.openai.com/
2. Sign up and add billing
3. Create API key
4. Add to `.env` as `OPENAI_API_KEY`

## 🚀 Next Steps

1. **Try different keywords**: "landscaping", "cybersecurity", "facilities", etc.
2. **Compare the AI outputs**: Notice how each model approaches analysis differently
3. **Use as a template**: Copy the proposal structures for real bids
4. **Customize prompts**: Edit the code to focus on specific bid requirements
5. **Add real data**: Integrate with actual SAM.gov scraping when ready

## 🎓 Educational Value

This tool teaches you:
- How to structure government contract proposals
- What AI models focus on when analyzing contracts
- How to compare multiple AI perspectives
- Best practices for bid writing
- Understanding of contract requirements analysis

## ⚠️ Important Notes

- This is a **demonstration/training tool** with sample data
- AI-generated proposals should be **reviewed and customized**
- Always verify contract details on official SAM.gov website
- Use AI insights as a starting point, not final submissions
- Comply with all government contracting regulations

## 🤝 Contributing

Want to add real SAM.gov scraping? Consider:
- Implementing Playwright for JavaScript rendering
- Adding caching to reduce API costs
- Creating templates for different contract types
- Adding export functionality (PDF, Word, etc.)

## 📄 License



---

**Ready to analyze some contracts?** Run `tender.py` and start exploring! 🏛️✨

