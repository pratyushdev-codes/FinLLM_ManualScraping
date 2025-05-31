import requests
from bs4 import BeautifulSoup
import re

def scrape_tata_motors_data():
    baseurl = 'https://www.screener.in/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    try:
        r = requests.get('https://www.screener.in/company/TATAMOTORS/consolidated/', headers=headers)
        r.raise_for_status()  
        
        soup = BeautifulSoup(r.text, 'html.parser')
        

        ratios_list = soup.find('ul', id='top-ratios')
        
        if not ratios_list:
            print("Could not find the ratios list on the page")
            return
        
        # Dictionary to store the scraped data
        financial_data = {}
        
        # Find all list items within the ratios list
        ratio_items = ratios_list.find_all('li', class_='flex flex-space-between')
        
        for item in ratio_items:
            # Get the name (left side)
            name_span = item.find('span', class_='name')
            if name_span:
                name = name_span.get_text(strip=True)
                
                # Get the value (right side)
                value_span = item.find('span', class_='nowrap value')
                if value_span:
                    # Extract the numeric value and any currency/percentage symbols
                    value_text = value_span.get_text(strip=True)
                    
                    # Clean up the value text and extract numbers
                    # Remove currency symbols and extra spaces
                    clean_value = re.sub(r'[₹\s]', '', value_text)
                    
                    financial_data[name] = value_text
        
        return financial_data
    
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the webpage: {e}")
        return None

def display_financial_data(data):
    if not data:
        print("No data to display")
        return
    
    print("=" * 50)
    print("TATA MOTORS FINANCIAL INFORMATION")
    print("=" * 50)
    
    for key, value in data.items():
        print(f"{key:15}: {value}")
    
    print("=" * 50)

def extract_numeric_values(data):
    """Extract just the numeric values from the scraped data"""
    if not data:
        return None
    
    numeric_data = {}
    
    for key, value in data.items():
        # Extract numbers from the value string
        numbers = re.findall(r'[\d,]+\.?\d*', value)
        if numbers:
            # Handle cases like "1,179 / 536" for High/Low
            if '/' in value and len(numbers) >= 2:
                numeric_data[key] = f"{numbers[0]} / {numbers[1]}"
            else:
                # Remove commas and convert to float if possible
                try:
                    clean_number = numbers[0].replace(',', '')
                    if '.' in clean_number:
                        numeric_data[key] = float(clean_number)
                    else:
                        numeric_data[key] = int(clean_number)
                except ValueError:
                    numeric_data[key] = numbers[0]
        else:
            numeric_data[key] = value
    
    return numeric_data

# Main execution
if __name__ == "__main__":
    print("Scraping Tata Motors financial data...")
    
    # Scrape the data
    scraped_data = scrape_tata_motors_data()
    
    if scraped_data:
        # Display the raw scraped data
        display_financial_data(scraped_data)
        
        # Extract and display numeric values
        numeric_values = extract_numeric_values(scraped_data)
        
        print("\nNUMERIC VALUES EXTRACTED:")
        print("=" * 30)
        for key, value in numeric_values.items():
            print(f"{key:15}: {value}")
    else:
        print("Failed to scrape data from the website")