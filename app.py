import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# ----------------- CONFIG -----------------
st.set_page_config(page_title="Health & Workout Tracker", layout="wide")

WORKOUTS_FILE = Path("workouts.csv")
NUTRITION_FILE = Path("nutrition.csv")

# ----------------- UTILITIES -----------------

def load_csv(path: Path, columns: list):
    """Load a CSV file and ensure required columns exist."""
    if path.exists():
        df = pd.read_csv(path)
        for col in columns:
            if col not in df.columns:
                df[col] = None
        return df[columns]
    else:
        return pd.DataFrame(columns=columns)

def save_csv(df: pd.DataFrame, path: Path):
    """Save DataFrame to CSV."""
    df.to_csv(path, index=False)

def ensure_date_col(df: pd.DataFrame, col: str = "date"):
    """Ensure a column is parsed as date (no time component) safely."""
    if df.empty:
        return df
    df[col] = pd.to_datetime(df[col], errors='coerce', infer_datetime_format=True)
    df[col] = df[col].dt.normalize()  # removes time portion
    return df

# ----------------- LOAD DATA -----------------

workout_cols = ["date", "exercise", "sets", "reps", "weight", "notes"]
nutrition_cols = ["date", "calories", "protein", "carbs", "fat", "sugar", "notes"]

workouts_df = load_csv(WORKOUTS_FILE, workout_cols)
nutrition_df = load_csv(NUTRITION_FILE, nutrition_cols)

workouts_df = ensure_date_col(workouts_df, "date")
nutrition_df = ensure_date_col(nutrition_df, "date")

# ----------------- UI LAYOUT -----------------

st.title("💪 Health & Workout Tracker")

page = st.sidebar.radio(
    "Navigation",
    [
        "Log Workout",
        "Workout History",
        "Log Nutrition",
        "Nutrition Summary",
        "Import / Export"
    ]
)

# ----------------- PAGE: LOG WORKOUT -----------------

if page == "Log Workout":
    st.header("🏋️ Log Workout")

    col1, col2 = st.columns(2)

    with col1:
        w_date = st.date_input("Date", datetime.today(), key="workout_date")
        exercise = st.text_input("Exercise", placeholder="e.g. Barbell Bench Press")
        sets = st.number_input("Sets", min_value=1, step=1, value=3)
        reps = st.number_input("Reps", min_value=1, step=1, value=10)

    with col2:
        weight = st.number_input("Weight (lbs)", min_value=0.0, step=2.5, value=0.0)
        notes = st.text_area("Notes", placeholder="Optional notes...")

    if st.button("Add Workout Entry"):
        new_row = {
            "date": w_date.strftime("%Y-%m-%d"),
            "exercise": exercise,
            "sets": int(sets),
            "reps": int(reps),
            "weight": float(weight),
            "notes": notes,
        }
        workouts_df = pd.concat([workouts_df, pd.DataFrame([new_row])], ignore_index=True)
        save_csv(workouts_df, WORKOUTS_FILE)
        st.success("Workout entry added.")

    st.subheader("Recent Workout Entries")
    if workouts_df.empty:
        st.info("No workouts logged yet.")
    else:
        st.dataframe(workouts_df.sort_values("date", ascending=False).head(20))

# ----------------- PAGE: WORKOUT HISTORY -----------------

elif page == "Workout History":
    st.header("📈 Workout History & Progress")

    if workouts_df.empty:
        st.info("No workouts logged yet. Add entries on the 'Log Workout' page.")
    else:
        exercises = sorted(workouts_df["exercise"].dropna().unique())
        selected_exercise = st.selectbox("Select exercise to view progress:", exercises)

        filtered = workouts_df[workouts_df["exercise"] == selected_exercise].copy()
        filtered = filtered.sort_values("date")

        if filtered.empty:
            st.warning("No data for this exercise yet.")
        else:
            st.subheader(f"Weight Progress for: {selected_exercise}")
            plot_df = filtered.dropna(subset=["weight"])
            if not plot_df.empty:
                chart_df = plot_df[["date", "weight"]].set_index("date")
                st.line_chart(chart_df)
            else:
                st.info("No weight values to plot for this exercise.")

            st.subheader("History Table")
            st.dataframe(
                filtered.sort_values("date", ascending=False).reset_index(drop=True)
            )

            # Simple stats
            if not plot_df.empty:
                start_weight = plot_df["weight"].iloc[0]
                current_weight = plot_df["weight"].iloc[-1]
                change = current_weight - start_weight
                pct_change = (change / start_weight * 100) if start_weight != 0 else 0
                st.markdown(
                    f"**Start:** {start_weight:.1f} lbs → "
                    f"**Current:** {current_weight:.1f} lbs "
                    f"(**Δ {change:+.1f} lbs, {pct_change:+.1f}%**) "
                )

# ----------------- PAGE: LOG NUTRITION -----------------

