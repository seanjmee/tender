"""
SAM.gov Contract Agent with Dual LLM Comparison

This application searches SAM.gov for contract opportunities and uses both
Google AI (Gemini) and GPT-4 (OpenAI) to generate summaries and sample bids.
"""

import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI
import gradio as gr
from typing import List, Dict, Optional
import urllib.parse
from bs4 import BeautifulSoup
import re
import asyncio

# Try to import Playwright for real browser automation
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Install with: pip install playwright && playwright install chromium")

# Load environment variables
load_dotenv(override=True)

# Initialize API clients
google_api_key = os.getenv('GOOGLE_API_KEY')
if google_api_key:
    genai.configure(api_key=google_api_key)
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Headers for web scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}


async def fetch_sam_contracts_playwright(keyword: str, limit: int = 3) -> List[Dict]:
    """
    Use Playwright to scrape SAM.gov with JavaScript rendering
    This is the REAL solution for SAM.gov's dynamic content
    """
    print(f"🌐 Using Playwright browser automation for: {keyword}")
    
    try:
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # Build the SAM.gov search URL
            search_url = "https://sam.gov/search/?index=opp&page=1&sort=-relevance&sfm%5Bstatus%5D%5Bis_active%5D=true"
            search_url += f"&keywords={urllib.parse.quote(keyword)}"
            
            print("   Navigating to SAM.gov...")
            await page.goto(search_url, wait_until="networkidle", timeout=30000)
            
            # Wait for results to load - SAM.gov uses these selectors
            print("   Waiting for results to load...")
            try:
                await page.wait_for_selector('[data-testid="search-results"]', timeout=15000)
            except Exception:
                # Try alternative selectors
                await page.wait_for_timeout(5000)  # Give it 5 seconds
            
            # Wait a bit more for dynamic content
            await page.wait_for_timeout(3000)
            
            # Extract the page content after JavaScript execution
            content = await page.content()
            
            # Save HTML for debugging (optional)
            # with open('/tmp/sam_gov_debug.html', 'w') as f:
            #     f.write(content)
            
            soup = BeautifulSoup(content, 'html.parser')
            contracts = []
            
            # Strategy 1: Try to find structured data or JSON embedded in page
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'opportunity' in script.string.lower():
                    # Try to extract any JSON data
                    try:
                        import json
                        # Look for JSON objects in script tags
                        json_match = re.search(r'\{[^{}]*"title"[^{}]*\}', script.string)
                        if json_match:
                            data = json.loads(json_match.group())
                            if 'title' in data:
                                print("   Found JSON data in script tag")
                    except (json.JSONDecodeError, AttributeError):
                        pass
            
            # Strategy 2: Look for SAM.gov specific selectors (updated based on their current structure)
            # SAM.gov changes their structure, so we try multiple approaches
            
            # Try finding by common SAM.gov patterns
            opportunity_containers = soup.find_all(['div', 'article', 'section'], attrs={
                'data-testid': re.compile(r'search-result|opportunity|contract', re.I)
            })
            
            if not opportunity_containers:
                # Try by class names that SAM.gov commonly uses
                opportunity_containers = soup.find_all(['div'], class_=re.compile(r'search-result|opportunity-card|contract-item', re.I))
            
            if not opportunity_containers:
                # Broader search - look for any div with links that seem like contract titles
                all_links = soup.find_all('a', href=re.compile(r'/opp/|/opportunity/|contract', re.I))
                print(f"   Found {len(all_links)} contract-related links")
                
                for link in all_links[:limit * 3]:
                    try:
                        # Get the container of this link
                        container = link.find_parent(['div', 'article', 'section'])
                        if container and container not in opportunity_containers:
                            opportunity_containers.append(container)
                    except (AttributeError, TypeError):
                        continue
            
            print(f"   Found {len(opportunity_containers)} potential opportunity containers")
            
            # Parse each container
            for container in opportunity_containers[:limit * 3]:
                try:
                    # Get all text from container for analysis
                    container_text = container.get_text(separator=' ', strip=True)
                    
                    # Skip if this looks like navigation or footer
                    skip_terms = ['privacy', 'terms of use', 'sitemap', 'help guide', 'all domains', 'sign in']
                    if any(term in container_text.lower() for term in skip_terms) and len(container_text) < 100:
                        continue
                    
                    # Find title - look for links or headings
                    title = None
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    
                    if not title:
                        # Try finding prominent link
                        link_elem = container.find('a', href=re.compile(r'/opp/|opportunity'))
                        if link_elem:
                            title = link_elem.get_text(strip=True)
                    
                    # Must have a title
                    if not title or len(title) < 15:
                        continue
                    
                    # Skip generic titles
                    if title.lower() in ['all domains', 'help guide', 'search', 'filter']:
                        continue
                    
                    # Extract all text content
                    all_text = container.get_text(separator='\n', strip=True)
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    
                    # Extract notice/solicitation number
                    notice_id = "N/A"
                    for line in lines:
                        if any(term in line.lower() for term in ['notice id', 'solicitation', 'number', 'award']):
                            # Look for alphanumeric codes
                            match = re.search(r'[A-Z0-9]{5,}[-_]?[A-Z0-9]*', line)
                            if match:
                                notice_id = match.group()
                                break
                    
                    # Extract description (look for longer text blocks)
                    description = ""
                    for line in lines:
                        if len(line) > 50 and line != title:
                            description = line
                            break
                    
                    if not description:
                        description = ' '.join(lines[1:4]) if len(lines) > 1 else f"Federal contract opportunity for {keyword}"
                    
                    # Extract dates
                    posted_date = "Recently posted"
                    deadline = "See SAM.gov for details"
                    
                    for line in lines:
                        # Look for date patterns
                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|[A-Z][a-z]{2}\s+\d{1,2},?\s+\d{4})', line)
                        if date_match:
                            if 'post' in line.lower() or 'publish' in line.lower():
                                posted_date = date_match.group()
                            elif 'dead' in line.lower() or 'due' in line.lower() or 'response' in line.lower():
                                deadline = date_match.group()
                    
                    # Extract department/agency
                    department = "Federal Government"
                    for line in lines:
                        if any(term in line.lower() for term in ['department', 'agency', 'office of']):
                            if len(line) < 100:  # Reasonable length for dept name
                                department = line
                                break
                    
                    contract = {
                        'title': title[:250],
                        'notice_id': notice_id,
                        'description': description[:2000],
                        'posted_date': posted_date,
                        'response_deadline': deadline,
                        'department': department,
                        'type': 'Active Opportunity',
                        'naics_code': 'See SAM.gov for NAICS codes'
                    }
                    
                    contracts.append(contract)
                    print(f"   ✓ Extracted: {title[:60]}...")
                    
                    if len(contracts) >= limit:
                        break
                        
                except Exception as e:
                    print(f"   ⚠️  Error parsing container: {str(e)[:100]}")
                    continue
            
            await browser.close()
            
            if contracts:
                print(f"✅ Successfully scraped {len(contracts)} real contracts from SAM.gov!")
                return contracts[:limit]
            else:
                print("⚠️  No contracts found in rendered page")
                return []
                
    except Exception as e:
        print(f"❌ Playwright scraping error: {str(e)}")
        return []


