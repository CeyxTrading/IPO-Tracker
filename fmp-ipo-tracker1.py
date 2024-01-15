import pandas as pd
import requests
from datetime import datetime, timedelta
import os
import time
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
pd.options.mode.chained_assignment = None


# Create a colormap for heatmap
heatmap_colormap = plt.get_cmap('RdYlGn')  # Red to Yellow to Green colormap


#  Output directories
CACHE_DIR = "cache"
RESULTS_DIR = "results"


#  todo Set your API key
FMP_API_KEY = os.environ['FMP_API_KEY']


def get_ipo_calendar(start_date_str, end_date_str):
    try:
        file_name = f"ipo-calendar-{start_date_str}-to-{end_date_str}.csv"
        path = os.path.join(CACHE_DIR, file_name)
        if os.path.exists(path):
            ipo_calendar_df = pd.read_csv(path)
            ipo_calendar_df['date'] = pd.to_datetime(ipo_calendar_df['date'])
            return ipo_calendar_df
        else:
            url = f"https://financialmodelingprep.com/api/v3/ipo_calendar?from={start_date_str}&to={end_date_str}&apikey={FMP_API_KEY}"
            response = requests.get(url)
            if response.status_code == 200:
                response_json = response.json()
                ipo_calendar_df = pd.DataFrame(response_json)
                # Rename columns
                ipo_calendar_df = ipo_calendar_df.rename({'open': 'Open', 'high': 'High','low':'Low','close': 'Close','volume': 'Volume'})
                ipo_calendar_df.to_csv(path)
                return ipo_calendar_df
            else:
                print("Failed to fetch IPO calendar data: {response.status_code}")
    except Exception as ex:
        print(f"Failed to fetch IPO calendar data: {ex}")


