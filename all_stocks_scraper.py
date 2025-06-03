import requests
from bs4 import BeautifulSoup
import csv
import time
import re

def scrape_stock_data(base_url="https://www.screener.in/screens/41897/all-bse-companies/?page=", start_page=1, max_pages=198):
   
    
    stocks_data = []
    page = start_page
    stock_counter = 1  # Start numbering from 1
    
    # Headers to mimic a real browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    while page <= max_pages:
        print(f"Progress: Page {page}/{max_pages} ({((page-1)/max_pages)*100:.1f}%)")
            
        url = f"{base_url}{page}"
        print(f"Scraping page {page}: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the data table
            table = soup.find('table', class_='data-table')
            
            if not table:
                print(f"No table found on page {page}")
                break
            
         
            rows = table.find_all('tr', attrs={'data-row-company-id': True})
            
            if not rows:
                print(f"No data rows found on page {page}, but continuing...")
                page += 1
                continue
            
            page_stocks = []
            for row in rows:
                try:
                    # Extract company name and URL 
                    name_cells = row.find_all('td', class_='text')
                    if len(name_cells) < 2:
                        continue
                    

                    name_cell = name_cells[1]
                    link = name_cell.find('a')
                    
                    if link:
                        company_name = link.get_text(strip=True)
                        relative_url = link.get('href')
                        
                        # Construct full URL
                        if relative_url.startswith('/'):
                            full_url = f"https://www.screener.in{relative_url}"
                        else:
                            full_url = relative_url
                        
                        stock_data = {
                            'S.No': stock_counter, 
                            'Name': company_name,
                            'Url': full_url
                        }
                        
                        page_stocks.append(stock_data)
                        print(f"  Found: {stock_counter} - {company_name}")
                        stock_counter += 1 
                
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue
            
            if page_stocks:
                stocks_data.extend(page_stocks)
                print(f"Page {page}: Found {len(page_stocks)} stocks (Total: {len(stocks_data)})")
            else:
                print(f"No stocks found on page {page}, continuing...")
            

            if len(stocks_data) >= 4938:
                print(f"Reached expected total of 4938 stocks, stopping at page {page}")
                break
            
            page += 1
            
      
            time.sleep(2) 
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break
        except Exception as e:
            print(f"Unexpected error on page {page}: {e}")
            break
    
    return stocks_data

def save_to_csv(stocks_data, filename='stocks_data.csv'):
    """
    Save stock data to CSV file
    
    Args:
        stocks_data: List of dictionaries containing stock data
        filename: Output CSV filename
    """
    if not stocks_data:
        print("No data to save")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['S.No', 'Name', 'Url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for stock in stocks_data:
            writer.writerow(stock)
    
    print(f"Data saved to {filename}")
    print(f"Total stocks saved: {len(stocks_data)}")

def scrape_from_html_file(html_file_path):
    """
    Scrape stock data from a local HTML file (for testing)
    
    Args:
        html_file_path: Path to the HTML file
    """
    stocks_data = []
    
    with open(html_file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
    
    # Find the data table
    table = soup.find('table', class_='data-table')
    
    if not table:
        print("No table found in HTML file")
        return []
    
    # Find all data rows (excluding header rows)
    rows = table.find_all('tr', attrs={'data-row-company-id': True})
    
    for row in rows:
        try:
            # Extract serial number
            serial_cell = row.find('td', class_='text')
            if serial_cell:
                serial_no = serial_cell.get_text(strip=True).replace('.', '')
            else:
                continue
            

            name_cell = row.find_all('td', class_='text')[1]
            link = name_cell.find('a')
            
            if link:
                company_name = link.get_text(strip=True)
                relative_url = link.get('href')
                

                if relative_url.startswith('/'):
                    full_url = f"https://www.screener.in{relative_url}"
                else:
                    full_url = relative_url
                
                stock_data = {
                    'S.No': serial_no,
                    'Name': company_name,
                    'Url': full_url
                }
                
                stocks_data.append(stock_data)
                print(f"Found: {serial_no} - {company_name}")
        
        except Exception as e:
            print(f"Error processing row: {e}")
            continue
    
    return stocks_data

if __name__ == "__main__":

    print("Starting stock data scraping...")
    

    stocks_data = scrape_stock_data(
        base_url="https://www.screener.in/screens/41897/all-bse-companies/?page=",
        start_page=1,
        max_pages=198 
    )
    
    # Save to CSV
    if stocks_data:
        save_to_csv(stocks_data, 'all_bse_companies.csv')
        
        print(f"\n=== SCRAPING COMPLETE ===")
        print(f"Total stocks scraped: {len(stocks_data)}")
        print(f"Expected: 4938 stocks from 198 pages")
        print(f"CSV saved as: all_bse_companies.csv")
        

        print(f"\nFirst 10 entries:")
        print("S.No\tName\t\t\tUrl")
        print("-" * 80)
        for i, stock in enumerate(stocks_data[:10]):
            name_display = stock['Name'][:20] + "..." if len(stock['Name']) > 20 else stock['Name']
            print(f"{stock['S.No']}\t{name_display:<20}\t{stock['Url']}")
        
        print("\n... (continuing to stock 4938)")
        print(f"\nLast 3 entries:")
        print("S.No\tName\t\t\tUrl")
        print("-" * 80)
        for stock in stocks_data[-3:]:
            name_display = stock['Name'][:20] + "..." if len(stock['Name']) > 20 else stock['Name']
            print(f"{stock['S.No']}\t{name_display:<20}\t{stock['Url']}")
        
        print(f"\nAll data saved to: all_bse_companies.csv")
    
