<h1 align="center">🏠 Property Report Generator</h1>

<p align="center">
  A modern real estate tool to lookup, edit, and generate beautifully formatted PDF reports for buyers and sellers.
</p>

<p align="center">
  <img alt="GitHub repo size" src="https://img.shields.io/github/repo-size/YOUR_USERNAME/property-report-app?style=flat-square">
  <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/YOUR_USERNAME/property-report-app?style=flat-square">
  <img alt="License" src="https://img.shields.io/github/license/YOUR_USERNAME/property-report-app?style=flat-square">
</p>

---

## ✨ Features

✅ Real-time property lookup
✅ Editable property data in a modal
✅ Auto-generated PDF reports for buyers & sellers
✅ Clean and responsive UI with TailwindCSS
✅ FastAPI-powered backend with REST endpoints

---

## 🖼️ Demo

<p align="center">
  <img src="images/screenshot1.png" width="700" alt="Property Search UI" />
  <br/>
  <em>🏘️ Property Search Modal</em>
</p>

<p align="center">
  <img src="images/screenshot2.png" width="700" alt="Editable Form UI" />
  <br/>
  <em>📝 Editable Property Data</em>
</p>

<p align="center">
  <img src="images/screenshot3.png" width="700" alt="Generated PDF Preview" />
  <br/>
  <em>📄 PDF Report Preview</em>
</p>

---

## 🚀 Tech Stack

* ⚙️ **Backend**: [FastAPI](https://fastapi.tiangolo.com/)
* 🌐 **Frontend**: HTML + JavaScript + [TailwindCSS](https://tailwindcss.com/)
* 📄 **PDF Reports**: Generated using Python libraries (e.g., ReportLab / WeasyPrint)

---

## 🏁 Getting Started

### 🔧 Prerequisites

* Python 3.8+
* Node.js (only if Tailwind is compiled manually)
* `pip install -r requirements.txt`

---

### ▶️ Run the App Locally

```bash
# Backend
cd backend
uvicorn main:app --reload
```

Then open your browser and navigate to:
`http://127.0.0.1:8000`

```bash
# Frontend
# Simply open frontend/index.html in your browser
```

---

## 🗂️ Project Structure

```
property-report-app/
├── backend/
│   ├── main.py
│   ├── utils/
│   └── reports/
│
├── frontend/
│   ├── index.html
│   └── assets/
│       ├── style.css
│       └── script.js
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 📦 Future Improvements

* 🔍 Search by location & filters
* ☁️ Deploy backend to Render / Railway
* 📬 Email reports to users
* 🌍 Map preview integration

---

## 📄 License

This project is licensed under the MIT License. See `LICENSE` for more information.

---

## 🙌 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## 📬 Contact

Built with ❤️ by [@EHTIISHAM](https://github.com/EHTIISHAM)
Feel free to reach out for collaboration or questions.
