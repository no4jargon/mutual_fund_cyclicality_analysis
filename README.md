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

This repository hosts a **daily-updated dataset** focusing on Indian Mutual Fund schemes. It includes crucial details like Net Asset Value (NAV), Asset Management Company (AMC) info, scheme categories, and more. The data is automatically fetched and processed daily via a  Kaggle Notebook.

---

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

This dataset provides a comprehensive snapshot of over **9,000+** mutual fund schemes active in the Indian market. Featuring the latest Net Asset Value (NAV) data refreshed daily, it serves as a valuable resource for financial analysis, comparison, and tracking of the Indian mutual fund landscape.

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

* **`Scheme_Name`**: The primary name of the fund.
* **`AMC`**: The **Asset Management Company** managing the fund.
* **`Scheme_Code`**: A unique identifier for the scheme.
* **`Scheme_NAV_Name`**: A more detailed name, often indicating the specific plan (*e.g., Growth, IDCW/Dividend*).
* **`ISIN_Div_Payout/Growth` & `ISIN_Div_Reinvestment`**: Unique **ISIN** (*International Securities Identification Number*) codes for different plan options.
* **`Launch_Date`**: When the scheme started.
* **`Closure_Date`**: When the scheme closed.

**🏷️ Classification**

* **`Scheme_Type`**: How the fund is structured (*e.g., Open Ended, Close Ended*).
* **`Scheme_Category`**: The fund's investment strategy focus (*e.g., Equity Large Cap, Debt Liquid Fund*).

**💰 Financials & Investment Info**

* **`NAV`**: The **Net Asset Value** per unit of the scheme.
* **`Latest_NAV_Date`**: The date the `NAV` was reported.
* **`Scheme_Min_Amt`**: The minimum initial investment amount required.

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