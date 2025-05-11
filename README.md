# Indian Mutual Fund Dataset 📊

<p align="center">
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-white.svg?style=for-the-badge" alt="License: MIT">
  </a>
  <a href="https://www.kaggle.com/datasets/tharunreddy2911/mutual-fund-data">
    <img src="https://img.shields.io/badge/Kaggle-Scheme Dataset-blue.svg?style=for-the-badge&logo=kaggle" alt="Kaggle Dataset">
  </a>
  <a href="https://www.kaggle.com/datasets/tharunreddy2911/mutual-fund-historic-nav-data">
    <img src="https://img.shields.io/badge/Kaggle-Historic NAV Dataset-blue.svg?style=for-the-badge&logo=kaggle" alt="Kaggle Dataset">
  </a>
  <a href="#update-frequency">
    <img src="https://img.shields.io/badge/Updated-Daily-brightgreen.svg?style=for-the-badge" alt="Update Frequency">
  </a>
  <a href="https://flatgithub.com/InertExpert2911/Mutual_Fund_Data?filename=mutual_fund_data.csv">
    <img src="https://img.shields.io/badge/Explore%20Scheme%20Data%20(CSV)-Flat%20Data%20Viewer-orange.svg?style=for-the-badge" alt="View Scheme Data CSV">
  </a>
  <a href="https://github.com/InertExpert2911/Mutual_Fund_Data/commits/main/">
    <img src="https://img.shields.io/github/last-commit/InertExpert2911/Mutual_Fund_Data.svg?style=for-the-badge&" alt="GitHub last commit">
  </a>
</p>

This repository hosts a **daily-updated dataset** focusing on Indian Mutual Fund schemes. It is comprised of two main data files:
1.  `mutual_fund_data.csv`: Contains the latest snapshot of scheme details, including Net Asset Value (NAV), Asset Management Company (AMC), Assets Under Management (AUM), scheme categories, and more.
2.  `mutual_fund_nav_history.parquet`: Provides extensive historical Net Asset Value (NAV) data for time-series analysis.

The data is automatically fetched and processed daily via a Kaggle Notebook.

## Table of Contents

