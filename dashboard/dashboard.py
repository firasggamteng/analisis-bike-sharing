from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Dashboard Bike Sharing", layout="wide")

BASE = Path(__file__).parent
BLUE, ORANGE, RED, GREY, INK = "#1f6f8b", "#e07b39", "#c8553d", "#b8c7cf", "#2b3a42"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
SEASONS = ["Semi", "Panas", "Gugur", "Dingin"]
WEATHERS = ["Cerah", "Berkabut", "Hujan/Salju Ringan", "Hujan/Salju Lebat"]
METRICS = {"Total": "cnt", "Registered": "registered", "Casual": "casual"}
CONFIG = {"displayModeBar": False}

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1250px;}
    h1 {font-size: 1.9rem !important; margin-bottom: 0.2rem;}
    div[data-testid="stMetric"] {background: #f4f7f9; border-left: 4px solid #1f6f8b;
        padding: 0.7rem 1rem; border-radius: 4px;}
    div[data-testid="stMetricLabel"] {color: #55646c;}
    .insight {border-left: 4px solid #e07b39; padding: 0.4rem 0.9rem; margin-top: 0.6rem;
        background: #fbf6f2; border-radius: 3px; color: #2b3a42;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    day = pd.read_csv(BASE / "main_data.csv", parse_dates=["dteday"])
    hour = pd.read_csv(BASE / "hour_clean.csv", parse_dates=["dteday"])
    return day, hour


def style(fig, title, height=420, ytitle=None, xtitle=None, zero=True):
    fig.update_layout(
        title=dict(text=title, x=0, font=dict(size=15, color=INK)),
        template="simple_white",
        height=height,
        margin=dict(l=10, r=10, t=55, b=10),
        font=dict(color=INK),
        hoverlabel=dict(bgcolor="white"),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom"),
    )
    fig.update_yaxes(title=ytitle, gridcolor="#e8eef1", showline=False, rangemode="tozero" if zero else "normal")
    fig.update_xaxes(title=xtitle)
    return fig


def insight(text):
    st.markdown(f'<div class="insight">{text}</div>', unsafe_allow_html=True)


day_df, hour_df = load_data()

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Filter Data")
    years = st.multiselect("Tahun", [2011, 2012], default=[2011, 2012])
    seasons = st.multiselect("Musim", SEASONS, default=SEASONS)
    weathers = st.multiselect("Kondisi cuaca", WEATHERS[:3], default=WEATHERS[:3])
    metric_name = st.radio("Jenis pengguna", list(METRICS), horizontal=True)
    st.divider()
    st.caption("Sumber: Capital Bikeshare, Washington D.C., 2011-2012.")
    st.caption("Kolom cuaca 'Hujan/Salju Lebat' hanya 3 jam data sehingga tidak dijadikan pilihan.")

metric = METRICS[metric_name]

if not (years and seasons and weathers):
    st.warning("Pilih minimal satu tahun, satu musim, dan satu kondisi cuaca.")
    st.stop()

d = day_df[day_df["year"].isin(years) & day_df["season_label"].isin(seasons) & day_df["weather_label"].isin(weathers)]
h = hour_df[hour_df["year"].isin(years) & hour_df["season_label"].isin(seasons) & hour_df["weather_label"].isin(weathers)]

if d.empty or h.empty:
    st.warning("Tidak ada data untuk kombinasi filter ini. Ubah filter di sidebar.")
    st.stop()

# ---------------- Header & KPI ----------------
st.title("Dashboard Bike Sharing")
st.caption(f"Analisis penyewaan sepeda ({metric_name.lower()}) berdasarkan jam, cuaca, musim, dan pertumbuhan tahunan.")

k1, k2, k3, k4 = st.columns(4)
k1.metric(f"Total penyewaan ({metric_name})", f"{d[metric].sum():,}")
k2.metric("Rata-rata per hari", f"{d[metric].mean():,.0f}")
k3.metric("Porsi pengguna registered", f"{d['registered'].sum() / d['cnt'].sum():.1%}")
k4.metric("Jumlah hari dianalisis", f"{len(d):,}")

st.write("")
tab1, tab2, tab3 = st.tabs(["Pola per Jam", "Cuaca dan Musim", "Pertumbuhan dan Pengguna"])

# ---------------- Tab 1 ----------------
with tab1:
    st.subheader("Pertanyaan 1: Kapan jam puncak penyewaan?")
    view = st.radio("Tampilan", ["Hari kerja vs non-kerja", "Peta panas hari x jam"], horizontal=True)

    if view == "Hari kerja vs non-kerja":
        hourly = h.groupby(["day_type", "hr"])[metric].mean().unstack(0)
        colors = {"Hari Kerja": BLUE, "Non-Kerja": ORANGE}
        fig = go.Figure()
        for col in hourly.columns:
            fig.add_trace(go.Scatter(
                x=hourly.index, y=hourly[col], mode="lines+markers", name=col,
                line=dict(color=colors[col], width=3), marker=dict(size=6),
                hovertemplate="Pukul %{x:02d}:00<br>%{y:,.0f} sepeda/jam<extra>" + col + "</extra>"))
            pk = hourly[col].idxmax()
            fig.add_annotation(x=pk, y=hourly[col].max(), text=f"Puncak {pk:02d}:00 ({hourly[col].max():,.0f})",
                               showarrow=True, arrowhead=0, ay=-30, font=dict(color=colors[col], size=12))
        style(fig, "Rata-rata penyewaan per jam", ytitle="Sepeda per jam", xtitle="Jam dalam sehari")
        fig.update_xaxes(dtick=1)
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, width="stretch", config=CONFIG)

        parts = []
        for col in hourly.columns:
            parts.append(f"<b>{col}</b>: puncak pukul {hourly[col].idxmax():02d}:00 ({hourly[col].max():,.0f}/jam), "
                         f"tersepi pukul {hourly[col].idxmin():02d}:00 ({hourly[col].min():,.0f}/jam)")
        insight("<br>".join(parts) + "<br>Rebalancing armada sebaiknya dijadwalkan sebelum jam puncak.")
    else:
        order = {n: i for i, n in enumerate(DAYS)}
        heat = h.groupby(["weekday_label", "hr"])[metric].mean().unstack()
        heat = heat.reindex(DAYS)
        fig = go.Figure(go.Heatmap(
            z=heat.values, x=heat.columns, y=heat.index, colorscale=[[0, "#eef4f7"], [1, BLUE]],
            colorbar=dict(title="Sepeda/jam"),
            hovertemplate="%{y}, pukul %{x:02d}:00<br>%{z:,.0f} sepeda/jam<extra></extra>"))
        style(fig, "Rata-rata penyewaan per jam menurut hari", ytitle=None, xtitle="Jam dalam sehari", zero=False)
        fig.update_xaxes(dtick=1)
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, width="stretch", config=CONFIG)
        insight("Warna lebih gelap berarti permintaan lebih tinggi. Senin-Jumat memperlihatkan dua pita komuter "
                "(pagi dan sore), sedangkan Sabtu-Minggu terpusat di siang hari.")

