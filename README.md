# 🧭 VoyageAI — Intelligent Travel Companion & Itinerary Planner

VoyageAI is an interactive AI-powered travel assistant and trip planner built with **Python** and **Streamlit**. It leverages comprehensive tourism datasets across India to generate tailored 1-day exploration itineraries, calculate estimated sightseeing expenses, provide direct Google Maps navigation, and offer dynamic filtering options.

---

## 🌟 Key Features

* **Smart 1-Day Itinerary Engine:** Automatically organizes recommendations into Morning, Afternoon, and Evening slots based on visiting durations.
* **Trip Budget & Time Estimator:** Dynamically aggregates total entrance fees and sightseeing hours for the curated itinerary.
* **Travel Personas / Mood Presets:** One-click instant filters for *Budget Backpacker*, *Heritage & History*, *Nature & Scenic*, and *Family Friendly* travel styles.
* **Cascading Dynamic Filters:** Geographic Zone selection instantly filters available States and Territories, avoiding invalid query combinations.
* **Fuzzy NLP Query Matcher:** Built-in typo handling (`difflib`) and word-boundary regex parsing for seamless natural language search.
* **One-Click Navigation & Export:** Direct Google Maps query links for each spot and a downloadable `.txt` itinerary export.

---

## 🛠️ Tech Stack

* **Frontend & Deployment:** [Streamlit](https://streamlit.io/)
* **Data Processing & Analytics:** [Pandas](https://pandas.pydata.org/)
* **Dataset Management:** [kagglehub](https://github.com/Kaggle/kagglehub)
* **Language & String Processing:** Python (Regular Expressions `re`, `difflib`)

---

## 📊 Dataset Reference

This project utilizes the **India Travel Guide — Top Tourist Places** dataset available on Kaggle:
* **Dataset Source:** `saketk511/travel-dataset-guide-to-indias-must-see-places`
* **Coverage:** 325+ indexed destinations across 28 Indian States and Union Territories, including ratings, entrance fees, DSLR photography policies, and cultural significance.

---

## 🚀 Getting Started Locally

### 1. Prerequisites
Make sure you have **Python 3.9+** and **Git** installed on your system.

### 2. Clone the Repository
```bash
git clone [https://github.com/dasarideshna-pixel/travel-chatbot.git](https://github.com/dasarideshna-pixel/travel-chatbot.git)
cd travel-chatbot
