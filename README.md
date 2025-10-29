Project Samarth

An intelligent Q&A system built over Indian government datasets
Powered by Google Gemini API + Streamlit + MySQL + Open Government Data (data.gov.in)
Designed for real-time agricultural and climate data analysis

🚀 Vision

Government portals like data.gov.in
 host thousands of open datasets from various ministries.
However, they exist in inconsistent formats — making cross-domain insights difficult.

Project Samarth bridges this gap by enabling natural language querying across agriculture and climate datasets,
empowering researchers, policymakers, and analysts to make data-driven decisions with confidence.

🧩 Features

✅ Intelligent Query Understanding — Uses Gemini LLM to interpret complex, multi-part natural language questions.
✅ Cross-Dataset Integration — Merges data from the Ministry of Agriculture and IMD seamlessly.
✅ Source Traceability — Every output cites the dataset(s) from which values are derived.
✅ Interactive Visualization — Automatically generates charts for rainfall, crop yield, and trends.
✅ Policy Insight Generation — Supports data-backed policy argument summaries.

⚙️ Tech Stack
Layer	Technology Used
Frontend	Streamlit
Backend	Python (Flask-like logic inside Streamlit)
ML/LLM Model	Google Gemini API
Database	MySQL / XAMPP (optional for caching)
Deployment	Streamlit Cloud / Google Colab
Data Source	data.gov.in
 APIs
🧠 Example Questions

The system can answer questions like:

Compare the average annual rainfall in Punjab and Haryana for the last 5 years and list the top 3 crops in each.

Identify the district in Maharashtra with the highest sugarcane production in the most recent year.

Analyze the production trend of wheat in Uttar Pradesh over the last decade and correlate with rainfall.

Recommend drought-resistant crops based on 10-year climatic trends.

Provide data-backed reasons for promoting Crop_A over Crop_B in region Y.
