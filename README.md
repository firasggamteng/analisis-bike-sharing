# Proyek Analisis Data: Bike Sharing Dataset

Analisis data penyewaan sepeda Capital Bikeshare (Washington D.C., 2011–2012) dan dashboard interaktif Streamlit.

## Struktur
```
submission
├── dashboard
│   ├── main_data.csv      # data harian bersih
│   ├── hour_clean.csv     # data per jam bersih
│   └── dashboard.py
├── data
│   ├── day.csv
│   └── hour.csv
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment
```
python -m venv venv
venv\Scripts\activate        # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
```

## Menjalankan Dashboard
```
streamlit run dashboard/dashboard.py
```
