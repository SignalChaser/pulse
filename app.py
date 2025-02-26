import streamlit as st
import altair as alt
import numpy as np
import yfinance as yf
from datetime import datetime
import pandas as pd
from streamlit_extras.buy_me_a_coffee import button
import streamlit.components.v1 as components

st.set_page_config(page_title="Pulse", layout="wide")

if 'show_animation' not in st.session_state:
    st.session_state.show_animation = True


def load_particles_config():
    with open('particles_config.html', 'r') as file:
        return file.read()

# Where you use the particles configuration:
particles_js = load_particles_config()

# Load CSS file
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Call function to load CSS file
local_css('style.css')

def example():
    button(username="ajwaldert", floating=True, width=221, bg_color= "#1d2cf3", font_color="#ffffff", coffee_color="#ffffff")



@st.cache_data(ttl=60)
def fetch_stock_tickers(instrument_type):
    try:
        # Read from CSV instead of Supabase
        df = pd.read_csv('all_stocks.csv')
        
        # Add instrument_type column based on ISIN prefixes
        def determine_instrument_type(isin):
            if pd.isna(isin):
                return 'UNKNOWN'
            # Add your instrument type logic here
            return 'STOCK'  # Default to STOCK for now
        
        df['instrument_type'] = df['isin'].apply(determine_instrument_type)
        
        # Convert to the format expected by the rest of the app
        tickers_db = df.to_dict('records')
        
        # Ensure uppercase for consistency
        for ticker in tickers_db:
            ticker['country'] = ticker['country'].upper()
            ticker['instrument_type'] = ticker['instrument_type'].upper()
        
        return tickers_db
    except Exception as e:
        st.error(f"Error fetching stock tickers: {e}")
        return []

def fetch_data_by_ticker_and_date_range(isin, start_date, end_date):
    try:
        print(f"\nDEBUG INFO:")
        print(f"ISIN received: {isin}")
        
        # Convert datetime to date strings in YYYY-MM-DD format
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        print(f"Start date: {start_date_str}")
        print(f"End date: {end_date_str}")
        
        # Try fetching data using ISIN directly
        ticker_data = yf.download(
            tickers=isin,
            start=start_date_str,
            end=end_date_str,
            progress=False,
            auto_adjust=True  # Use adjusted prices by default
        )
        
        if ticker_data.empty:
            print(f"No data found using ISIN directly, falling back to symbol lookup")
            # Fallback to symbol if ISIN fails
            stocks_df = pd.read_csv('all_stocks.csv')
            stock_info = stocks_df[stocks_df['isin'] == isin].iloc[0]
            symbol = stock_info['symbol'].strip()
            print(f"Trying symbol: {symbol}")
            
            ticker_data = yf.download(
                tickers=symbol,
                start=start_date_str,
                end=end_date_str,
                progress=False,
                auto_adjust=True
            )
        
        if ticker_data.empty:
            st.error(f"No data found for symbol {symbol} (ISIN: {isin})")
            return pd.DataFrame()
            
        # Process the data
        ticker_data.reset_index(inplace=True)
        ticker_data.rename(columns={'Date': 'date'}, inplace=True)
        
        # Calculate daily returns using Close instead of Adj Close
        ticker_data['daily_return'] = ticker_data['Close'].pct_change()
        
        # Create the month_day column
        ticker_data['month_day'] = pd.to_datetime(ticker_data['date']).dt.strftime('%m-%d')
        
        # Drop any NaN values
        ticker_data.dropna(inplace=True)

        return ticker_data

    except Exception as e:
        st.error(f"Error processing data for {isin}: {str(e)}")
        print(f"Full error: {str(e)}")
        return pd.DataFrame()


