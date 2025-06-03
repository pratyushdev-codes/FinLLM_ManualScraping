import requests
from bs4 import BeautifulSoup
import re
import os
import pandas as pd
from datetime import datetime
import time
from urllib.parse import urljoin


def scrape_annual_reports(url="https://www.screener.in/company/505343/"):
    """Scrape annual report links from the given URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Fetching annual reports from: {url}")
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        

        annual_reports_section = soup.find('div', class_='documents annual-reports flex-column')
        
        if not annual_reports_section:
            print("Could not find annual reports section")
            return []
        

        report_links = []
        link_list = annual_reports_section.find('ul', class_='list-links')
        
        if link_list:
            for li in link_list.find_all('li'):
                link = li.find('a', href=True)
                if link:
                    href = link['href']
                    # Get the financial year text
                    year_text = link.get_text(strip=True).split('\n')[0].strip()
                    
                    # Get the source (BSE/NSE)
                    source_div = link.find('div', class_='ink-600 smaller')
                    source = source_div.get_text(strip=True) if source_div else 'unknown'
                    
                    report_links.append({
                        'year': year_text,
                        'url': href,
                        'source': source
                    })
        
        print(f"Found {len(report_links)} annual reports")
        return report_links
        
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return []
    except Exception as e:
        print(f"Error parsing annual reports: {e}")
        return []


def scrape_credit_ratings(url="https://www.screener.in/company/TATAMOTORS/consolidated/"):
    """Scrape credit rating links from the given URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Fetching credit ratings from: {url}")
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        

        credit_ratings_section = soup.find('div', class_='documents credit-ratings flex-column')
        
        if not credit_ratings_section:
            print("Could not find credit ratings section")
            return []
        

        rating_links = []
        link_list = credit_ratings_section.find('ul', class_='list-links')
        
        if link_list:
            for li in link_list.find_all('li'):
                link = li.find('a', href=True)
                if link:
                    href = link['href']

                    rating_text = link.get_text(strip=True).split('\n')[0].strip()
                    

                    source_div = link.find('div', class_='ink-600 smaller')
                    date_source = source_div.get_text(strip=True) if source_div else 'unknown'
                    
                    rating_links.append({
                        'title': rating_text,
                        'url': href,
                        'date_source': date_source
                    })
        
        print(f"Found {len(rating_links)} credit ratings")
        return rating_links
        
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return []
    except Exception as e:
        print(f"Error parsing credit ratings: {e}")
        return []