* [📜 Description](#-description)
* [💻 Explore the Data Online](#-explore-the-data-online)
* [💾 How to Use](#-how-to-use)
* [🔍 What's Inside](#-whats-inside)
    * [Current Scheme Details: `mutual_fund_data.csv`](#--current-scheme-details-mutual_fund_datacsv)
    * [Historical NAV Data: `mutual_fund_nav_history.parquet`](#--historical-nav-data-mutual_fund_nav_historyparquet)
* [📈 Calculable Metrics & Analyses (from Historical NAV Data)](#-calculable-metrics--analyses-from-historical-nav-data)
* [⏱️ Update Frequency](#️-update-frequency)
* [💡 Potential Uses](#-potential-uses)
* [🤝 Contributing](#-contributing)
* [🙏 Acknowledgements](#-acknowledgements)
* [📄 License](#-license)

## 📜 Description

This dataset provides a comprehensive view of the Indian mutual fund market.
* The `mutual_fund_data.csv` file offers a snapshot of over **9,000+** mutual fund schemes, featuring the latest Net Asset Value (NAV) & Assets Under Management (AUM) data, refreshed daily.
* The `mutual_fund_nav_history.parquet` file contains over **20 Million+ historical NAV records** for in-depth performance analysis, with **6,000+ new NAV records added daily.**

Together, these files serve as a valuable resource for financial analysis, comparison, backtesting, and tracking of the Indian mutual fund landscape.

## 💻 Explore the Data Online

Instantly explore, filter, and sort the `mutual_fund_data.csv` (scheme details) directly in your browser:


<a href="https://www.kaggle.com/datasets/tharunreddy2911/mutual-fund-data">
    <img src="https://img.shields.io/badge/Kaggle-Scheme Dataset-blue.svg?style=flat-square&logo=kaggle" alt="Kaggle Dataset">
  </a>
  <a href="https://www.kaggle.com/datasets/tharunreddy2911/mutual-fund-historic-nav-data">
    <img src="https://img.shields.io/badge/Kaggle-Historic NAV Dataset-blue.svg?style=flat-square&logo=kaggle" alt="Kaggle Dataset">
  </a>
<a href="https://flatgithub.com/InertExpert2911/Mutual_Fund_Data?filename=mutual_fund_data.csv">
  <img src="https://img.shields.io/badge/Explore%20Scheme%20Data%20(CSV)-Flat%20Data%20Viewer-orange.svg?style=flat-square" alt="Explore CSV with Flat Data Viewer">
</a>

*(Note: The Parquet file is best explored after downloading due to its size and format.)*

## 💾 How to Use

1.  **Download:** Clone the repository or download the desired files (`mutual_fund_data.csv`, `mutual_fund_nav_history.parquet`) directly.
2.  **Load:** Use your favorite data analysis tool.

    * **For `mutual_fund_data.csv` (Scheme Details):**
        ```python
        import pandas as pd
        df_schemes = pd.read_csv('mutual_fund_data.csv')
        print("Scheme Details Data:")
        print(df_schemes.head())
        ```
    * **For `mutual_fund_nav_history.parquet` (Historical NAVs):**
        You'll likely need `pandas` and potentially `pyarrow` or `fastparquet` installed.
        ```python
        import pandas as pd
        # Ensure you have pyarrow or fastparquet installed:
        # pip install pandas pyarrow
        # or
        # pip install pandas fastparquet
        df_nav_history = pd.read_parquet('mutual_fund_nav_history.parquet')
        print("\nHistorical NAV Data:")
        print(df_nav_history.head())
        ```
3.  **Analyze:** Explore the data based on your requirements!

## 🔍 What's Inside

### 📋 Current Scheme Details: `mutual_fund_data.csv`

This file provides a daily snapshot of various details for each mutual fund scheme.

* **`Scheme_Code`**: Unique code assigned to a mutual fund scheme.
* **`AMC`**: The **Asset Management Company** that manages the mutual fund.
* **`Scheme_Name`**: Name of the mutual fund scheme.
* **`Scheme_NAV_Name`**: Detailed name of the scheme often indicating the specific plan (*e.g., Growth, IDCW/Dividend*).
* **`ISIN_Div_Payout/Growth`**: Unique ISIN (*International Securities Identification Number*) for dividend payout or growth option of the scheme.
* **`ISIN_Div_Reinvestment`**: Unique ISIN for dividend reinvestment option of the scheme.
* **`ISIN_Div_Payout/Growth/Div_Reinvestment`**: Comprehensive ISINs covering dividend payout, growth, or dividend reinvestment options.
* **`Launch_Date`**: Date when the mutual fund scheme was launched.
* **`Closure_Date`**: Date when the mutual fund scheme was closed (*if applicable*).
* **`Scheme_Type`**: How the fund is structured (*e.g., Open Ended, Close Ended*).
* **`Scheme_Category`**: Classification of the scheme based on its investment strategy (*e.g., Equity Large Cap, Debt Liquid Fund*).
* **`NAV`**: **Latest Net Asset Value** per unit of the fund scheme.
* **`Latest_NAV_Date`**: Date on which the **latest NAV** was declared.
* **`Scheme_Min_Amt`**: Minimum investment amount required to invest in the scheme.
* **`AAUM_Quarter`**: The quarter for which the average AUM is reported (*e.g., January - March 2025*).
* **`Average_AUM_Cr`**: Average assets under management in crores for the scheme.

### ⏳ Historical NAV Data: `mutual_fund_nav_history.parquet`

This file contains the daily time-series of Net Asset Values, crucial for performance analysis and backtesting. It includes:

* **`Scheme_Code`**: 🔑 Unique code assigned to a mutual fund scheme. (Links to `mutual_fund_data.csv`)
* **`Date`**: 📅 The specific date for which the NAV is reported (e.g., `YYYY-MM-DD`).
* **`NAV`**: 💰 The Net Asset Value per unit of the fund scheme on the given `Date`.

This file is designed for efficient storage and quick loading of large historical datasets.

## 📈 Calculable Metrics & Analyses (from `mutual_fund_nav_history.parquet`)

The historical NAV data empowers you to quickly derive powerful insights like:

* **Performance & Returns 🚀:**
    * Absolute & Annualized (CAGR) Returns
    * Rolling & Point-to-Point Returns
    * Daily/Log Returns
* **Risk & Volatility 📉:**
    * Standard Deviation
    * Sharpe & Sortino Ratios (needs risk-free rate)
    * Max Drawdown
    * Beta & Alpha (needs benchmark data)
* **Trends & Momentum 📊:**
    * Moving Averages (SMA, EMA)
    * Rate of Change (ROC)
* **Comparisons & Market View 🧐 (when combined with scheme data):**
    * Fund Performance Rankings
    * Correlations Between Funds
* **Basic Stats 🔢:**
    * Highest/Lowest NAV over periods
    * Average/Median NAV over periods

## ⏱️ Update Frequency

* **Daily Updates**: Both `mutual_fund_data.csv` (scheme details) and `mutual_fund_nav_history.parquet` (new daily NAVs) are automatically refreshed every day via a scheduled Kaggle Notebook.
* Data typically reflects the NAV from the **previous trading day**.
* The historical NAV file (`mutual_fund_nav_history.parquet`) grows daily with new NAV records for all tracked schemes.

## 💡 Potential Uses

* ✅ **Scheme Discovery & Comparison:** Use `mutual_fund_data.csv` to filter and compare funds based on AMC, category, AUM, etc.
* ✅ **Performance Backtesting:** Leverage `mutual_fund_nav_history.parquet` to test investment strategies over historical periods.
* ✅ **Trend Analysis:** Analyze NAV movements and calculate momentum indicators from the historical data.
* ✅ **Risk Assessment:** Calculate volatility, Sharpe ratio, and other risk metrics for individual funds.
* ✅ **Market Overview:** Get a quick snapshot of the Indian mutual fund market structure using the scheme details.
* ✅ **Dashboard Building:** Create visualizations of the Indian MF landscape, tracking NAVs and performance.

## 🤝 Contributing

While the data is updated automatically, contributions to improve the README, add analysis examples (e.g., in a separate notebook), or suggest enhancements are welcome! Please feel free to open an issue or submit a pull request.

## 🙏 Acknowledgements

* Data is sourced from the **Association of Mutual Funds in India (AMFI)**.
* This dataset is compiled for educational and analytical purposes.
* **Always consult a financial advisor before making investment decisions.**

## 📄 License

This dataset is shared under the [MIT License](https://opensource.org/licenses/MIT).
