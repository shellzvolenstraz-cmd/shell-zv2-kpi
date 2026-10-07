import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Radiant KPI Dashboard - Shell ZV2", layout="wide", page_icon="⛽")

st.title("⛽ Radiant KPI & Štatistický Dashboard")
st.subheader("Automatické spracovanie denných uzávierok z Radiantu")

col1, col2 = st.columns(2)
with col1:
    item_file = st.file_uploader("1. Nahrajte report položiek (24HourItemSalesReport)", type=["xls", "html", "txt", "htm"])
with col2:
    pay_file = st.file_uploader("2. Nahrajte report platieb (24hvýkazospôsobeplatby)", type=["xls", "html", "txt", "htm"])

def parse_number(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).replace('\xa0', '').replace(' ', '').replace(',', '.')
    match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
    return float(match.group()) if match else 0.0

if item_file and pay_file:
    try:
        # Čítanie súborov
        item_bytes = item_file.read()
        pay_bytes = pay_file.read()

        # Pokus o načítanie HTML tabuliek pomocou pandas
        try:
            item_dfs = pd.read_html(item_bytes, encoding='utf-16')
        except Exception:
            item_dfs = pd.read_html(item_bytes, encoding='utf-8')

        try:
            pay_dfs = pd.read_html(pay_bytes, encoding='utf-16')
        except Exception:
            pay_dfs = pd.read_html(pay_bytes, encoding='utf-8')

        # Spojenie všetkých tabuliek z reportu
        item_df = pd.concat(item_dfs, ignore_index=True)
        pay_df = pd.concat(pay_dfs, ignore_index=True)

        st.success("✅ Súbory z Radiantu boli úspešne načítané!")

        # Vyhľadávanie hodnôt v položkovom reporte
        def find_item_qty_or_amount(keyword):
            for idx, row in item_df.iterrows():
                row_str = " ".join(row.astype(str))
                if re.search(re.escape(keyword), row_str, re.IGNORECASE):
                    # Získanie čísel z riadku
                    nums = [parse_number(val) for val in row if parse_number(val) > 0]
                    if nums:
                        return nums[-1] # Posledné číslo býva suma / množstvo
            return 0.0

        fs = find_item_qty_or_amount('Natural 95')
        vpr = find_item_qty_or_amount('V-Power Racing')
        vp = find_item_qty_or_amount('V-Power')
        fsd = find_item_qty_or_amount('Diesel')
        vpd = find_item_qty_or_amount('V-Power Diesel')
        adblue = find_item_qty_or_amount('AdBlue')

        coffee = find_item_qty_or_amount('Espresso')
        hotdog = find_item_qty_or_amount('Hot-Dog') or find_item_qty_or_amount('HotDogy')

        # Transakcie z výkazu platieb
        transactions = 0.0
        for idx, row in pay_df.iterrows():
            row_str = " ".join(row.astype(str))
            if 'total' in row_str.lower() or 'spolu' in row_str.lower():
                nums = [parse_number(val) for val in row if parse_number(val) > 0]
                if nums:
                    transactions = nums[-1]
                    break

        if transactions == 0:
            transactions = 800.0 # záložná hodnota ak sa nenašla

        # Zobrazenie KPI
        total_liters = fs + vpr + vp + fsd + vpd

        st.markdown("### 📊 Hlavné Denné Ukazovatele (KPI)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Celkové Palivá", f"{total_liters:,.2f} L")
        c2.metric("Počet Transakcií", f"{int(transactions)} ks")
        c3.metric("Priemerná Čerpaná Dávka", f"{(total_liters / transactions if transactions > 0 else 0):.2f} L / tran.")
        
        pref_fuels = vpr + vp + vpd
        pref_pen = (pref_fuels / total_liters * 100) if total_liters > 0 else 0
        c4.metric("Penetrácia Prémiových Palív", f"{pref_pen:.2f} %")

        st.markdown("---")
        st.markdown("### 🔍 Extrahované Hodnoty z Reportu")
        st.write({
            "Natural 95": fs,
            "V-Power 95": vp,
            "V-Power Racing": vpr,
            "Diesel": fsd,
            "V-Power Diesel": vpd,
            "AdBlue": adblue,
            "Káva": coffee,
            "HotDog": hotdog,
            "Transakcie": transactions
        })

    except Exception as e:
        st.error(f"⚠️ Nepodarilo sa automaticky prečítať štruktúru HTML tabuľky: {e}")
        st.info("Ukážka surového textu zo súboru pre diagnostiku:")
        item_text = item_file.read().decode('utf-16', errors='ignore')[:1000]
        st.text_area("Surový text (prvých 1000 znakov)", item_text, height=200)

else:
    st.info("👆 Nahrajte oba reporty z Radiantu hore vo formulári.")