def scrape_concalls(url="https://www.screener.in/company/TATAMOTORS/consolidated/"):
    """Scrape conference call links from the given URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Fetching concalls from: {url}")
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        

        concalls_section = soup.find('div', class_='documents concalls flex-column')
        
        if not concalls_section:
            print("Could not find concalls section")
            return []
        

        concall_links = []
        link_list = concalls_section.find('ul', class_='list-links')
        
        if link_list:
            for li in link_list.find_all('li'):

                li_text = li.get_text(strip=True)
                

                month_year_match = re.search(r'([A-Za-z]+)\s+(\d{4})', li_text)
                if month_year_match:
                    month = month_year_match.group(1)
                    year = month_year_match.group(2)
                    month_year = f"{month}_{year}"
                else:

                    month_year = "Unknown_Date"
                

                links = li.find_all('a', href=True)
                
                concall_data = {
                    'month_year': month_year,
                    'transcript': None,
                    'notes': None,
                    'ppt': None,
                    'rec': None  
                }
                
                for link in links:
                    link_text = link.get_text(strip=True).lower()
                    href = link['href']
                    
                    if 'transcript' in link_text:
                        concall_data['transcript'] = href
                    elif 'notes' in link_text:
                        concall_data['notes'] = href
                    elif 'ppt' in link_text:
                        concall_data['ppt'] = href
                    elif 'rec' in link_text:
                        concall_data['rec'] = href 
                
        
                if concall_data['transcript'] or concall_data['notes'] or concall_data['ppt']:
                    concall_links.append(concall_data)
        
        print(f"Found {len(concall_links)} concall entries")
        return concall_links
        
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return []
    except Exception as e:
        print(f"Error parsing concalls: {e}")
        return []


def download_concalls(concall_links, base_download_dir="Concalls"):
    """Download all concall documents to the specified directory structure"""
    if not concall_links:
        print("No concall links to download")
        return
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    successful_downloads = 0
    failed_downloads = 0
    

    os.makedirs(base_download_dir, exist_ok=True)
    print(f"Created/Using directory: {base_download_dir}")
    
    for i, concall in enumerate(concall_links, 1):
        month_year = concall['month_year']
        

        month_dir = os.path.join(base_download_dir, month_year)
        os.makedirs(month_dir, exist_ok=True)
        
        print(f"[{i}/{len(concall_links)}] Processing: {month_year}")
        

        file_types = ['transcript', 'notes', 'ppt'] 
        
        for file_type in file_types:
            url = concall.get(file_type)
            if url:
                try:
                    print(f"  Downloading {file_type}...")
                    

                    if url.endswith('.pdf'):
                        file_extension = '.pdf'
                    elif url.endswith('.html'):
                        file_extension = '.html'
                    elif 'pdf' in url.lower():
                        file_extension = '.pdf'
                    else:
                        file_extension = '.pdf'
                    
                    filename = f"{file_type}{file_extension}"
                    filepath = os.path.join(month_dir, filename)
                    
                    # Skip if file already exists
                    if os.path.exists(filepath):
                        print(f"    File already exists: {filename}")
                        successful_downloads += 1
                        continue
                    

                    response = requests.get(url, headers=headers, stream=True, timeout=30)
                    response.raise_for_status()
                    

                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    file_size = os.path.getsize(filepath)
                    print(f"    Downloaded: {filename} ({file_size:,} bytes)")
                    successful_downloads += 1
                    

                    time.sleep(1)
                    
                except requests.RequestException as e:
                    print(f"    Error downloading {file_type}: {e}")
                    failed_downloads += 1
                except Exception as e:
                    print(f"    Unexpected error for {file_type}: {e}")
                    failed_downloads += 1
            else:
                print(f"  No {file_type} link found")
    
    print(f"\nConcalls Download Summary:")
    print(f"  Successful: {successful_downloads}")
    print(f"  Failed: {failed_downloads}")


def download_credit_ratings(rating_links, download_dir="credit_ratings"):
    """Download all credit rating documents to the specified directory"""
    if not rating_links:
        print("No rating links to download")
        return
    

    os.makedirs(download_dir, exist_ok=True)
    print(f"Created/Using directory: {download_dir}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    successful_downloads = 0
    failed_downloads = 0
    
    for i, rating in enumerate(rating_links, 1):
        try:
            title = rating['title']
            url = rating['url']
            date_source = rating['date_source']
            
            print(f"[{i}/{len(rating_links)}] Downloading: {title} - {date_source}")
            

            safe_date_source = re.sub(r'[^\w\s-]', '', date_source).strip()
            safe_date_source = re.sub(r'[-\s]+', '_', safe_date_source)
            

            if url.endswith('.pdf'):
                file_extension = '.pdf'
            elif url.endswith('.html'):
                file_extension = '.html'
            elif 'pdf' in url.lower():
                file_extension = '.pdf'
            elif 'html' in url.lower():
                file_extension = '.html'
            else:

                if 'crisil' in url.lower():
                    file_extension = '.html'
                elif 'care' in url.lower() or 'icra' in url.lower():
                    file_extension = '.pdf'
                else:
                    file_extension = '.html'
            
            filename = f"{safe_date_source}_rating{file_extension}"
            filepath = os.path.join(download_dir, filename)
            

            if os.path.exists(filepath):
                print(f"  File already exists: {filename}")
                successful_downloads += 1
                continue
            

            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(filepath)
            print(f"  Downloaded: {filename} ({file_size:,} bytes)")
            successful_downloads += 1
            

            time.sleep(1)
            
        except requests.RequestException as e:
            print(f"  Error downloading {title}: {e}")
            failed_downloads += 1
        except Exception as e:
            print(f"  Unexpected error for {title}: {e}")
            failed_downloads += 1
    
    print(f"\nCredit Ratings Download Summary:")
    print(f"  Successful: {successful_downloads}")
    print(f"  Failed: {failed_downloads}")
    print(f"  Total: {len(rating_links)}")


def download_annual_reports(report_links, download_dir="annual_reports"):
    """Download all annual reports to the specified directory"""
    if not report_links:
        print("No report links to download")
        return
    

    os.makedirs(download_dir, exist_ok=True)
    print(f"Created/Using directory: {download_dir}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    successful_downloads = 0
    failed_downloads = 0
    
    for i, report in enumerate(report_links, 1):
        try:
            year = report['year']
            url = report['url']
            source = report['source']
            
            print(f"[{i}/{len(report_links)}] Downloading: {year} from {source}")
            

            safe_year = re.sub(r'[^\w\s-]', '', year).strip()
            safe_year = re.sub(r'[-\s]+', '_', safe_year)
            

            if url.endswith('.pdf'):
                file_extension = '.pdf'
            elif url.endswith('.zip'):
                file_extension = '.zip'
            else:
                file_extension = '.pdf'
            
            filename = f"{safe_year}_{source}{file_extension}"
            filepath = os.path.join(download_dir, filename)
            

            if os.path.exists(filepath):
                print(f"  File already exists: {filename}")
                successful_downloads += 1
                continue
            

            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(filepath)
            print(f"  Downloaded: {filename} ({file_size:,} bytes)")
            successful_downloads += 1
            

            time.sleep(1)
            
        except requests.RequestException as e:
            print(f"  Error downloading {year}: {e}")
            failed_downloads += 1
        except Exception as e:
            print(f"  Unexpected error for {year}: {e}")
            failed_downloads += 1
    
    print(f"\nDownload Summary:")
    print(f"  Successful: {successful_downloads}")
    print(f"  Failed: {failed_downloads}")
    print(f"  Total: {len(report_links)}")


def scrape_shareholding_data():
    """Scrape shareholding pattern data from Tata Motors page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("Fetching shareholding data...")
        r = requests.get('https://www.screener.in/company/TATAMOTORS/consolidated/', headers=headers)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Extract shareholding data
        shareholding_data = extract_shareholding_data(soup)
        
        return shareholding_data
    
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the webpage: {e}")
        return None


