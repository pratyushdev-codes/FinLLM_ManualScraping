import requests
from bs4 import BeautifulSoup
import re
import subprocess
import os
import platform
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time

def find_chrome_profiles():
    """Find all available Chrome profiles and their display names"""
    system = platform.system()
    
    if system == "Windows":
        user_data_dir = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
    elif system == "Darwin":  # macOS
        user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    elif system == "Linux":
        user_data_dir = os.path.expanduser("~/.config/google-chrome")
    else:
        print(f"Unsupported operating system: {system}")
        return []
    
    profiles = []
    
    if os.path.exists(user_data_dir):
        # Check for Default profile
        default_path = os.path.join(user_data_dir, "Default")
        if os.path.exists(default_path):
            profiles.append(("Default", "Person 1 (Default)"))
        
        # Check for other profiles
        for item in os.listdir(user_data_dir):
            if item.startswith("Profile "):
                item_path = os.path.join(user_data_dir, item)
                if os.path.isdir(item_path):
                    # Try to read the profile name from preferences
                    prefs_file = os.path.join(item_path, "Preferences")
                    display_name = item
                    if os.path.exists(prefs_file):
                        try:
                            import json
                            with open(prefs_file, 'r', encoding='utf-8') as f:
                                prefs = json.load(f)
                                if 'profile' in prefs and 'name' in prefs['profile']:
                                    display_name = prefs['profile']['name']
                        except:
                            pass
                    profiles.append((item, display_name))
    
    return profiles

def open_chrome_with_profile_subprocess(profile_directory="Default"):
    """Open Chrome with a specific profile using subprocess"""
    system = platform.system()
    
    if system == "Windows":
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    elif system == "Darwin":  # macOS
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif system == "Linux":
        chrome_path = "/usr/bin/google-chrome"
    else:
        print(f"Unsupported operating system: {system}")
        return
    
    try:
        cmd = [chrome_path, f"--profile-directory={profile_directory}", "https://www.screener.in/company/TATAMOTORS/consolidated/"]
        subprocess.Popen(cmd)
        print(f"Chrome opened with profile: {profile_directory}")
    except FileNotFoundError:
        print(f"Chrome not found at: {chrome_path}")
        if system == "Windows":
            try:
                chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                cmd = [chrome_path, f"--profile-directory={profile_directory}", "https://www.screener.in/company/TATAMOTORS/consolidated/"]
                subprocess.Popen(cmd)
                print(f"Chrome opened with profile: {profile_directory}")
            except FileNotFoundError:
                print("Chrome not found in standard locations")
    except Exception as e:
        print(f"Error opening Chrome: {e}")

def scrape_annual_reports(url="https://www.screener.in/company/TATAMOTORS/consolidated/"):
    """Scrape annual report links from the given URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Fetching annual reports from: {url}")
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Find the annual reports section
        annual_reports_section = soup.find('div', class_='documents annual-reports flex-column')
        
        if not annual_reports_section:
            print("Could not find annual reports section")
            return []
        
        # Find all report links
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

def download_annual_reports(report_links, download_dir="annual_reports"):
    """Download all annual reports to the specified directory"""
    if not report_links:
        print("No report links to download")
        return
    
    # Create directory if it doesn't exist
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
            
            # Create a safe filename
            safe_year = re.sub(r'[^\w\s-]', '', year).strip()
            safe_year = re.sub(r'[-\s]+', '_', safe_year)
            
            # Determine file extension based on URL
            if url.endswith('.pdf'):
                file_extension = '.pdf'
            elif url.endswith('.zip'):
                file_extension = '.zip'
            else:
                # Try to determine from URL or default to .pdf
                file_extension = '.pdf'
            
            filename = f"{safe_year}_{source}{file_extension}"
            filepath = os.path.join(download_dir, filename)
            
            # Skip if file already exists
            if os.path.exists(filepath):
                print(f"  File already exists: {filename}")
                successful_downloads += 1
                continue
            
            # Download the file
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save the file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(filepath)
            print(f"  Downloaded: {filename} ({file_size:,} bytes)")
            successful_downloads += 1
            
            # Add a small delay to be respectful to the server
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

def scrape_tata_motors_data():
    """Scrape using requests (without browser profile)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        r = requests.get('https://www.screener.in/company/TATAMOTORS/consolidated/', headers=headers)
        r.raise_for_status()  
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Extract financial ratios
        financial_data = extract_financial_data(soup)
        
        # Extract shareholding data
        shareholding_data = extract_shareholding_data(soup)
        
        return {
            'financial_ratios': financial_data,
            'shareholding_pattern': shareholding_data
        }
    
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the webpage: {e}")
        return None