def fetch_sam_contracts(keyword: str, limit: int = 3) -> List[Dict]:
    """
    Scrape contract opportunities from SAM.gov website using multiple strategies
    
    Args:
        keyword: Search term for contracts
        limit: Number of results to return
        
    Returns:
        List of contract dictionaries with relevant information
    """
    print(f"🔍 Searching SAM.gov for: {keyword}")
    
    # Strategy 1: Use Playwright if available (BEST - handles JavaScript)
    if PLAYWRIGHT_AVAILABLE:
        try:
            contracts = asyncio.run(fetch_sam_contracts_playwright(keyword, limit))
            if contracts:
                return contracts
        except Exception as e:
            print(f"⚠️  Playwright failed: {e}")
    
    # Strategy 2: Try direct API endpoints
    print("   Trying API endpoints...")
    try:
        # Try the public opportunities API
        api_url = "https://api.sam.gov/prod/opportunities/v1/search"
        params = {
            'q': keyword,
            'limit': limit,
            'api_key': 'null'
        }
        
        response = requests.get(api_url, params=params, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'opportunitiesData' in data:
                contracts = parse_sam_api_response(data, limit)
                if contracts:
                    print(f"✅ Found {len(contracts)} contracts via API")
                    return contracts
    except Exception as e:
        print(f"   API attempt failed: {e}")
    
    # Strategy 3: Try RSS/XML feeds
    print("   Trying RSS feeds...")
    try:
        rss_url = f"https://sam.gov/api/prod/opportunity-feed/rss?q={urllib.parse.quote(keyword)}"
        response = requests.get(rss_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            contracts = parse_rss_feed(response.content, keyword, limit)
            if contracts:
                print(f"✅ Found {len(contracts)} contracts via RSS")
                return contracts
    except Exception as e:
        print(f"   RSS attempt failed: {e}")
    
    # Fallback: Generate realistic sample data
    print(f"⚠️  All scraping methods failed. Generating realistic samples for '{keyword}'")
    print("💡 To get real contracts, install Playwright: pip install playwright && playwright install chromium")
    return generate_sample_contracts(keyword, limit)


def parse_sam_api_response(data: dict, limit: int) -> List[Dict]:
    """Parse SAM.gov API response format"""
    contracts = []
    opportunities = data.get('opportunitiesData', [])
    
    for opp in opportunities[:limit]:
        contract = {
            'title': opp.get('title', 'No title'),
            'notice_id': opp.get('noticeId', 'N/A'),
            'description': opp.get('description', 'No description')[:1500],
            'posted_date': opp.get('postedDate', 'N/A'),
            'response_deadline': opp.get('responseDeadLine', 'N/A'),
            'department': opp.get('department', {}).get('name', 'N/A') if isinstance(opp.get('department'), dict) else str(opp.get('department', 'N/A')),
            'type': opp.get('type', 'N/A'),
            'naics_code': opp.get('naicsCode', 'N/A')
        }
        contracts.append(contract)
    
    return contracts


def extract_opportunities_from_json(data: dict, keyword: str) -> List[Dict]:
    """Recursively search JSON for opportunity data"""
    contracts = []
    
    # Common keys that might contain opportunity lists
    opportunity_keys = ['opportunities', 'results', 'data', 'items', 'opportunitiesData']
    
    for key in opportunity_keys:
        if key in data and isinstance(data[key], list):
            for item in data[key]:
                if isinstance(item, dict) and 'title' in item:
                    contract = {
                        'title': item.get('title', 'Untitled'),
                        'notice_id': item.get('noticeId', item.get('id', 'N/A')),
                        'description': item.get('description', item.get('summary', ''))[:1500],
                        'posted_date': item.get('postedDate', item.get('publishDate', 'N/A')),
                        'response_deadline': item.get('responseDeadLine', item.get('deadline', 'N/A')),
                        'department': item.get('department', item.get('agency', 'N/A')),
                        'type': item.get('type', 'N/A'),
                        'naics_code': item.get('naicsCode', 'N/A')
                    }
                    contracts.append(contract)
    
    return contracts


def parse_rss_feed(rss_content: bytes, keyword: str, limit: int) -> List[Dict]:
    """Parse SAM.gov RSS feed if available"""
    contracts = []
    try:
        soup = BeautifulSoup(rss_content, 'xml')
        items = soup.find_all('item')[:limit]
        
        for item in items:
            title = item.find('title').get_text() if item.find('title') else f"{keyword.title()} Opportunity"
            description = item.find('description').get_text() if item.find('description') else ""
            pub_date = item.find('pubDate').get_text() if item.find('pubDate') else "N/A"
            link = item.find('link').get_text() if item.find('link') else ""
            
            # Extract notice ID from link if possible
            notice_id = "N/A"
            if link:
                match = re.search(r'[A-Z0-9-]{10,}', link)
                if match:
                    notice_id = match.group(0)
            
            contract = {
                'title': title[:200],
                'notice_id': notice_id,
                'description': BeautifulSoup(description, 'html.parser').get_text()[:1500],
                'posted_date': pub_date,
                'response_deadline': 'See SAM.gov',
                'department': 'Federal Government',
                'type': 'Active Opportunity',
                'naics_code': 'See SAM.gov'
            }
            contracts.append(contract)
    except Exception as e:
        print(f"   RSS parsing error: {e}")
    
    return contracts


def generate_sample_contracts(keyword: str, limit: int) -> List[Dict]:
    """Generate realistic sample contracts when scraping fails"""
    sample_contracts = [
        {
            'title': f'{keyword.title()} Services and Maintenance Contract',
            'notice_id': 'DEMO-2024-001',
            'description': f'The Department of General Services is seeking qualified contractors to provide comprehensive {keyword} services for federal facilities. This includes regular maintenance, seasonal work, equipment provision, and emergency response services. Contractors must demonstrate experience with similar government contracts and meet all federal compliance requirements. The contract period is for a base year with four option years.',
            'posted_date': '2024-10-15',
            'response_deadline': '2024-12-01',
            'department': 'Department of General Services',
            'type': 'Combined Synopsis/Solicitation',
            'naics_code': '561730'
        },
        {
            'title': f'Multi-Site {keyword.title()} and Landscape Management',
            'notice_id': 'DEMO-2024-002',
            'description': f'This procurement is for professional {keyword} and landscape management services at multiple federal buildings and grounds in the region. The scope includes design consultation, plant material selection and installation, irrigation system maintenance, integrated pest management, and sustainable landscape practices. Preference given to contractors with LEED certifications, sustainable {keyword} practices, and veteran-owned business status.',
            'posted_date': '2024-10-20',
            'response_deadline': '2024-12-15',
            'department': 'General Services Administration',
            'type': 'Solicitation',
            'naics_code': '561730'
        },
        {
            'title': f'{keyword.title()} Equipment and Materials Supply Contract',
            'notice_id': 'DEMO-2024-003',
            'description': f'The Department of Veterans Affairs requires {keyword} equipment, materials, and supplies for multiple medical center locations nationwide. This includes commercial-grade equipment, maintenance tools, organic materials, and professional installation services. Deliveries must meet federal sustainability standards and support small business participation. This is a multi-year indefinite delivery/indefinite quantity (IDIQ) contract with a ceiling of $5M.',
            'posted_date': '2024-10-25',
            'response_deadline': '2024-12-20',
            'department': 'Department of Veterans Affairs',
            'type': 'Presolicitation',
            'naics_code': '561730'
        }
    ]
    
    return sample_contracts[:limit]


def generate_google_response(contract_data: Dict, company_profile: Optional[Dict] = None) -> Dict[str, str]:
    """
    Generate contract summary and bid proposal using Google AI (Gemini)
    
    Args:
        contract_data: Dictionary containing contract information
        company_profile: Optional dictionary with company details for personalized proposals
        
    Returns:
        Dictionary with 'summary' and 'bid_proposal' keys
    """
    try:
        system_instruction = "You are a professional government contract analyst and bid writer with expertise in crafting winning proposals."
        
        # Build company context if provided
        company_context = ""
        if company_profile and company_profile.get('company_name'):
            company_context = f"""

When creating the proposal outline, incorporate these company strengths and details:
Company Name: {company_profile.get('company_name', '')}
Years of Experience: {company_profile.get('experience', '')}
Key Capabilities: {company_profile.get('capabilities', '')}
Certifications: {company_profile.get('certifications', '')}
Past Performance: {company_profile.get('past_performance', '')}
Competitive Advantages: {company_profile.get('competitive_advantages', '')}

Tailor the proposal to highlight how this company's specific strengths match the contract requirements."""
        
        prompt = f"""You are a professional contract analyst and bid writer. Analyze this government contract opportunity:

Title: {contract_data['title']}
Department: {contract_data['department']}
Posted: {contract_data['posted_date']}
Deadline: {contract_data['response_deadline']}
Description: {contract_data['description']}{company_context}

Please provide:
1. A concise summary of the key requirements, scope, and timeline
2. A brief 1-2 paragraph proposal outline that addresses the contract requirements, highlights relevant qualifications, and differentiators"""

        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=system_instruction
        )
        
        response = model.generate_content(prompt)
        content = response.text
        
        # Try to split into summary and proposal
        if "proposal outline" in content.lower() or "2." in content:
            parts = content.split('\n\n', 1)
            if len(parts) == 2:
                return {
                    'summary': parts[0],
                    'bid_proposal': parts[1]
                }
        
        return {
            'summary': content[:len(content)//2],
            'bid_proposal': content[len(content)//2:]
        }
        
    except Exception as e:
        return {
            'summary': f"Error generating Google AI response: {str(e)}",
            'bid_proposal': "Unable to generate proposal."
        }


def generate_openai_response(contract_data: Dict, company_profile: Optional[Dict] = None) -> Dict[str, str]:
    """
    Generate contract summary and bid proposal using GPT-4
    
    Args:
        contract_data: Dictionary containing contract information
        company_profile: Optional dictionary with company details for personalized proposals
        
    Returns:
        Dictionary with 'summary' and 'bid_proposal' keys
    """
    try:
        # Build company context if provided
        company_context = ""
        if company_profile and company_profile.get('company_name'):
            company_context = f"""

When creating the proposal outline, incorporate these company strengths and details:
Company Name: {company_profile.get('company_name', '')}
Years of Experience: {company_profile.get('experience', '')}
Key Capabilities: {company_profile.get('capabilities', '')}
Certifications: {company_profile.get('certifications', '')}
Past Performance: {company_profile.get('past_performance', '')}
Competitive Advantages: {company_profile.get('competitive_advantages', '')}

Tailor the proposal to highlight how this company's specific strengths match the contract requirements."""
        
        prompt = f"""You are a professional contract analyst and bid writer. Analyze this government contract opportunity:

Title: {contract_data['title']}
Department: {contract_data['department']}
Posted: {contract_data['posted_date']}
Deadline: {contract_data['response_deadline']}
Description: {contract_data['description']}{company_context}

Please provide:
1. A concise summary of the key requirements, scope, and timeline
2. A brief 1-2 paragraph proposal outline that addresses the contract requirements, highlights relevant qualifications, and differentiators"""

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional government contract analyst and bid writer with expertise in crafting winning proposals."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024
        )
        
        content = response.choices[0].message.content
        
        # Try to split into summary and proposal
        if "proposal outline" in content.lower() or "2." in content:
            parts = content.split('\n\n', 1)
            if len(parts) == 2:
                return {
                    'summary': parts[0],
                    'bid_proposal': parts[1]
                }
        
        return {
            'summary': content[:len(content)//2],
            'bid_proposal': content[len(content)//2:]
        }
        
    except Exception as e:
        return {
            'summary': f"Error generating OpenAI response: {str(e)}",
            'bid_proposal': "Unable to generate proposal."
        }


def process_contracts(keyword: str, company_name: str = "", experience: str = "", 
                      capabilities: str = "", certifications: str = "", 
                      past_performance: str = "", competitive_advantages: str = "") -> str:
    """
    Main processing function that fetches contracts and generates comparisons
    
    Args:
        keyword: Search term for contracts
        company_name: Optional company name for personalized proposals
        experience: Years/description of experience
        capabilities: Key capabilities and services
        certifications: Relevant certifications
        past_performance: Past performance highlights
        competitive_advantages: Competitive advantages and differentiators
        
    Returns:
        HTML formatted string with results
    """
    if not keyword or keyword.strip() == "":
        return "<p style='color: red;'>Please enter a search keyword.</p>"
    
    # Build company profile if provided
    company_profile = None
    if company_name and company_name.strip():
        company_profile = {
            'company_name': company_name,
            'experience': experience,
            'capabilities': capabilities,
            'certifications': certifications,
            'past_performance': past_performance,
            'competitive_advantages': competitive_advantages
        }
    
    # Fetch contracts
    contracts = fetch_sam_contracts(keyword, limit=3)
    
    # Build HTML output
    html_output = f"<h2>Search Results for: <em>{keyword}</em></h2>"
    
    for idx, contract in enumerate(contracts, 1):
        html_output += f"""
        <div style='border: 2px solid #4CAF50; padding: 20px; margin: 20px 0; border-radius: 10px; background-color: #f9f9f9;'>
            <h3 style='color: #2E7D32; margin-top: 0;'>Contract {idx}: {contract['title']}</h3>
            <div style='background-color: #e8f5e9; padding: 10px; border-radius: 5px; margin: 10px 0;'>
                <p style='color: #000; margin: 5px 0;'><strong style='color: #1B5E20;'>Notice ID:</strong> {contract['notice_id']}</p>
                <p style='color: #000; margin: 5px 0;'><strong style='color: #1B5E20;'>Department:</strong> {contract['department']}</p>
                <p style='color: #000; margin: 5px 0;'><strong style='color: #1B5E20;'>Posted:</strong> {contract['posted_date']}</p>
                <p style='color: #000; margin: 5px 0;'><strong style='color: #1B5E20;'>Deadline:</strong> {contract['response_deadline']}</p>
            </div>
        """
        
        # Only generate AI responses if we have valid contracts
        if contract['notice_id'] != 'N/A' and 'Error' not in contract['title']:
            html_output += "<p style='color: #666; font-style: italic;'><em>Generating AI analysis...</em></p>"
            
            # Generate responses from both LLMs with company profile
            google_response = generate_google_response(contract, company_profile)
            openai_response = generate_openai_response(contract, company_profile)
            
            # Display side-by-side comparison
            html_output += """
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;'>
                <div style='background-color: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;'>
                    <h4 style='color: #1B5E20; margin-top: 0;'>🤖 Google Gemini Analysis</h4>
                    <h5 style='color: #2E7D32; margin-bottom: 8px;'>Summary:</h5>
                    <p style='font-size: 14px; color: #000; line-height: 1.6;'>{}</p>
                    <h5 style='color: #2E7D32; margin-top: 15px; margin-bottom: 8px;'>Proposal Outline:</h5>
                    <p style='font-size: 14px; color: #000; line-height: 1.6;'>{}</p>
                </div>
                <div style='background-color: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 4px solid #2196F3;'>
                    <h4 style='color: #0D47A1; margin-top: 0;'>🤖 GPT-4 Analysis</h4>
                    <h5 style='color: #1565C0; margin-bottom: 8px;'>Summary:</h5>
                    <p style='font-size: 14px; color: #000; line-height: 1.6;'>{}</p>
                    <h5 style='color: #1565C0; margin-top: 15px; margin-bottom: 8px;'>Proposal Outline:</h5>
                    <p style='font-size: 14px; color: #000; line-height: 1.6;'>{}</p>
                </div>
            </div>
            """.format(
                google_response['summary'].replace('\n', '<br>'),
                google_response['bid_proposal'].replace('\n', '<br>'),
                openai_response['summary'].replace('\n', '<br>'),
                openai_response['bid_proposal'].replace('\n', '<br>')
            )
        else:
            html_output += f"<p style='color: #666; font-style: italic;'>{contract['description']}</p>"
        
        html_output += "</div>"
    
    return html_output


def create_gradio_interface():
    """
    Create and launch the Gradio web interface
    """
    with gr.Blocks(title="SAM.gov Contract Agent", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🏛️ SAM.gov Contract Intelligence Agent
        
        Search for government contract opportunities and get AI-powered analysis from both Google Gemini and GPT-4.
        The agent will attempt to scrape live contracts from SAM.gov, and generate personalized proposals based on your company profile.
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🔍 Search Contracts")
                keyword_input = gr.Textbox(
                    label="Search Keyword",
                    placeholder="e.g., gardening, IT services, construction",
                    value="gardening",
                    lines=1
                )
                
                gr.Markdown("### 🏢 Company Profile (Optional)")
                gr.Markdown("*Provide your company details for personalized AI-generated proposals*")
                
                company_name = gr.Textbox(
                    label="Company Name",
                    placeholder="e.g., GreenScape Solutions LLC",
                    lines=1
                )
                
                experience = gr.Textbox(
                    label="Years of Experience / Background",
                    placeholder="e.g., 15 years providing commercial landscaping services",
                    lines=2
                )
                
                capabilities = gr.Textbox(
                    label="Key Capabilities & Services",
                    placeholder="e.g., Landscape design, irrigation systems, organic lawn care, tree services",
                    lines=3
                )
                
                certifications = gr.Textbox(
                    label="Certifications & Credentials",
                    placeholder="e.g., ISA Certified Arborist, LEED AP, Licensed Pest Applicator",
                    lines=2
                )
                
                past_performance = gr.Textbox(
                    label="Past Performance Highlights",
                    placeholder="e.g., Maintained 50+ federal facilities, 98% CPARS rating, $2M in completed projects",
                    lines=3
                )
                
                competitive_advantages = gr.Textbox(
                    label="Competitive Advantages",
                    placeholder="e.g., Veteran-owned, local presence, sustainable practices, 24/7 emergency response",
                    lines=3
                )
                
                search_btn = gr.Button("🚀 Generate Proposals", variant="primary", size="lg")
            
            with gr.Column(scale=2):
                output_html = gr.HTML(label="Results")
        
        search_btn.click(
            fn=process_contracts,
            inputs=[keyword_input, company_name, experience, capabilities, 
                   certifications, past_performance, competitive_advantages],
            outputs=output_html
        )
        
        gr.Markdown("""
        ---
        ### 💡 Tips & Important Notes:
        - **Live Scraping**: The agent attempts to scrape real contracts from SAM.gov (may fall back to samples)
        - **Personalized Proposals**: Fill in company profile for customized, realistic bid proposals
        - **AI Comparison**: See how Google Gemini vs GPT-4 approach the same opportunity differently
        - **About "Bids"**: The AI GENERATES proposal outlines for YOU to submit - it doesn't scrape existing bids
        - **Keywords to try**: "security services", "landscaping", "IT services", "cybersecurity", "construction"
        - **Save Results**: Copy AI-generated proposals and use as templates for your actual submissions
        
        **Note**: SAM.gov frequently updates their website structure. If scraping quality drops, check console 
        output and consider enabling debug mode in the code (line 86) to inspect the HTML being parsed.
        """)
    
    return demo


if __name__ == "__main__":
    print("🚀 Starting SAM.gov Contract Intelligence Agent...")
    print("=" * 60)
    print("📋 Required API Keys (check your .env file):")
    print("   ✓ GOOGLE_API_KEY")
    print("   ✓ OPENAI_API_KEY")
    print("\n🎯 Features:")
    print("   • Attempts to scrape live contracts from SAM.gov")
    print("   • Falls back to realistic sample data if needed")
    print("   • Personalized proposals based on your company profile")
    print("   • Dual AI analysis (Google Gemini + GPT-4)")
    print("\n🌐 Launching web interface...")
    print("=" * 60)
    
    demo = create_gradio_interface()
    demo.launch(share=False)