# ---------------- Tab 2 ----------------
with tab2:
    st.subheader("Pertanyaan 2: Seberapa besar pengaruh cuaca dan musim?")
    stat = st.radio("Ukuran", ["Rata-rata", "Median"], horizontal=True)
    fn = "mean" if stat == "Rata-rata" else "median"

    c1, c2 = st.columns(2)
    wdf = d.groupby("weather_label")[metric].agg(fn).reindex([w for w in WEATHERS if w in d["weather_label"].values])
    base = day_df[day_df["year"].isin(years) & day_df["weather_label"].eq("Cerah")][metric].agg(fn)
    colors_w = [BLUE if w == "Cerah" else RED if w == "Hujan/Salju Ringan" else GREY for w in wdf.index]
    labels = []
    for w, v in wdf.items():
        labels.append(f"{v:,.0f}" if w == "Cerah" or not base else f"{v:,.0f}<br>({(v / base - 1) * 100:+.0f}%)")
    fig = go.Figure(go.Bar(x=wdf.index, y=wdf.values, marker_color=colors_w, text=labels, textposition="outside",
                           hovertemplate="%{x}<br>%{y:,.0f} sepeda/hari<extra></extra>"))
    style(fig, f"{stat} penyewaan harian per cuaca", ytitle="Sepeda per hari")
    fig.update_yaxes(range=[0, wdf.max() * 1.25])
    c1.plotly_chart(fig, width="stretch", config=CONFIG)

    sdf = d.groupby("season_label")[metric].agg(fn).reindex([s for s in SEASONS if s in d["season_label"].values])
    colors_s = [BLUE if s == sdf.idxmax() else RED if s == sdf.idxmin() else GREY for s in sdf.index]
    fig = go.Figure(go.Bar(x=sdf.index, y=sdf.values, marker_color=colors_s, text=[f"{v:,.0f}" for v in sdf.values],
                           textposition="outside", hovertemplate="%{x}<br>%{y:,.0f} sepeda/hari<extra></extra>"))
    style(fig, f"{stat} penyewaan harian per musim", ytitle="Sepeda per hari")
    fig.update_yaxes(range=[0, sdf.max() * 1.2])
    c2.plotly_chart(fig, width="stretch", config=CONFIG)

    msg = f"Musim tertinggi: <b>{sdf.idxmax()}</b> ({sdf.max():,.0f}/hari); terendah: <b>{sdf.idxmin()}</b> ({sdf.min():,.0f}/hari)."
    if "Cerah" in wdf.index and base:
        drops = [f"{w} {(1 - v / base) * 100:.0f}%" for w, v in wdf.items() if w != "Cerah"]
        if drops:
            msg += " Penurunan dibanding hari cerah: " + ", ".join(drops) + "."
    insight(msg)

    st.markdown("**Hubungan suhu dan penyewaan harian**")
    fig = go.Figure(go.Scatter(
        x=d["temp_c"], y=d[metric], mode="markers", marker=dict(color=BLUE, size=7, opacity=0.5),
        customdata=d[["dteday", "weather_label"]].assign(dteday=d["dteday"].dt.strftime("%d %b %Y")),
        hovertemplate="%{customdata[0]}<br>Suhu %{x:.1f} C<br>%{y:,.0f} sepeda<br>%{customdata[1]}<extra></extra>"))
    style(fig, "Suhu vs penyewaan harian (satu titik = satu hari)", height=380, ytitle="Sepeda per hari",
          xtitle="Suhu (derajat Celsius)")
    st.plotly_chart(fig, width="stretch", config=CONFIG)
    corr = d[["temp_c", metric]].corr().iloc[0, 1]
    insight(f"Korelasi suhu dengan penyewaan pada data terpilih: <b>{corr:.2f}</b> (semakin hangat, semakin banyak penyewaan).")