def extract_shareholding_data(soup):
    """Extract shareholding pattern data from BeautifulSoup object"""

    shareholding_div = soup.find('div', id='quarterly-shp')
    
    if not shareholding_div:
        print("Could not find the shareholding pattern table")
        return None
    
    table = shareholding_div.find('table', class_='data-table')
    
    if not table:
        print("Could not find the shareholding data table")
        return None
    
    # Extract headers
    headers = []
    header_row = table.find('thead').find('tr')
    th_elements = header_row.find_all('th')
    
    for th in th_elements:
        header_text = th.get_text(strip=True)
        if header_text and header_text != "":
            headers.append(header_text)
    

    shareholding_data = {}
    tbody = table.find('tbody')
    rows = tbody.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 1:
            
            first_cell = cells[0]
            

            button = first_cell.find('button')
            if button:

                button_text = button.get_text(strip=True)
                category = button_text.replace('+', '').strip()
            else:

                category = first_cell.get_text(strip=True)
            

            values = []
            for i in range(1, len(cells)):
                cell_value = cells[i].get_text(strip=True)
                values.append(cell_value)
            

            row_data = {}
            for j, header in enumerate(headers[1:]): 
                if j < len(values):
                    row_data[header] = values[j]
            
            shareholding_data[category] = row_data
    
    return shareholding_data


def create_shareholding_dataframe(data):
    """Convert shareholding data to pandas DataFrame for easier analysis"""
    if not data:
        return None
    
    try:
       
        df = pd.DataFrame(data).T 
        

        numeric_df = df.copy()
        for col in df.columns:
            for idx in df.index:
                if idx != "No. of Shareholders": 
                    value = df.loc[idx, col]
                    if isinstance(value, str) and '%' in value:
          
                        try:
                            numeric_df.loc[idx, col] = float(value.replace('%', ''))
                        except:
                            numeric_df.loc[idx, col] = value
                else:
            
                    value = df.loc[idx, col]
                    if isinstance(value, str):
                        try:
                            numeric_df.loc[idx, col] = int(value.replace(',', ''))
                        except:
                            numeric_df.loc[idx, col] = value
        
        return numeric_df
    except Exception as e:
        print(f"Error creating DataFrame: {e}")
        return None


def analyze_shareholding_trends(df):
    """Analyze trends in shareholding data"""
    if df is None:
        return None
    
    trend_analysis = {}
    

    percentage_categories = [cat for cat in df.index if cat != "No. of Shareholders"]
    
    if len(df.columns) >= 2:
        latest_quarter = df.columns[-1]
        earliest_quarter = df.columns[0]
        
        trend_analysis['period'] = f"{earliest_quarter} to {latest_quarter}"
        trend_analysis['changes'] = {}
        
        for category in percentage_categories:
            try:
                latest_val = float(df.loc[category, latest_quarter])
                earliest_val = float(df.loc[category, earliest_quarter])
                change = latest_val - earliest_val
                trend_analysis['changes'][category] = {
                    'change': change,
                    'from': earliest_val,
                    'to': latest_val
                }
            except:
                trend_analysis['changes'][category] = {'error': 'Could not calculate change'}
        

        try:
            latest_shareholders = int(df.loc["No. of Shareholders", latest_quarter])
            earliest_shareholders = int(df.loc["No. of Shareholders", earliest_quarter])
            change_shareholders = latest_shareholders - earliest_shareholders
            change_percent = (change_shareholders / earliest_shareholders) * 100
            trend_analysis['shareholder_change'] = {
                'absolute': change_shareholders,
                'percentage': change_percent,
                'from': earliest_shareholders,
                'to': latest_shareholders
            }
        except:
            trend_analysis['shareholder_change'] = {'error': 'Could not calculate shareholder count change'}
    
    return trend_analysis


