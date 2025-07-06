import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Stock Valuation Tool", layout="wide")

@st.cache_data
def load_tickers(region):
    if region == "India":
        df = pd.read_csv("nse_tickers.csv")
        return [t + ".NS" for t in df['Symbol'].tolist()]
    elif region == "USA":
        df = pd.read_csv("us_tickers.csv")
        return df['Symbol'].tolist()
    return []

def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        financials = stock.financials
        cashflow = stock.cashflow
        hist_prices = stock.history(period="5y")

        ev = info.get('enterpriseValue')
        shares = info.get('sharesOutstanding')
        price_now = info.get('currentPrice')

        ebit = financials.loc["Operating Income"].dropna()
        dep = cashflow.loc["Depreciation"].dropna()
        ebitda = ebit + dep
        years = list(ebit.index.year)
        ratios = []

        for year in years:
            try:
                ebitda_year = ebitda[str(year)]
                ratio = ev / ebitda_year if ebitda_year else None
                if ratio:
                    ratios.append(ratio)
            except:
                continue

        if len(ratios) >= 3:
            cagr = ((ratios[-1] / ratios[-3]) ** (1 / 2)) - 1
        else:
            cagr = 0.05

        latest_ebitda = ebitda[-1]
        projected_ebitda = latest_ebitda * (1 + cagr)
        projected_ev = ratios[-1] * projected_ebitda
        projected_price = projected_ev / shares if shares else None

        hist_3y = hist_prices.last("3y")
        entry = hist_3y["Low"].min()
        exit_ = hist_3y["High"].max()

        return {
            "Ticker": ticker,
            "Current Price": price_now,
            "Projected Price": round(projected_price, 2),
            "Entry Price": round(entry, 2),
            "Exit Price": round(exit_, 2),
            "CAGR EV/EBITDA (%)": round(cagr * 100, 2),
            "Signal": "Buy" if price_now < projected_price else "Hold/Sell"
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

st.title("📊 Stock Valuation & Projection Tool")
region = st.selectbox("Select Market Region", ["India", "USA"])
tickers = load_tickers(region)
selected = st.multiselect("Choose stocks to evaluate", tickers, default=tickers[:5])

if st.button("Run Valuation"):
    results = []
    for t in selected:
        with st.spinner(f"Evaluating {t}..."):
            result = fetch_stock_data(t)
            results.append(result)
    df = pd.DataFrame(results)
    st.dataframe(df)
    st.download_button("Download CSV", data=df.to_csv(index=False), file_name="valuation_results.csv")