def main():

    with st.container():

        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    instrument_type = col1.selectbox("Instrument Type", ("STOCK", "ETF", "CURRENCY", "CRYPTO"), help="Select the instrument type." , key="analyzer instrument_type")

    country = col2.selectbox("Country",
                             ("UNITED STATES", "GERMANY", "UNITED KINGDOM", "INDIA", "AUSTRALIA", "SWITZERLAND",
                              "FRANCE", "NETHERLANDS", "CHINA", "BRAZIL", "JAPAN", "INDONESIA", "SOUTH KOREA"),
                             help="Select the country.", key="analyzer country")


    ticker_input = fetch_stock_tickers(instrument_type)


    # Filter tickers based on the selected country and instrument type
    filtered_tickers = [{'combined': ticker['combined'], 'symbol': ticker['symbol']} for ticker in ticker_input if
                        ticker['country'].upper() == country and ticker[
                            'instrument_type'].upper() == instrument_type]

    # Create a list from ticker_input
    ticker_input_list = [i['combined'] for i in filtered_tickers]

    # Selectbox for tickers based on the selected country
    ticker = col3.selectbox("Name | ISIN", ticker_input_list, help="Select your instrument of choice either by name or ISIN", key = "analyzer ticker")


    st.session_state.ticker = ticker


    start_date = col4.date_input("Data From:", value=datetime(1900, 1, 1), min_value=datetime(1900, 1, 1),
                                 max_value=datetime.now(), help="Select the start date for the data to be fetched.", key="analyzer start_date")

    end_date = col5.date_input("Data To:", value=datetime.now(), min_value=datetime(1900, 1, 1),
                               max_value=datetime.now(), help="Select the end date for the data to be fetched", key="analyser end_date")

    exclude_years = col6.multiselect("Exclude Years", list(range(2024, 1899, -1)), help="Select the years to exclude from the analysis.", key = "analyzer exclude_years")
    fetch_button = col7.button("Fetch Data", type="primary", key = "analyzer fetch_button")

    st.divider()

    def run_animation():
        # Handle the logic for showing or hiding the animation
        if st.session_state.show_animation:

            st.header("Welcome to Pulse Analytics")
            st.write("**Pulse** is an interactive dashboard designed to help you analyze seasonal and trend-based trade patterns across various asset classes. Get started by selecting your desired instrument and pressing the 'Fetch Data' button. Pulse is free to use, but to support ongoing development, please consider donating via the **'Buy me a coffee'** button.")
            #how to pictures? guide, buy coffe button
            components.html(particles_js, height=500, scrolling=False)

    if fetch_button:
        st.session_state.show_animation = False


    run_animation()

    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())


    # Need to initiate session state variables for each element we need
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame()

    if 'avg_returns' not in st.session_state:
        st.session_state.avg_returns = None

    if fetch_button:
        if st.session_state.ticker:
            isin = st.session_state.ticker.split('|')[-1].strip()
            company_name = st.session_state.ticker.split('|')[0].strip()

            st.session_state.isin = isin
            st.session_state.company_name = company_name

            # Initialize DataFrame in session state
            if 'df' not in st.session_state:
                st.session_state.df = pd.DataFrame()

            # Fetching data
            df = fetch_data_by_ticker_and_date_range(isin, start_date, end_date)
            
            if not df.empty:
                st.session_state.df = df
                
                # Store earliest and latest dates
                st.session_state.earliest_date = df['date'].min().strftime('%Y-%m-%d')
                st.session_state.latest_date = df['date'].max().strftime('%Y-%m-%d')
                
                # Filter out excluded years
                if exclude_years:
                    st.session_state.df = st.session_state.df[~pd.to_datetime(st.session_state.df['date']).dt.year.isin(exclude_years)]

                # Calculate average returns
                st.session_state.avg_returns = st.session_state.df.groupby('month_day')['daily_return'].mean().reset_index()
                
                # Calculate growth (cumulative returns)
                st.session_state.growth = (1 + st.session_state.avg_returns['daily_return']).cumprod() * 100
                
                # Calculate min and max growth for chart scaling
                st.session_state.min_growth = st.session_state.growth.min()
                st.session_state.max_growth = st.session_state.growth.max()
                
            else:
                st.error("No data available for the selected ticker")
        else:
            st.error("Please select a ticker")

    with st.container():
        col8, col9  = st.columns([7, 3])


    st.divider()
    with st.container():
        col_4, col_5, col_6, col_7, col_8, col_9, col_10 = st.columns(7)
    with st.container():
        col100, _, col101 = st.columns([96, 5, 64])

    if not st.session_state.df.empty:
        st.session_state.df['date'] = pd.to_datetime(st.session_state.df['date']).dt.strftime('%Y-%m-%d')

        st.session_state.brush = alt.selection_interval(value={'x': [20, 40]}, name="Interval", empty=False, clear=False,  encodings=['x'], mark=alt.BrushConfig(fill='#1d2cf3', fillOpacity=0.3))

        chart = alt.Chart(
            pd.DataFrame({'Day_of_Year': st.session_state.avg_returns.month_day, 'Growth': st.session_state.growth.round(2)})
        ).mark_line(
            color='white',
            strokeWidth=2,
            interpolate='linear'
        ).encode(
            x=alt.X('Day_of_Year:T', title='Day of Year', axis=alt.Axis(format='%b %d', labelAngle=-90, tickCount=100)),
            y=alt.Y('Growth:Q', title='Growth of $100', scale=alt.Scale(domain=[ st.session_state.min_growth,  st.session_state.max_growth])),
            tooltip=[alt.Tooltip('Day_of_Year:T', format='%b %d'), 'Growth']
        ).properties(
            width=1200,
            height=640,
            background='rgba(0, 0, 0, 0)',
            title={
                "text": "Seasonal Pattern Chart",
                "subtitle": "Depicting the growth of 100$ invested in the instrument averaged accross the years by each day of the year",
                "color": "white",
                "subtitleColor": "white",
                "subtitleFontSize": 16
            }).add_params(st.session_state.brush)

        # Adjusting font sizes
        chart = chart.configure_axis(
            titleFontSize=14,  # Axis title font size
            labelFontSize=12  # Tick label font size
        ).configure_legend(
            disable=True  # This line disables the legend
        ).configure_title(
            fontSize=20  # Chart title font size
        )

        data = col100.altair_chart(chart, use_container_width=True, on_select='rerun', key="my_chart")

        selection_data = data  # Get the JSON response from Altair chart selection
        #st.write(selection_data)

        if "Day_of_Year" in selection_data["selection"]["Interval"]:
            # Access the Unix timestamps
            unix_timestamps = selection_data["selection"]["Interval"]["Day_of_Year"]

            # Convert Unix timestamps to human-readable dates
            readable_dates = [datetime.fromtimestamp(ts / 1000).strftime('%m-%d') for ts in unix_timestamps]

            # Convert selected dates to datetime with the same reference year
            start_filter = datetime.strptime('2000-' + readable_dates[0], '%Y-%m-%d')
            end_filter = datetime.strptime('2000-' + readable_dates[1], '%Y-%m-%d')
            # Assuming readable_dates contains the start and end dates
            start_date_str = readable_dates[0]
            end_date_str = readable_dates[1]

            # Define the colors for the dates
            start_date_color = "#ffffff"  # Red color for start date
            end_date_color = "#ffffff"  # Green color for end date

            # Create the HTML string with inline CSS to color the dates
            html_string = f"""
            <h1 style='text-align: left; color: white;'>
                {st.session_state.company_name} - {st.session_state.isin} |
                Pattern from:
                <span style='color: {start_date_color}; font-style: italic;'>{start_date_str}</span> to
                <span style='color: {end_date_color}; font-style: italic;'>{end_date_str}</span>
            </h1>
            """

            # Display the HTML string using Streamlit
            col8.markdown(html_string, unsafe_allow_html=True)
        else:
            col8.markdown(
                f"<h1 style='text-align: left; color: white;'>{st.session_state.company_name} - {st.session_state.isin}</h1>",
                unsafe_allow_html=True)
            start_filter = '2000-01-01'
            end_filter = '2000-12-31'

        col8.write(f"Data used for analysis: {st.session_state.earliest_date} to {st.session_state.latest_date}")

        pattern_return = st.session_state.df.copy()
        # Ensure 'month_day' is a string
        pattern_return['month_day'] = pattern_return['month_day'].astype(str)

        pattern_return['month_day'] = pd.to_datetime('2000-' + pattern_return['month_day'], format='%Y-%m-%d')

        pattern_return = pattern_return[
            (pattern_return['month_day'] >= start_filter) & (pattern_return['month_day'] <= end_filter)]

        pattern_return['date'] = pd.to_datetime(pattern_return['date'])

        pattern_return['year'] = pattern_return['date'].dt.year

        pattern_return_grouped = pattern_return.groupby('year')['daily_return'].apply(lambda x: (1 + x).prod() - 1).reset_index()

        # Rename the column to 'Return'
        pattern_return_grouped = pattern_return_grouped.rename(columns={'daily_return': 'Return'})

        # Round the returns to two decimal places
        pattern_return_grouped['Return'] = pattern_return_grouped['Return'].round(2)

        #Adding Metrics
        col_4.metric("Maximum Pattern Growth", f"{pattern_return_grouped['Return'].max() * 100:.2f}%")
        col_5.metric("Maximum Pattern Drawdown", f"{pattern_return_grouped['Return'].min() * 100:.2f}%")
        col_6.metric("Average Pattern Return", f"{pattern_return_grouped['Return'].mean() * 100:.2f}%")
        col_7.metric("Cumulative Pattern Return", f"{(pattern_return['daily_return']).sum():.2%}")
        col_8.metric("Positive Returns", f"{len(pattern_return_grouped[pattern_return_grouped['Return'] > 0]):.0f}")
        col_9.metric("Negative Returns", f"{len(pattern_return_grouped[pattern_return_grouped['Return'] < 0]):.0f}")
        col_10.metric("Positive / Negative Ratio %",f"{(len(pattern_return_grouped[pattern_return_grouped['Return'] > 0]) / len(pattern_return_grouped) * 100):.2f}%")

        # st.dataframe(yearly_returns)

        # Create the bar chart
        bar_chart = alt.Chart(pattern_return_grouped).mark_bar(color='#E5E5E5').encode(
            x=alt.X('year:O', title='Year'),
            y=alt.Y('Return:Q', title='Yearly Return', axis=alt.Axis(format='%')),
            tooltip=[alt.Tooltip('year:O', title='Year'),
                     alt.Tooltip('Return:Q', title='Return', format='.2%')]
        ).properties(
            width=700,
            height=300,
            title='Yearly Pattern Return'
        )

        # Highlight the top 3 years
        highlighted_bars = alt.Chart(pattern_return_grouped.nlargest(3, 'Return')).mark_bar(color='#1d2cf3',
                                                                                    opacity=1).encode(
            x=alt.X('year:O', title='Year'),
            y=alt.Y('Return:Q', title='Yearly Return', axis=alt.Axis(format='%')),
            tooltip=[alt.Tooltip('year:O', title='Year'),
                     alt.Tooltip('Return:Q', title='Return', format='.2%')]
        )

        # Combine the charts
        combined_chart = alt.layer(bar_chart, highlighted_bars).properties(
            width=700,
            height=300,
            background='rgba(0, 0, 0, 0)',  # Set background to transparent
            title='Pattern Return by Year'
        ).configure_view(
            stroke=None  # Ensure no border stroke is applied
        ).configure_axis(
            titleFontSize=14,  # Axis title font size
            labelFontSize=12  # Tick label font size
        ).configure_legend(
            disable=True  # This line disables the legend
        ).configure_title(
            fontSize=20  # Chart title font size
        )

        st.session_state.combined_chart = combined_chart

        # Calculate cumulative return based on yearly returns
        cumulative_return_yearly = np.cumsum(pattern_return_grouped['Return'])

        # Create DataFrame with cumulative return based on yearly returns
        cumulative_data_yearly = pd.DataFrame(
            {'Year': pattern_return_grouped['year'], 'Cumulative_Return': cumulative_return_yearly})

        # Update area_chart to display cumulative return based on yearly returns
        area_chart_yearly = alt.Chart(cumulative_data_yearly).mark_area(
            line={'color': 'lightblue'},
            color=alt.Gradient(
                gradient='linear',
                stops=[
                    alt.GradientStop(color='white', offset=0),
                    alt.GradientStop(color='#1d2cf3', offset=1)
                ],
                x1=1,
                x2=1,
                y1=1,
                y2=0
            )
        ).encode(
            x=alt.X('Year:O', title='Year'),
            y=alt.Y('Cumulative_Return:Q', title='Cumulative Return', axis=alt.Axis(format='%')),
            tooltip=[alt.Tooltip('Year:O', title='Year'),
                     alt.Tooltip('Cumulative_Return:Q', title='Cumulative Return', format='.2%')]
            # Format as percentage
        ).properties(
            width=700,
            height=300,
            background='rgba(0, 0, 0, 0)',
            title='Cumulative Pattern Return'
        ).configure_axis(
            titleFontSize=14,  # Axis title font size
            labelFontSize=12  # Tick label font size
        ).configure_legend(
            disable=True  # This line disables the legend
        ).configure_title(
            fontSize=20  # Chart title font size
        )


        col101.altair_chart( st.session_state.combined_chart, use_container_width=True)
        col101.altair_chart(area_chart_yearly, use_container_width=True)
        st.markdown('<hr class="hr-opacity">', unsafe_allow_html=True)
    st.text("")
    st.text("")

    with st.container():
        col12, col14 = st.columns([2, 12])

    col12.markdown("""
            <div style='width: 80%; text-align: center;'>
                        <img src='https://static.wixstatic.com/media/c44eec_37ef0553f0ac4b72af61d42545d98504~mv2.png/v1/fill/w_162,h_144,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/pulse%20(3).png' alt='Logo' width='100' height='100'>
                    </div>
                    """, unsafe_allow_html=True)

    col14.markdown(
        "Legal Disclaimer: Past performance and historical seasonal trends do not guarantee future outcomes, especially regarding market trends. I do not endorse any specific financial instruments, securities groups, industry sectors, analysis periods, or strategies, nor do I offer consultancy, brokerage, or asset management services. I explicitly disclaim any explicit or implied trading recommendations, including any assurances of profit or protection against losses. While every effort is made to interpret terms broadly in case of ambiguity, users bear sole responsibility for their trading strategies and outcomes. Indicators, strategies, and functions provided may contain errors leading to unexpected results or losses. I do not warrant the accuracy, completeness, or adequacy of the information provided. Users must comply with applicable capital market regulations. All content and images are copyright protected, requiring prior written consent for use beyond copyright law. Futures and forex trading carry significant risks and may result in the loss of invested capital. Only risk capital should be used, and trading should only be considered by those with sufficient risk tolerance. Past performance does not guarantee future results, and testimonials do not assure similar outcomes for other clients.")


    example()

if __name__ == "__main__":
    main()
