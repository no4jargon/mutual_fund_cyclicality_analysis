# Indian Mutual Fund Dataset 📊

<p align="center">
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-white.svg?style=for-the-badge" alt="License: MIT">
  </a>
  <a href="https://www.kaggle.com/datasets/tharunreddy2911/mutual-fund-data">
    <img src="https://img.shields.io/badge/Kaggle-Dataset-blue.svg?style=for-the-badge&logo=kaggle" alt="Kaggle Dataset">
  </a>
  <a href="#update-frequency">
    <img src="https://img.shields.io/badge/Updated-Daily-brightgreen.svg?style=for-the-badge" alt="Update Frequency">
  </a>
  <a href="https://flatgithub.com/InertExpert2911/Mutual_Fund_Data/">
    <img src="https://img.shields.io/badge/Explore%20CSV-Flat%20Data%20Viewer-orange.svg?style=for-the-badge" alt="View CSV">
  </a>
  <a href="https://github.com/InertExpert2911/Mutual_Fund_Data/commits/main/">
    <img src="https://img.shields.io/github/last-commit/InertExpert2911/Mutual_Fund_Data.svg?style=for-the-badge&" alt="GitHub last commit">
  </a>
</p>

----

## Table of Contents

* [📜 Description](#-description)
* [💻 Explore the Data Online](#-explore-the-data-online)
* [💾 How to Use](#-how-to-use)
* [🔍 What's Inside: `mutual_fund_data.csv`](#-whats-inside-mutual_fund_datacsv)
* [⏱️ Update Frequency](#️-update-frequency)
* [💡 Potential Uses](#-potential-uses)
* [🤝 Contributing](#-contributing)
* [🙏 Acknowledgements](#-acknowledgements)
* [📄 License](#-license)

---

## 📜 Description

This dataset offers an extensive look at over **16,000+** Indian mutual fund schemes, covering a wide array including old(closed), currently active, and new/recently launched funds. Featuring the latest **Net Asset Value (NAV)** and **Assets Under Management (AUM)** data, it's designed for easy analysis and comparison!

---

## 💻 Explore the Data Online

Instantly explore, filter, and sort the dataset directly in your browser without downloading using these tools:

<a href="https://www.kaggle.com/datasets/tharunreddy2911/mutual-fund-data">
  <img src="https://img.shields.io/badge/Explore%20Dataset%20on-Kaggle-blue.svg?style=flat-square&logo=kaggle" alt="Explore on Kaggle">
</a>
<a href="https://flatgithub.com/InertExpert2911/Mutual_Fund_Data/">
  <img src="https://img.shields.io/badge/Explore%20CSV-Flat%20Data%20Viewer-orange.svg?style=flat-square" alt="Explore CSV with Flat Data Viewer">
</a>

---

## 💾 How to Use

1.  **Download:** Clone the repository or download the `mutual_fund_data.csv` file directly.
2.  **Load:** Use your favorite data analysis tool (like Python with Pandas, R, Excel, etc.) to load the CSV file.

    ```python
    import pandas as pd
    df = pd.read_csv('mutual_fund_data.csv')
    print(df.head())
    ```
3.  **Analyze:** Explore the data based on your requirements!

---

## 🔍 What's Inside: `mutual_fund_data.csv`

**🆔 Fund Identification & Details**

### 🆔 Fund Identification & Details

* **`Scheme_Code`**: Unique code assigned to a mutual fund scheme.
* **`AMC`**: The **Asset Management Company** that manages the mutual fund.
* **`Scheme_Name`**: Name of the mutual fund scheme.
* **`Scheme_NAV_Name`**: Detailed name of the scheme often indicating the specific plan(*e.g., Growth, IDCW/Dividend*).
* **`ISIN_Div_Payout/Growth`**: Unique ISIN(*International Securities Identification Number*) for dividend payout or growth option of the scheme.
* **`ISIN_Div_Reinvestment`**:  Unique ISIN for dividend reinvestment option of the scheme.
* **`ISIN_Div_Payout/Growth/Div_Reinvestment`**: Comprehensive ISINs covering dividend payout, growth, or dividend reinvestment options, often a combination or primary identifier if others are not specific.
* **`Lauch_Date`**: Date when the mutual fund scheme was launched
* **`Closure_Date`**: Date when the mutual fund scheme was closed (*if applicable*)

### 🏷️ Classification

* **`Scheme_Type`**: How the fund is structured (*e.g., Open Ended, Close Ended*).
* **`Scheme_Category`**: Classification of the scheme based on its investment strategy(*e.g., Equity Large Cap, Debt Liquid Fund*).

### 💰 Financials & Investment Info

* **`NAV`**: **Net Asset Value** per unit of the fund scheme. 
* **`Latest_NAV_Date`**: Date on which the **latest NAV** was declared.
* **`Scheme_Min_Amt`**: Minimum investment amount required to invest in the scheme.
* **`AAUM_Quarter`**: The quarter for which the average AUM is reported (*e.g., January - March 2025*)
* **`Average_AUM_Cr`**: Average assets under management in crores for the scheme.

---

## ⏱️ Update Frequency

* **Updated Daily**: The dataset is automatically refreshed every day via a scheduled Kaggle Notebook. It typically reflects the NAV from the previous trading day.

---

## 💡 Potential Uses

* ✅ Compare different mutual funds and AMCs.
* ✅ Analyze trends across fund categories and types.
* ✅ Get a quick overview of the Indian mutual fund market structure.
* ✅ Build dashboards or visualizations of the Indian MF landscape.
* ✅ Track NAV movements for specific schemes.

---

## 🤝 Contributing

While the data is updated automatically, contributions to improve the README, add analysis examples (e.g., in a separate notebook), or suggest enhancements are welcome! Please feel free to open an issue or submit a pull request.

---

## 🙏 Acknowledgements

* Data is sourced from the **Association of Mutual Funds in India (AMFI)**.
* This dataset is compiled for educational and analytical purposes. 
* **Always consult a financial advisor before making investment decisions.**

---

## 📄 License

This dataset is shared under the [MIT License](https://opensource.org/licenses/MIT).
