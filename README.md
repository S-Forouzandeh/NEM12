# 🔌 NEM12 File Generator (Streamlit App)

This project provides a user-friendly web interface to convert raw CSV and Excel metering data into the standardized **NEM12 format**, used across the Australian National Electricity Market (NEM).

Developed for industry partners and utilities who require a streamlined and reliable way to generate NEM12-compliant metering data from raw interval readings.

---

## 🚀 Live App

👉 [Launch the NEM12 Generator App](https://s-forouzandeh-nem12-streamlit-app-gfddln.streamlit.app/)

No installation needed — just upload your files, and download the result in seconds.

---

## 📄 About the NEM12 Format

The NEM12 format is an industry-standard data structure used by energy retailers, distributors, and market participants to exchange interval metering data. It follows a row-based structure:

| Row Type | Description                                                |
|----------|------------------------------------------------------------|
| 100      | File header (file type, creation date, sender info)       |
| 200      | NMI and register/meter configuration                      |
| 300      | Interval readings (e.g., 15/30-min usage or generation)   |
| 400      | Read quality flags (used when readings vary in quality)   |
| 900      | End of the data block                                     |

This tool builds that structure automatically from input files.

---

## 📦 Features

- ✅ Upload **CSV** and **Excel** (`.xlsx`) files
- ✅ Automatic extraction and grouping of row types: 100, 200, 300, 400, 900
- ✅ Adds missing headers (e.g., `100` row) if required
- ✅ Outputs valid **NEM12 `.csv`** file
- ✅ Clean and simple interface via [Streamlit](https://streamlit.io)
- ✅ Supports multiple file uploads in a single run

---

## 🧪 How to Use

1. Visit the [web app](https://s-forouzandeh-nem12-streamlit-app-gfddln.streamlit.app/)
2. Upload one or more metering files in `.csv` or `.xlsx` format
3. Click **"Generate"**
4. Download the final NEM12 output as a `.csv` file

---

## 🧰 Local Development (Optional)

If you want to run this app locally:

### 🔧 Requirements

- Python 3.8+
- `pip install -r requirements.txt`

### 📂 Project Structure

