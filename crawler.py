import os
import time
import threading
import requests
import pandas as pd
from datetime import datetime, timedelta
import schedule
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ================== CẤU HÌNH ==================
API_URL = "https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx"
CACHE_DIR = "data_cache"
DEFAULT_SYMBOL = "HPG"
MAX_PAGES = 120
SCHED_TIME = "17:00"

os.makedirs(CACHE_DIR, exist_ok=True)


# ================== HÀM LẤY DỮ LIỆU ==================
def get_stock_data(symbol, max_pages=MAX_PAGES):
    all_data = []
    page = 1
    while page <= max_pages:
        params = {
            "Symbol": symbol.upper(),
            "StartDate": "",
            "EndDate": "",
            "PageIndex": page,
            "PageSize": 100
        }
        response = requests.get(API_URL, params=params, timeout=10)
        try:
            data = response.json()
        except:
            break

        if not data or "Data" not in data or not data["Data"]:
            break

        items = data["Data"].get("Data", [])
        if not items:
            break

        for item in items:
            all_data.append({
                "Ngày": item.get("Ngay"),
                "Mở cửa": item.get("GiaMoCua"),
                "Đóng cửa": item.get("GiaDongCua"),
                "Cao nhất": item.get("GiaCaoNhat"),
                "Thấp nhất": item.get("GiaThapNhat"),
                "Khối lượng": item.get("KhoiLuongKhopLenh")
            })
        page += 1

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data)

    # chuẩn hóa dữ liệu
    df["Ngày"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")
    df["Ngày"] = df["Ngày"].apply(lambda x: x.replace(hour=17) if pd.notnull(x) else x)
    for col in ["Mở cửa", "Đóng cửa", "Cao nhất", "Thấp nhất", "Khối lượng"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.dropna(subset=["Ngày"]).sort_values("Ngày").reset_index(drop=True)


# ================== QUẢN LÝ FILE CACHE ==================
def cache_path(symbol: str) -> str:
    return os.path.join(CACHE_DIR, f"{symbol.upper()}.csv")


def save_to_cache(symbol: str, df: pd.DataFrame) -> None:
    df.to_csv(cache_path(symbol), index=False, encoding="utf-8")


def load_from_cache(symbol: str) -> pd.DataFrame:
    path = cache_path(symbol)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, parse_dates=["Ngày"])
            return df.sort_values("Ngày").reset_index(drop=True)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


# ================== BACKGROUND SCHEDULE ==================
def update_all_cached_symbols():
    files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".csv")]
    symbols = [os.path.splitext(f)[0].upper() for f in files]
    if not symbols:
        symbols = [DEFAULT_SYMBOL]

    for sym in symbols:
        try:
            print(f"[Cập nhật] Đang tải dữ liệu {sym} ...")
            df = get_stock_data(sym, max_pages=MAX_PAGES)
            if not df.empty:
                save_to_cache(sym, df)
                print(f"[Cập nhật] Hoàn tất {sym}, số dòng = {len(df)}")
            else:
                print(f"[Cập nhật] Không có dữ liệu cho {sym}")
        except Exception as e:
            print(f"[Cập nhật] Lỗi khi cập nhật {sym}: {e}")


def scheduler_thread():
    schedule.every().day.at(SCHED_TIME).do(update_all_cached_symbols)
    print(f"[Scheduler] Sẽ tự động cập nhật lúc {SCHED_TIME} mỗi ngày.")
    while True:
        schedule.run_pending()
        time.sleep(30)


def start_scheduler_in_thread():
    t = threading.Thread(target=scheduler_thread, daemon=True)
    t.start()
    return t


# ================== VẼ BIỂU ĐỒ ==================
def make_figure(df: pd.DataFrame, symbol: str,
                show_open=True, show_high=False, show_low=False, show_volume=True) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="Không có dữ liệu")
        return fig

    df = df.copy()
    df["Ngày"] = pd.to_datetime(df["Ngày"])

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.75, 0.25], vertical_spacing=0.05,
                        subplot_titles=(f"{symbol} - Giá cổ phiếu", "Khối lượng"))

    # Đóng cửa
    fig.add_trace(go.Scatter(
        x=df["Ngày"], y=df["Đóng cửa"], mode="lines+markers",
        name="Đóng cửa", line=dict(color="blue", width=2)
    ), row=1, col=1)

    # Mở cửa
    if show_open:
        fig.add_trace(go.Scatter(
            x=df["Ngày"], y=df["Mở cửa"], mode="lines",
            name="Mở cửa", line=dict(color="green", dash="dash")
        ), row=1, col=1)

    # Cao nhất
    if show_high:
        fig.add_trace(go.Scatter(
            x=df["Ngày"], y=df["Cao nhất"], mode="lines",
            name="Cao nhất", line=dict(color="red", dash="dot")
        ), row=1, col=1)

    # Thấp nhất
    if show_low:
        fig.add_trace(go.Scatter(
            x=df["Ngày"], y=df["Thấp nhất"], mode="lines",
            name="Thấp nhất", line=dict(color="orange", dash="dashdot")
        ), row=1, col=1)

    # Khối lượng
    if show_volume:
        fig.add_trace(go.Bar(
            x=df["Ngày"], y=df["Khối lượng"],
            name="Khối lượng", marker=dict(color="rgba(128,128,128,0.6)")
        ), row=2, col=1)

    # Layout
    fig.update_layout(
        hovermode="x unified",
        template="plotly_white",
        height=700,
        legend=dict(orientation="h",     # legend nằm ngang
        yanchor="bottom",
        y=1.07,              # đẩy legend lên cao hơn so với subplot title
        xanchor="center",    # canh giữa
        x=0.5,
        )
    )

    # Trục thời gian → tick theo ngày
    fig.update_xaxes(
        tickformat="%d-%m-%Y",  # hiển thị ngày/tháng/năm
        showgrid=True
    )

    fig.update_yaxes(title_text="Giá (VND)", row=1, col=1)
    fig.update_yaxes(title_text="Khối lượng", row=2, col=1)

    return fig


# ================== STREAMLIT ==================
def main():
    st.title("📊 Dashboard chứng khoán CafeF")

    symbol = st.text_input("Nhập mã cổ phiếu:", DEFAULT_SYMBOL)
    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("Chọn ngày bắt đầu", datetime.today() - timedelta(days=365))
    with col2:
        date_to = st.date_input("Chọn ngày kết thúc (để trống nếu muốn lấy đến hiện tại)", value=None)
    if date_to is None:
        date_to = datetime.today().date()

    if st.button("Hiển thị biểu đồ"):
        df = load_from_cache(symbol)
        if df.empty:
            df = get_stock_data(symbol)
            if not df.empty:
                save_to_cache(symbol, df)

        if not df.empty:
            date_to_final = pd.to_datetime(date_to) if date_to else pd.to_datetime(datetime.today())
            df_filtered = df[(df["Ngày"] >= pd.to_datetime(date_from)) & (df["Ngày"] <= date_to_final)]
            if not df_filtered.empty:
                st.success(f"Hiển thị {len(df_filtered)} dòng dữ liệu cho {symbol}")
                df_display = df_filtered.copy()
                df_display["Ngày"] = df_display["Ngày"].dt.strftime("%d/%m/%Y")  # chỉ ngày/tháng/năm
                st.dataframe(df_display.tail(120))

                fig = make_figure(df_filtered, symbol,
                                  show_open=True, show_high=True,
                                  show_low=True, show_volume=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Không có dữ liệu trong khoảng thời gian này.")
        else:
            st.error("Không lấy được dữ liệu.")


if __name__ == "__main__":
    start_scheduler_in_thread()
    main()