def extract_financial_data(soup):
    """Extract financial ratios from BeautifulSoup object"""
    ratios_list = soup.find('ul', id='top-ratios')
    
    if not ratios_list:
        print("Could not find the ratios list on the page")
        return None
    
    financial_data = {}
    ratio_items = ratios_list.find_all('li', class_='flex flex-space-between')
    
    for item in ratio_items:
        name_span = item.find('span', class_='name')
        if name_span:
            name = name_span.get_text(strip=True)
            
            value_span = item.find('span', class_='nowrap value')
            if value_span:
                value_text = value_span.get_text(strip=True)
                financial_data[name] = value_text
    
    return financial_data

def extract_shareholding_data(soup):
    """Extract shareholding pattern data from BeautifulSoup object"""
    # Find the shareholding table
    shareholding_div = soup.find('div', id='quarterly-shp')
    
    if not shareholding_div:
        print("Could not find the shareholding pattern table")
        return None
    
    table = shareholding_div.find('table', class_='data-table')
    
    if not table:
        print("Could not find the shareholding data table")
        return None
    
    # Extract headers (dates)
    headers = []
    header_row = table.find('thead').find('tr')
    th_elements = header_row.find_all('th')
    
    for th in th_elements:
        header_text = th.get_text(strip=True)
        if header_text and header_text != "":
            headers.append(header_text)
    
    # Extract data rows
    shareholding_data = {}
    tbody = table.find('tbody')
    rows = tbody.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 1:
            # Get the row label
            first_cell = cells[0]
            
            # Check if it's a button (for shareholding categories)
            button = first_cell.find('button')
            if button:
                # Extract category name from button text
                button_text = button.get_text(strip=True)
                category = button_text.replace('+', '').strip()
            else:
                # For rows like "No. of Shareholders"
                category = first_cell.get_text(strip=True)
            
            # Extract values for each quarter
            values = []
            for i in range(1, len(cells)):
                cell_value = cells[i].get_text(strip=True)
                values.append(cell_value)
            
            # Store the data with headers
            row_data = {}
            for j, header in enumerate(headers[1:]):  # Skip first header which is empty
                if j < len(values):
                    row_data[header] = values[j]
            
            shareholding_data[category] = row_data
    
    return shareholding_data

def display_financial_data(data):
    """Display financial ratios"""
    if not data:
        print("No financial data to display")
        return
    
    print("TATA MOTORS FINANCIAL RATIOS")
    print("-" * 50)
    
    for key, value in data.items():
        print(f"{key:20}: {value}")
    
    print()

def display_shareholding_data(data):
    """Display shareholding pattern data"""
    if not data:
        print("No shareholding data to display")
        return
    
    print("TATA MOTORS SHAREHOLDING PATTERN")
    print("-" * 50)
    
    # Get all quarters (assuming all categories have the same quarters)
    if data:
        first_category = list(data.keys())[0]
        quarters = list(data[first_category].keys())
        
        # Display as a formatted table
        print(f"{'Category':<15}", end="")
        for quarter in quarters:
            print(f"{quarter:>12}", end="")
        print()
        
        print("-" * 80)
        
        for category, quarterly_data in data.items():
            print(f"{category:<15}", end="")
            for quarter in quarters:
                value = quarterly_data.get(quarter, "N/A")
                print(f"{value:>12}", end="")
            print()
    
    print()

def create_shareholding_dataframe(data):
    """Convert shareholding data to pandas DataFrame for easier analysis"""
    if not data:
        return None
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(data).T  # Transpose to have categories as rows
        
        # Clean percentage values for numerical analysis
        numeric_df = df.copy()
        for col in df.columns:
            for idx in df.index:
                if idx != "No. of Shareholders":  # Keep shareholder count as is
                    value = df.loc[idx, col]
                    if isinstance(value, str) and '%' in value:
                        # Remove % and convert to float
                        try:
                            numeric_df.loc[idx, col] = float(value.replace('%', ''))
                        except:
                            numeric_df.loc[idx, col] = value
                else:
                    # For shareholder count, remove commas
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