elif page == "Log Nutrition":
    st.header("🍽️ Log Nutrition")

    col1, col2, col3 = st.columns(3)

    with col1:
        n_date = st.date_input("Date", datetime.today(), key="nut_date")
        calories = st.number_input("Calories", min_value=0, step=10, value=0)
    with col2:
        protein = st.number_input("Protein (g)", min_value=0.0, step=1.0, value=0.0)
        carbs = st.number_input("Carbs (g)", min_value=0.0, step=1.0, value=0.0)
    with col3:
        fat = st.number_input("Fat (g)", min_value=0.0, step=1.0, value=0.0)
        sugar = st.number_input("Sugar (g)", min_value=0.0, step=1.0, value=0.0)

    n_notes = st.text_area("Notes", placeholder="Optional notes, meal details, etc.")

    if st.button("Add Nutrition Entry"):
        new_row = {
            "date": n_date.strftime("%Y-%m-%d"),
            "calories": int(calories),
            "protein": float(protein),
            "carbs": float(carbs),
            "fat": float(fat),
            "sugar": float(sugar),
            "notes": n_notes,
        }
        nutrition_df = pd.concat([nutrition_df, pd.DataFrame([new_row])], ignore_index=True)
        save_csv(nutrition_df, NUTRITION_FILE)
        st.success("Nutrition entry added.")

    st.subheader("Recent Nutrition Entries")
    if nutrition_df.empty:
        st.info("No nutrition entries yet.")
    else:
        st.dataframe(nutrition_df.sort_values("date", ascending=False).head(20))

# ----------------- PAGE: NUTRITION SUMMARY -----------------

elif page == "Nutrition Summary":
    st.header("📊 Nutrition Summary (Daily / Weekly / Monthly)")

    if nutrition_df.empty:
        st.info("No nutrition data yet. Log entries on the 'Log Nutrition' page.")
    else:
        df = nutrition_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        # Daily totals
        st.subheader("Daily Totals")
        st.dataframe(df.sort_values("date", ascending=False).reset_index(drop=True))

        # Weekly averages
        df["week"] = df["date"].dt.to_period("W").apply(lambda r: r.start_time)
        weekly = (
            df.groupby("week")[["calories", "protein", "carbs", "fat", "sugar"]]
            .mean()
            .round(1)
            .reset_index()
            .sort_values("week", ascending=False)
        )

        st.subheader("Weekly Averages")
        st.dataframe(weekly)

        # Monthly averages
        df["month"] = df["date"].dt.to_period("M").apply(lambda r: r.start_time)
        monthly = (
            df.groupby("month")[["calories", "protein", "carbs", "fat", "sugar"]]
            .mean()
            .round(1)
            .reset_index()
            .sort_values("month", ascending=False)
        )

        st.subheader("Monthly Averages")
        st.dataframe(monthly)

# ----------------- PAGE: IMPORT / EXPORT -----------------

elif page == "Import / Export":
    st.header("📂 Import / Export Data")

    # ---- Workouts ----
    st.subheader("Import Workout History CSV")
    st.markdown(
        "Expected columns: `date,exercise,sets,reps,weight,notes` "
        "(this matches the strict file we built)."
    )

    workout_file = st.file_uploader("Upload workouts.csv", type=["csv"], key="workout_upload")
    if workout_file is not None:
        uploaded = pd.read_csv(workout_file)
        for col in workout_cols:
            if col not in uploaded.columns:
                uploaded[col] = None
        uploaded = uploaded[workout_cols]
        uploaded = ensure_date_col(uploaded, "date")
        workouts_df = uploaded
        save_csv(workouts_df, WORKOUTS_FILE)
        st.success("Workout history imported and saved.")

    st.subheader("Export Current Workout Data")
    if not workouts_df.empty:
        st.download_button(
            "Download workouts.csv",
            data=workouts_df.to_csv(index=False),
            file_name="workouts_export.csv",
            mime="text/csv",
        )
    else:
        st.info("No workout data to export.")

    st.markdown("---")

    # ---- Nutrition ----
    st.subheader("Import Nutrition CSV")
    st.markdown("Expected columns: `date,calories,protein,carbs,fat,sugar,notes`")

    nutrition_file = st.file_uploader("Upload nutrition.csv", type=["csv"], key="nutrition_upload")
    if nutrition_file is not None:
        uploaded_n = pd.read_csv(nutrition_file)
        for col in nutrition_cols:
            if col not in uploaded_n.columns:
                uploaded_n[col] = None
        uploaded_n = uploaded_n[nutrition_cols]
        uploaded_n = ensure_date_col(uploaded_n, "date")
        nutrition_df = uploaded_n
        save_csv(nutrition_df, NUTRITION_FILE)
        st.success("Nutrition history imported and saved.")

    st.subheader("Export Current Nutrition Data")
    if not nutrition_df.empty:
        st.download_button(
            "Download nutrition.csv",
            data=nutrition_df.to_csv(index=False),
            file_name="nutrition_export.csv",
            mime="text/csv",
        )
    else:
        st.info("No nutrition data to export.")