def save_shareholding_data_to_txt(shareholding_data, filename="tata_motors_shareholding.txt"):
    """Save shareholding data to a text file"""
    if not shareholding_data:
        print("No shareholding data to save")
        return False
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:

            f.write("TATA MOTORS COMPLETE FINANCIAL DATA\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("Source: Screener.in (TATAMOTORS/consolidated)\n\n")
            

            f.write("SHAREHOLDING PATTERN\n")
            f.write("-" * 30 + "\n")
            

            first_category = list(shareholding_data.keys())[0]
            quarters = list(shareholding_data[first_category].keys())
            

            f.write(f"{'Category':<15}")
            for quarter in quarters:
                f.write(f"{quarter:>12}")
            f.write("\n")
            

            f.write("-" * (15 + 12 * len(quarters)) + "\n")
            

            for category, quarterly_data in shareholding_data.items():
                f.write(f"{category:<15}")
                for quarter in quarters:
                    value = quarterly_data.get(quarter, "N/A")
                    f.write(f"{value:>12}")
                f.write("\n")
            f.write("\n")
            
            # Trend Analysis
            df = create_shareholding_dataframe(shareholding_data)
            if df is not None:
                trends = analyze_shareholding_trends(df)
                if trends:
                    f.write("SHAREHOLDING TREND ANALYSIS\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"Period: {trends['period']}\n\n")
                    
                    f.write("Changes:\n")
                    for category, change_data in trends['changes'].items():
                        if 'error' not in change_data:
                            change = change_data['change']
                            from_val = change_data['from']
                            to_val = change_data['to']
                            f.write(f"{category:<15}: {change:+6.2f}% ({from_val:.2f}% → {to_val:.2f}%)\n")
                    
                    # Shareholder count
                    if 'shareholder_change' in trends and 'error' not in trends['shareholder_change']:
                        sh_change = trends['shareholder_change']
                        f.write(f"\nShareholder Count Change: {sh_change['absolute']:+,} ({sh_change['percentage']:+.1f}%)\n")
                        f.write(f"From: {sh_change['from']:,} → To: {sh_change['to']:,}\n")
            

            f.write("\nKEY OBSERVATIONS\n")
            f.write("-" * 30 + "\n")
            f.write("1. Financial metrics show company performance\n")
            f.write("2. Shareholding pattern indicates investor sentiment\n")
            f.write("3. FII/DII movements suggest institutional interest\n")
            f.write("4. Promoter holding changes reflect management decisions\n")
            f.write("5. Retail participation shows market accessibility\n")
        
        print(f"Shareholding data successfully saved to {filename}")
        return True
        
    except Exception as e:
        print(f"Error saving to text file: {e}")
        return False


def main():
    """Main function to run the scraper"""
    print("TATA MOTORS DATA SCRAPER")
    print("=" * 50)
    

    print("1. Scraping shareholding pattern...")
    shareholding_data = scrape_shareholding_data()
    
    if shareholding_data:

        if save_shareholding_data_to_txt(shareholding_data):
            print("✓ Shareholding data saved successfully!")
        else:
            print("✗ Failed to save shareholding data")
    else:
        print("✗ Failed to scrape shareholding data")
    
    print("\n" + "=" * 50)
    

    print("2. Downloading annual reports...")
    report_links = scrape_annual_reports()
    if report_links:
        download_annual_reports(report_links)
        print("✓ Annual reports download completed!")
    else:
        print("✗ No annual reports found to download")
    
    print("\n" + "=" * 50)
    

    print("3. Downloading credit ratings...")
    rating_links = scrape_credit_ratings()
    if rating_links:
        download_credit_ratings(rating_links)
        print("✓ Credit ratings download completed!")
    else:
        print("✗ No credit ratings found to download")
    
    print("\n" + "=" * 50)
    

    print("4. Downloading concalls...")
    concall_links = scrape_concalls()
    if concall_links:
        download_concalls(concall_links)
        print("✓ Concalls download completed!")
    else:
        print("✗ No concalls found to download")
    
    print("\n" + "=" * 50)
    print("SCRAPING COMPLETED!")
    print("Files saved in:")
    print("  - tata_motors_shareholding.txt (shareholding data)")
    print("  - annual_reports/ (annual reports)")
    print("  - credit_ratings/ (credit rating documents)")
    print("  - Concalls/ (conference call materials organized by month_year)")
    print("\nConcalls Directory Structure:")
    print("  Concalls/")
    print("  ├── month_year/")
    print("  │   ├── transcript.pdf")
    print("  │   ├── notes.pdf (if available)")
    print("  │   └── ppt.pdf")
    print("  └── ...")


if __name__ == "__main__":
    main()