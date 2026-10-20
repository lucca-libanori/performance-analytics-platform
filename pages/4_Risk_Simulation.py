import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Risk Simulation", layout="wide")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}


def get_engine():
    connection_string = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    )
    return create_engine(connection_string)


def load_settled_profits(engine):
    query = """
    SELECT bet_id, date, time, profit
    FROM bets
    WHERE status IN ('win', 'loss', 'void')
      AND profit IS NOT NULL
    ORDER BY date ASC, time ASC, bet_id ASC;
    """
    return pd.read_sql(query, engine)


def max_drawdown(profits):
    """Maior queda (em unidades, valor positivo) entre um pico e o vale seguinte."""
    cum = np.concatenate([[0.0], np.cumsum(profits)])
    return float((np.maximum.accumulate(cum) - cum).max())


@st.cache_data(show_spinner="Running simulations...")
def simulate_drawdowns(profits, n_sims, seed, batch=1000):
    """
    Reordena aleatoriamente as mesmas apostas (o lucro total é sempre o mesmo)
    e calcula o drawdown máximo de cada ordem.
    Retorna um array com o drawdown máximo (positivo) de cada simulação.
    """
    profits = np.asarray(profits, dtype=float)
    rng = np.random.default_rng(seed)

    results = []
    done = 0
    while done < n_sims:
        b = min(batch, n_sims - done)
        sims = rng.permuted(np.tile(profits, (b, 1)), axis=1)
        cum = np.concatenate([np.zeros((b, 1)), np.cumsum(sims, axis=1)], axis=1)
        dd = (np.maximum.accumulate(cum, axis=1) - cum).max(axis=1)
        results.append(dd)
        done += b

    return np.concatenate(results)


def plot_drawdown_distribution(sim_dd, observed_dd):
    p95 = float(np.percentile(sim_dd, 95))

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=-sim_dd,
        nbinsx=60,
        marker=dict(color="rgba(239, 68, 68, 0.55)", line=dict(color="#0e1117", width=1)),
        hovertemplate="Drawdown: %{x:.1f} u<br>Simulations: %{y}<extra></extra>",
        showlegend=False,
    ))

    fig.add_vline(
        x=-observed_dd, line_width=2.5, line_dash="dash", line_color="#ffffff",
        annotation_text=f"Observed: -{observed_dd:.1f} u",
        annotation_position="top",
        annotation_font=dict(color="#ffffff", size=12),
    )

    fig.add_vline(
        x=-p95, line_width=1.8, line_dash="dot", line_color="#f59e0b",
        annotation_text=f"95th pct: -{p95:.1f} u",
        annotation_position="bottom",
        annotation_font=dict(color="#f59e0b", size=12),
    )

    fig.update_layout(
        height=450,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="white", family="Arial, sans-serif"),
        xaxis=dict(title="Max drawdown (u)", showgrid=False, zeroline=False),
        yaxis=dict(
            title="Simulations",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.06)",
            zeroline=False,
        ),
        bargap=0.03,
        margin=dict(l=20, r=20, t=40, b=20),
        hoverlabel=dict(
            bgcolor="#1f2937", font_size=13, font_color="white",
            bordercolor="rgba(255,255,255,0.1)"
        ),
    )

    return fig


def main():
    st.title("Risk Simulation")
    st.write(
        "Monte Carlo simulation of the maximum drawdown: the same bets are replayed "
        "thousands of times to show how deep a drawdown is *normal* for this "
        "betting history, and whether the one actually observed was unusual."
    )

    try:
        engine = get_engine()
        data = load_settled_profits(engine)

        if len(data) < 30:
            st.info("At least 30 settled bets are needed to run the simulation.")
            return

        profits = data["profit"].to_numpy(dtype=float)

        st.sidebar.header("Simulation settings")

        n_sims = st.sidebar.select_slider(
            "Number of simulations",
            options=[1000, 2000, 5000, 10000, 20000],
            value=5000,
        )
        seed = st.sidebar.number_input("Random seed", min_value=0, value=42, step=1)
        bankroll_units = st.sidebar.number_input(
            "Bankroll size (units)", min_value=1.0, value=100.0, step=10.0,
            help="Used to estimate the chance that a drawdown wipes out this bankroll."
        )

        observed_dd = max_drawdown(profits)
        sim_dd = simulate_drawdowns(profits, int(n_sims), int(seed))

        median_dd = float(np.median(sim_dd))
        p95_dd = float(np.percentile(sim_dd, 95))
        share_as_bad = float((sim_dd >= observed_dd).mean() * 100)
        ruin_prob = float((sim_dd >= bankroll_units).mean() * 100)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Observed max drawdown", f"-{observed_dd:.2f} u")
        c2.metric("Median simulated", f"-{median_dd:.2f} u")
        c3.metric("95th percentile", f"-{p95_dd:.2f} u")
        c4.metric(f"Ruin risk ({bankroll_units:.0f}u bankroll)", f"{ruin_prob:.1f}%")

        fig = plot_drawdown_distribution(sim_dd, observed_dd)
        st.plotly_chart(fig, width="stretch")

        st.subheader("How to read this")

        if share_as_bad < 5:
            verdict = (
                f"In only **{share_as_bad:.1f}%** of the simulations the drawdown was as "
                "deep as the one observed. That is unusually bad luck in the sequence — "
                "or a sign that the bets are not as independent as the simulation assumes."
            )
        elif share_as_bad > 95:
            verdict = (
                f"In **{share_as_bad:.1f}%** of the simulations the drawdown was at least "
                "as deep as the one observed, so the observed path was unusually smooth."
            )
        else:
            verdict = (
                f"In **{share_as_bad:.1f}%** of the simulations the drawdown was at least "
                "as deep as the one observed. The observed drawdown sits well within "
                "the range expected from variance alone."
            )

        st.write(verdict)

    except Exception as e:
        st.error(f"Error loading risk simulation page: {e}")


if __name__ == "__main__":
    main()