# ---------------- Tab 3 ----------------
with tab3:
    st.subheader("Pertanyaan 3: Seberapa cepat penyewaan tumbuh?")
    monthly = d.pivot_table(index="mnth", columns="year", values=metric, aggfunc="sum").reindex(range(1, 13))

    c1, c2 = st.columns([3, 2])
    fig = go.Figure()
    for yr, color in [(2011, GREY), (2012, BLUE)]:
        if yr in monthly.columns:
            fig.add_trace(go.Scatter(x=MONTHS, y=monthly[yr], mode="lines+markers", name=str(yr),
                                     line=dict(color=color, width=3),
                                     hovertemplate="%{x} " + str(yr) + "<br>%{y:,.0f} sepeda<extra></extra>"))
    style(fig, "Total penyewaan per bulan", ytitle="Total penyewaan")
    fig.update_layout(hovermode="x unified")
    c1.plotly_chart(fig, width="stretch", config=CONFIG)

    share = d.groupby("year")[["registered", "casual"]].sum()
    share = share.div(share.sum(axis=1), axis=0) * 100
    fig = go.Figure()
    for col, color, name in [("registered", BLUE, "Registered"), ("casual", ORANGE, "Casual")]:
        fig.add_trace(go.Bar(x=share.index.astype(str), y=share[col], name=name, marker_color=color,
                             text=[f"{v:.1f}%" for v in share[col]], textposition="inside",
                             textfont=dict(color="white"),
                             hovertemplate=name + " %{x}<br>%{y:.1f}%<extra></extra>"))
    style(fig, "Proporsi tipe pengguna", ytitle="Persen dari total")
    fig.update_layout(barmode="stack")
    fig.update_yaxes(range=[0, 100])
    c2.plotly_chart(fig, width="stretch", config=CONFIG)

    if {2011, 2012} <= set(monthly.columns):
        yoy = (monthly[2012] / monthly[2011] - 1) * 100
        valid = yoy.dropna()
        fig = go.Figure(go.Bar(
            x=[MONTHS[i - 1] for i in valid.index], y=valid.values, marker_color=BLUE,
            text=[f"{v:.0f}%" for v in valid.values], textposition="outside",
            hovertemplate="%{x}<br>Pertumbuhan %{y:.1f}%<extra></extra>"))
        style(fig, "Pertumbuhan year-over-year per bulan (2012 dibanding 2011)", height=360, ytitle="Pertumbuhan (%)")
        fig.update_yaxes(range=[0, max(valid.max() * 1.2, 10)])
        st.plotly_chart(fig, width="stretch", config=CONFIG)

        tot = d.groupby("year")[metric].sum()
        reg = d.groupby("year")[["registered", "casual"]].sum()
        insight(f"Total penyewaan 2012 naik <b>{(tot[2012] / tot[2011] - 1) * 100:.1f}%</b> dibanding 2011. "
                f"Registered tumbuh {(reg.loc[2012, 'registered'] / reg.loc[2011, 'registered'] - 1) * 100:.1f}%, "
                f"casual {(reg.loc[2012, 'casual'] / reg.loc[2011, 'casual'] - 1) * 100:.1f}%.")
        with st.expander("Lihat tabel data bulanan"):
            table = pd.DataFrame({"Bulan": MONTHS, "2011": monthly[2011], "2012": monthly[2012], "YoY (%)": yoy.round(1)})
            st.dataframe(table.dropna().reset_index(drop=True), hide_index=True)
    else:
        st.info("Pilih tahun 2011 dan 2012 sekaligus untuk melihat pertumbuhan year-over-year.")

st.caption("Proyek Analisis Data - Firas Razin")
