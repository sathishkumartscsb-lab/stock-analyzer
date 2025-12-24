import requests
from bs4 import BeautifulSoup

url = "https://www.screener.in/company/TCS/consolidated/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

sh_section = soup.find('section', id='shareholding')
if sh_section:
    # Find the row with Promoters
    # Try the exact logic from the codebase to see if it fails
    print("Testing original logic...")
    row_name = "Promoters"
    found_td = sh_section.find('td', string=lambda text: text and row_name.lower() in text.lower())
    print(f"Original logic found: {found_td}")

    print("\nInspecting Promoters row manually:")
    rows = sh_section.find_all('tr')
    for row in rows:
        if "Promoters" in row.text:
            print(f"Row HTML:\n{row.prettify()}")
            first_td = row.find('td')
            if first_td:
                print(f"First TD content: '{first_td.text}'")
                print(f"First TD string: '{first_td.string}'")
            break