def extract_numeric_values(data):
    """Extract just the numeric values from the financial data"""
    if not data:
        return None
    
    numeric_data = {}
    
    for key, value in data.items():
        numbers = re.findall(r'[\d,]+\.?\d*', value)
        if numbers:
            if '/' in value and len(numbers) >= 2:
                numeric_data[key] = f"{numbers[0]} / {numbers[1]}"
            else:
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

def analyze_shareholding_trends(df):
    """Analyze trends in shareholding data"""
    if df is None:
        return None
    
    trend_analysis = {}
    
    # Get latest vs earliest data for percentage categories
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
        
        # Shareholder count change
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

def save_data_to_txt(all_data, filename="tata_motors_data.txt"):
    """Save all data to a clean text file without decorative lines"""
    if not all_data:
        print("No data to save")
        return False
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # Header
            f.write("TATA MOTORS COMPLETE FINANCIAL DATA\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("Source: Screener.in (TATAMOTORS/consolidated)\n\n")
            
            # Financial Ratios
            financial_data = all_data.get('financial_ratios')
            if financial_data:
                f.write("FINANCIAL RATIOS\n")
                f.write("-" * 30 + "\n")
                for key, value in financial_data.items():
                    f.write(f"{key:20}: {value}\n")
                f.write("\n")
                
                # Numeric values
                numeric_values = extract_numeric_values(financial_data)
                if numeric_values:
                    f.write("NUMERIC VALUES (FOR CALCULATIONS)\n")
                    f.write("-" * 30 + "\n")
                    for key, value in numeric_values.items():
                        f.write(f"{key:20}: {value}\n")
                    f.write("\n")
            
            # Shareholding Pattern
            shareholding_data = all_data.get('shareholding_pattern')
            if shareholding_data:
                f.write("SHAREHOLDING PATTERN\n")
                f.write("-" * 30 + "\n")
                
                # Get quarters
                first_category = list(shareholding_data.keys())[0]
                quarters = list(shareholding_data[first_category].keys())
                
                # Write header row
                f.write(f"{'Category':<15}")
                for quarter in quarters:
                    f.write(f"{quarter:>12}")
                f.write("\n")
                
                # Write separator
                f.write("-" * (15 + 12 * len(quarters)) + "\n")
                
                # Write data rows
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
            
            # Key observations
            f.write("\nKEY OBSERVATIONS\n")
            f.write("-" * 30 + "\n")
            f.write("1. Financial metrics show company performance\n")
            f.write("2. Shareholding pattern indicates investor sentiment\n")
            f.write("3. FII/DII movements suggest institutional interest\n")
            f.write("4. Promoter holding changes reflect management decisions\n")
            f.write("5. Retail participation shows market accessibility\n")
        
        print(f"Data successfully saved to {filename}")
        return True
        
    except Exception as e:
        print(f"Error saving to text file: {e}")
        return False

def display_trend_analysis(trends):
    """Display trend analysis in console"""
    if not trends:
        return
    
    print("SHAREHOLDING TREND ANALYSIS")
    print("-" * 50)
    print(f"Period: {trends['period']}")
    print("\nChanges:")
    print("-" * 40)
    
    for category, change_data in trends['changes'].items():
        if 'error' not in change_data:
            change = change_data['change']
            from_val = change_data['from']
            to_val = change_data['to']
            print(f"{category:<15}: {change:+6.2f}% ({from_val:.2f}% → {to_val:.2f}%)")
    
    # Shareholder count
    if 'shareholder_change' in trends and 'error' not in trends['shareholder_change']:
        sh_change = trends['shareholder_change']
        print(f"\nShareholder Count Change: {sh_change['absolute']:+,} ({sh_change['percentage']:+.1f}%)")
        print(f"From: {sh_change['from']:,} → To: {sh_change['to']:,}")

# Main execution
if __name__ == "__main__":
    print("Tata Motors Complete Data Scraper")
    print("-" * 50)
    
    # Find Chrome profiles
    print("Available Chrome Profiles:")
    profiles = find_chrome_profiles()
    
    if profiles:
        for i, (directory, display_name) in enumerate(profiles, 1):
            print(f"{i}. {display_name} ({directory})")
        
        # Look for 'soul' profile
        soul_profile = None
        for directory, display_name in profiles:
            if "soul" in display_name.lower():
                soul_profile = directory
                print(f"\nFound 'soul' profile: {display_name} ({directory})")
                break
        
        if not soul_profile:
            print("\nProfile with 'soul' not found. Using Default profile.")
            soul_profile = "Default"
    else:
        soul_profile = "Default"
    
    # Choose action
    print(f"\nUsing profile: {soul_profile}")
    choice = input("\nWhat would you like to do?\n1. Open Chrome with profile\n2. Scrape all data\n3. Download annual reports\n4. Scrape data + Download reports\nEnter choice (1/2/3/4): ")
    
    if choice == "1":
        print("Opening Chrome with your profile...")
        open_chrome_with_profile_subprocess(soul_profile)
    
    elif choice == "2":
        print("Scraping complete data...")
        all_data = scrape_tata_motors_data()
        
        if all_data:
            # Display financial ratios
            financial_data = all_data.get('financial_ratios')
            if financial_data:
                display_financial_data(financial_data)
                
                # Show numeric values
                numeric_values = extract_numeric_values(financial_data)
                print("NUMERIC VALUES:")
                print("-" * 30)
                for key, value in numeric_values.items():
                    print(f"{key:20}: {value}")
                print()
            
            # Display shareholding data
            shareholding_data = all_data.get('shareholding_pattern')
            if shareholding_data:
                display_shareholding_data(shareholding_data)
                
                # Create DataFrame and analyze trends
                df = create_shareholding_dataframe(shareholding_data)
                if df is not None:
                    trends = analyze_shareholding_trends(df)
                    if trends:
                        display_trend_analysis(trends)
            
            # Save to text file
            print("\n" + "-" * 50)
            save_choice = input("Save complete data to text file? (y/n): ")
            if save_choice.lower() == 'y':
                filename = input("Enter filename (default: tata_motors_data.txt): ").strip()
                if not filename:
                    filename = "tata_motors_data.txt"
                
                if save_data_to_txt(all_data, filename):
                    print("Data saved successfully!")
                else:
                    print("Failed to save data")
            
            # Optional CSV save for shareholding data
            if shareholding_data:
                csv_choice = input("Also save shareholding data to CSV? (y/n): ")
                if csv_choice.lower() == 'y':
                    if df is not None:
                        csv_filename = "tata_motors_shareholding.csv"
                        df.to_csv(csv_filename)
                        print(f"Shareholding data saved to {csv_filename}")
        else:
            print("Failed to scrape data")
    
    elif choice == "3":
        print("Downloading annual reports...")
        report_links = scrape_annual_reports()
        if report_links:
            download_annual_reports(report_links)
        else:
            print("No annual reports found to download")
    
    elif choice == "4":
        print("Scraping complete data and downloading annual reports...")
        
        # First scrape the data
        all_data = scrape_tata_motors_data()
        
        if all_data:
            # Display financial ratios
            financial_data = all_data.get('financial_ratios')
            if financial_data:
                display_financial_data(financial_data)
                
                # Show numeric values
                numeric_values = extract_numeric_values(financial_data)
                print("NUMERIC VALUES:")
                print("-" * 30)
                for key, value in numeric_values.items():
                    print(f"{key:20}: {value}")
                print()
            
            # Display shareholding data
            shareholding_data = all_data.get('shareholding_pattern')
            if shareholding_data:
                display_shareholding_data(shareholding_data)
                
                # Create DataFrame and analyze trends
                df = create_shareholding_dataframe(shareholding_data)
                if df is not None:
                    trends = analyze_shareholding_trends(df)
                    if trends:
                        display_trend_analysis(trends)
            
            # Save to text file
            print("\n" + "-" * 50)
            save_choice = input("Save complete data to text file? (y/n): ")
            if save_choice.lower() == 'y':
                filename = input("Enter filename (default: tata_motors_data.txt): ").strip()
                if not filename:
                    filename = "tata_motors_data.txt"
                
                if save_data_to_txt(all_data, filename):
                    print("Data saved successfully!")
                else:
                    print("Failed to save data")
            
            # Optional CSV save for shareholding data
            if shareholding_data:
                csv_choice = input("Also save shareholding data to CSV? (y/n): ")
                if csv_choice.lower() == 'y':
                    if df is not None:
                        csv_filename = "tata_motors_shareholding.csv"
                        df.to_csv(csv_filename)
                        print(f"Shareholding data saved to {csv_filename}")
        
        # Now download annual reports
        print("\n" + "=" * 50)
        print("DOWNLOADING ANNUAL REPORTS")
        print("=" * 50)
        report_links = scrape_annual_reports()
        if report_links:
            download_annual_reports(report_links)
        else:
            print("No annual reports found to download")
    
    else:
        print("Invalid choice!")