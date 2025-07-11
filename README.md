# 💬 Chatbot Task-1 – AI-Powered Banking Chatbot with CSV Querying

This is a simple yet functional AI chatbot for banking purposes. It takes in user queries from a chat interface, uses natural language processing and Elasticsearch logic to search across a customer banking dataset (CSV), and presents structured responses back to the user via an interactive frontend.

---

## 🚀 Features

- 🌐 Web-based Chat Interface (HTML + CSS + JavaScript)
- 🧠 Backend with Flask to handle NLP and routing
- 📁 CSV-based banking data loaded and queried in real time
- 🔍 Full-text search for customer account and transaction queries
- 🧾 Displays tabular results (e.g., Account No, Outstanding Balance)
- 📊 Styled UI using CSS with light/dark themes
- ✅ Minimal and easy to set up – no complex databases required

---

## 🛠 Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Flask)
- **Data**: CSV files (`Data.csv`)
- **Logic**: Basic parsing, filtering & data retrieval using Pandas

---

## 📁 File Structure

```
├── app.py                   # Flask backend
├── Banking AI Chatbot.ipynb # Jupyter notebook version of logic
├── Data.csv                 # Source data (banking records)
├── index.html               # Chat UI frontend
├── style.css                # Stylesheet for the chat UI
```

---

## ⚙️ How to Run the Project

1. **Clone the Repository**
```bash
git clone https://github.com/voiceofarsalan/banking_bot.git
cd Chatbot-Task1
```

2. **Create a virtual environment & activate**
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install flask pandas
```

4. **Run the Flask App**
```bash
python app.py
```

5. **Open your browser and go to:**
```
http://localhost:5000
```

---

## 💡 Example Use Cases

- "Show me all customers with outstanding balance over 10,000."
- "Find accounts with number starting from 123."
- "How many transactions were made by account number XYZ?"

---

## 📌 Notes

- All logic is handled in-memory from the CSV file using Pandas.
- You can extend the logic to hook this into a proper NLP pipeline or database in the future.
- Make sure `Data.csv` is present in the root directory when running the Flask app.

---

## 📞 Contact

Made with ❤️ by [Arsalan Ahmed](https://www.linkedin.com/in/arsalan-ahmed-7223741b3/)

---

## 📄 License

This project is for educational/demo purposes. Feel free to fork and build upon it.