def get_prices(symbol, interval, start_date_str, end_date_str):
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-chart/{interval}/{symbol}?from={start_date_str}&to={end_date_str}&apikey={FMP_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            response_json = response.json()
            prices_df = pd.DataFrame(response_json)
            prices_df.rename(
                columns={"date": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close",
                         "volume": "Volume"}, inplace=True)
            prices_df['Date'] = pd.to_datetime(prices_df['Date'])
            prices_df.sort_values(by='Date', inplace=True)
            prices_df.set_index('Date', inplace=True)
            return prices_df
        else:
            print("Failed to fetch price data: {response.status_code}")
    except Exception as ex:
        print(f"Failed to fetch price data: {ex}")


def resample_ohlc(data, freq):
    ohlc_dict = {
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }

    resampled = data.resample(freq).apply(ohlc_dict)
    return resampled


# Function to safely access series values
def safe_get(series, index, default=pd.NA):
    return series.iloc[index] if -len(series) <= index < len(series) else default


def calculate_performance(prices_df):
    # Calculate percentage change for minute data
    prices_df.dropna(inplace=True)
    prices_df['close_pct_1p'] = prices_df['Close'].pct_change() * 100
    minute_pct_changes = [safe_get(prices_df['close_pct_1p'], -i) for i in range(1, 5)]

    # Calculate hourly changes
    hourly_data_df = resample_ohlc(prices_df, 'H')
    hourly_data_df.dropna(inplace=True)
    hourly_data_df['close_pct_1p'] = hourly_data_df['Close'].pct_change() * 100
    hourly_pct_changes = [safe_get(hourly_data_df['close_pct_1p'], -i) for i in range(1, 5)]

    # Calculate daily changes
    daily_data_df = resample_ohlc(prices_df, 'D')
    daily_data_df.dropna(inplace=True)
    daily_data_df['close_pct_1p'] = daily_data_df['Close'].pct_change() * 100
    daily_pct_changes = [safe_get(daily_data_df['close_pct_1p'], -i) for i in range(1, 5)]

    # Calculate weekly changes
    weekly_data_df = resample_ohlc(prices_df, 'W')
    weekly_data_df.dropna(inplace=True)
    weekly_data_df['close_pct_1p'] = weekly_data_df['Close'].pct_change() * 100
    weekly_pct_changes = [safe_get(weekly_data_df['close_pct_1p'], -i) for i in range(1, 5)]

    # Create a DataFrame for the changes
    change_data_df = pd.DataFrame({
        'Δ 1 Min T -1': minute_pct_changes[0],
        'Δ 1 Min T -2': minute_pct_changes[1],
        'Δ 1 Min T -3': minute_pct_changes[2],
        'Δ 1 Min T -4': minute_pct_changes[3],
        'Δ 1 Hour T -1': hourly_pct_changes[0],
        'Δ 1 Hour T -2': hourly_pct_changes[1],
        'Δ 1 Hour T -3': hourly_pct_changes[2],
        'Δ 1 Hour T -4': hourly_pct_changes[3],
        'Δ 1 Day T -1': daily_pct_changes[0],
        'Δ 1 Day T -2': daily_pct_changes[1],
        'Δ 1 Day T -3': daily_pct_changes[2],
        'Δ 1 Day T -4': daily_pct_changes[3],
        'Δ 1 Week T -1': weekly_pct_changes[0],
        'Δ 1 Week T -2': weekly_pct_changes[1],
        'Δ 1 Week T -3': weekly_pct_changes[2],
        'Δ 1 Week T -4': weekly_pct_changes[3],
    }, index=[0])

    return change_data_df


def generate_html_string(data, data_columns):
    html = []
    html.append("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <!-- Refresh the page every 60 seconds -->
        <meta http-equiv="refresh" content="60">
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
        <title>IPO Price Tracker</title>
        <style>
            .percent-change {
                color: #fff; /* White text color */
            }
        .sticky-header th {
            position: sticky;
            top: 0;
            background-color: #fff; /* Background color for the sticky header */
            font-size: 10px;
            font-weight: bold;
        }
        .table-container {
            overflow-y: auto; /* Add scrolling to the table */
            max-height: 1024px; /* Adjust height as needed */
            padding: 24px;
        }
        .table td {
            font-size: 10px; /* Smaller font size for table rows */
        }
        </style>
    </head>
    <body>
        <div class="table-container">
            <h2 class="mt-5">IPO Price Changes</h2>
            <table class="table table-striped sticky-header">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Company</th>
                        <th>Date</th>""")

    for col_name in data_columns:
        html.append(f"<th>{col_name}</th>")
    html.append("</tr></thead><tbody>")

    for index, row in data.iterrows():
        html.append("<tr>")
        html.append(f"<td><a href='https://finance.yahoo.com/quote/{row['Symbol']}' target='_blank'>{row['Symbol']}</a></td>")
        html.append(f"<td><a href='https://finance.yahoo.com/quote/{row['Symbol']}' target='_blank'>{row['Company']}</a></td>")
        html.append(f"<td>{row['Date']}</td>")
        for col_name in data_columns:
            value = row[col_name]
            color_value = row.get(col_name + '_color', '#fff')
            html.append(f"<td class='percent-change' style='background-color: {color_value}'>{round(value, 2)}%</td>")
        html.append("</tr>")

    html.append("""
            </tbody>
        </table>
    </div>
    </body>
    </html>
    """)

    return ''.join(html)


def generate_html_report(data, data_columns):
    print("Generating HTML report...")
    html_content = generate_html_string(data, data_columns)

    # Write the HTML report
    today_date_str = datetime.today().strftime('%Y-%m-%d')
    file_name = f"ipo_price_tracker-{today_date_str}.html"
    with open(os.path.join(RESULTS_DIR, file_name), 'w', encoding='utf-8') as file:
        file.write(html_content)


def get_min_max_ranges(dataframe):
    ranges = {}
    for col in dataframe.columns:
        # Skip non-numeric columns
        if col in ['Symbol', 'Company', 'Date'] or col.endswith('_color'):
            continue

        min_val = dataframe[col].min()
        max_val = dataframe[col].max()
        ranges[col] = (min_val, max_val)

    return ranges


def percent_change_to_color(value, min_val, max_val):
    # Normalize the value between 0 and 1
    norm = Normalize(vmin=min_val, vmax=max_val)
    # Get the color from the colormap
    color = heatmap_colormap(norm(value))
    # Handle zero values
    hex_color = '#ccc'
    if value != 0:
        hex_color = matplotlib.colors.rgb2hex(color)
    # Convert the color to a hex string
    return hex_color


def add_color_to_df(df, change_ranges):
    for column_name in df.columns:
        if column_name.endswith('_color') or column_name in ['Symbol', 'Company', 'Date']:  # Skip color columns and non-data columns
            continue

        # Get min/max values for this column
        min_val, max_val = change_ranges[column_name]
        # Apply color to each cell in the column
        df[column_name + '_color'] = df[column_name].apply(lambda x: percent_change_to_color(x, min_val, max_val))
    else:
        # If not found in change_ranges, use a default color
        df[column_name + '_color'] = '#fff'

    return df


def run_loop():
    while True:
        start_date_str = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date_str = datetime.today().strftime('%Y-%m-%d')

        ipo_calendar_df = get_ipo_calendar(start_date_str, end_date_str)
        if ipo_calendar_df is None:
            print("No data returned from IPO calendar API - exiting")
            exit(0)

        # Filter by exchange
        mask = (ipo_calendar_df["exchange"] == 'Nasdaq')
        ipo_calendar_df = ipo_calendar_df[mask]

        all_changes_df = pd.DataFrame()
        for index, row in ipo_calendar_df.iterrows():
            symbol = row['symbol']
            company = row['company']
            date = row['date']
            print(f"Processing {symbol} - {company}...")
            prices_df = get_prices(symbol, "1min", start_date_str, end_date_str)
            if prices_df is None or len(prices_df) < 10:
                print(f"Not enough price data for {symbol}")
                continue

            if prices_df['Close'].min() < 1.0:
                print(f"Not trading penny stocks: {symbol}")
                continue

            change_row_df = calculate_performance(prices_df)
            # Add 'Symbol' and 'Company' to the row
            change_row_df.insert(0, 'Symbol', symbol)
            change_row_df.insert(1, 'Company', company)
            change_row_df.insert(2, 'Date', date)
            all_changes_df = pd.concat([all_changes_df, change_row_df], axis=0, ignore_index=True)

        # Calculate min/max for each column
        all_changes_df.fillna(0, inplace=True)
        change_ranges = get_min_max_ranges(all_changes_df)

        # Add color columns to the DataFrame
        all_changes_df = add_color_to_df(all_changes_df, change_ranges)

        # Define data columns (excluding color columns and special columns)
        data_columns = [col for col in all_changes_df.columns if not col.endswith('_color') and col not in ['Symbol', 'Company', 'Date']]

        # Generate HTML report
        generate_html_report(all_changes_df, data_columns)

        time.sleep(60)


if __name__ == "__main__":
    # Create output directories
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    # Start main loop
    run_loop()
