import investpy
import pandas as pd
import os

# Set display options
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

COUNTRY_CODES = {
    'netherlands': 'NL',
    'germany': 'DE',
    'france': 'FR',
    'switzerland': 'CH',
    'united states': 'US',
    'united kingdom': 'GB',
    'india': 'IN',
    'australia': 'AU',
    'china': 'CN',
    'brazil': 'BR',
    'japan': 'JP',
    'indonesia': 'ID',
    'south korea': 'KR'
}

def get_country_stocks(country):
    try:
        print(f"\nFetching stocks for {country.title()}...")
        stocks = investpy.stocks.get_stocks(country=country)
        print(f"Found {len(stocks)} stocks before filtering")
        
        country_code = COUNTRY_CODES.get(country.lower())
        if not country_code:
            raise Exception(f"No country code mapping found for {country}")
            
        stocks = stocks[stocks['isin'].str.startswith(country_code)]
        print(f"Found {len(stocks)} stocks after filtering for {country_code}")
        
        if len(stocks) == 0:
            raise Exception(f"No stocks found for {country} with ISIN starting with {country_code}")
            
        stocks['combined'] = stocks['name'] + ' | ' + stocks['isin']
        stocks = stocks[['country', 'name', 'isin', 'symbol', 'combined']]
        stocks = stocks.rename(columns={'name': 'company'})
        return stocks
    except Exception as e:
        print(f"Error fetching stocks for {country}: {str(e)}")
        return None

def process_stocks():
    csv_file = 'all_stocks.csv'
    summary = {
        'total_new_stocks': 0,
        'total_updated_stocks': 0,
        'countries_processed': 0,
        'countries_failed': 0,
        'country_stats': {}
    }

    all_stocks = pd.DataFrame()
    existing_data = pd.DataFrame()

    if os.path.exists(csv_file):
        existing_data = pd.read_csv(csv_file)
        print(f"\nExisting stocks in file: {len(existing_data)}")

    for country in COUNTRY_CODES.keys():
        country_stocks = get_country_stocks(country)
        if country_stocks is not None:
            summary['countries_processed'] += 1
            
            if len(existing_data) > 0:
                new_isins = set(country_stocks['isin']) - set(existing_data['isin'])
                updated_isins = set(country_stocks['isin']) & set(existing_data['isin'])
                
                summary['country_stats'][country] = {
                    'new': len(new_isins),
                    'updated': len(updated_isins)
                }
                
                summary['total_new_stocks'] += len(new_isins)
                summary['total_updated_stocks'] += len(updated_isins)
            else:
                summary['country_stats'][country] = {
                    'new': len(country_stocks),
                    'updated': 0
                }
                summary['total_new_stocks'] += len(country_stocks)
            
            all_stocks = pd.concat([all_stocks, country_stocks])
        else:
            summary['countries_failed'] += 1

    # Combine with existing data and remove duplicates
    if len(existing_data) > 0:
        all_stocks = pd.concat([existing_data, all_stocks])
    all_stocks = all_stocks.drop_duplicates(subset='isin', keep='last')
    
    # Save to CSV
    all_stocks.to_csv(csv_file, index=False)
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Countries processed successfully: {summary['countries_processed']}")
    print(f"Countries failed: {summary['countries_failed']}")
    print(f"Total new stocks added: {summary['total_new_stocks']}")
    print(f"Total stocks updated: {summary['total_updated_stocks']}")
    print("\nPer country statistics:")
    for country, stats in summary['country_stats'].items():
        print(f"{country.title()}: {stats['new']} new, {stats['updated']} updated")
    print(f"\nTotal stocks in database: {len(all_stocks)}")

if __name__ == "__main__":
    process_stocks()


