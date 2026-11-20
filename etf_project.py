import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score
from pathlib import Path

TICKERS = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "GLD"]


def download_prices(end="2026-01-01"):
    raw = yf.download(
        TICKERS,
        start="2010-01-01",
        end=end,
        auto_adjust=True,
        progress=False
    )

    if raw.empty:
        raise ValueError("No se descargaron datos.")

    prices = raw["Close"].reindex(columns=TICKERS).sort_index()

    if prices.isna().any().any():
        raise ValueError("Hay precios faltantes. Revisar la descarga.")

    if prices.index.duplicated().any():
        raise ValueError("Hay fechas duplicadas.")

    if not np.isfinite(prices.to_numpy()).all() or (prices <= 0).any().any():
        raise ValueError("Hay precios no válidos.")

    return prices


def prepare_data(prices):
    frames = []

    for ticker in TICKERS:
        p = prices[ticker]
        daily_return = p / p.shift(1) - 1

        df = pd.DataFrame(index=prices.index)
        df["Ticker"] = ticker

        # Información disponible al cierre de cada fecha.
        for window in [1, 5, 20, 60]:
            df[f"return_{window}"] = p / p.shift(window) - 1

        df["volatility_20"] = daily_return.rolling(20).std()
        df["relative_sma_10"] = p / p.rolling(10).mean() - 1
        df["relative_sma_20"] = p / p.rolling(20).mean() - 1
        df["relative_sma_60"] = p / p.rolling(60).mean() - 1

        df["Month"] = prices.index.month.astype(str)
        df["Weekday"] = prices.index.dayofweek.astype(str)

        # Señal al cierre de t.
        # Compra al cierre de t+1 y venta al cierre de t+2.
        df["future_return"] = p.shift(-2) / p.shift(-1) - 1

        # Fecha en que conocemos el resultado de la operación.
        df["label_end"] = pd.Series(
            prices.index, index=prices.index
        ).shift(-2)

        frames.append(df.rename_axis("Date").reset_index())

    data = pd.concat(frames, ignore_index=True)

    numeric = [
        "return_1", "return_5", "return_20", "return_60",
        "volatility_20",
        "relative_sma_10", "relative_sma_20", "relative_sma_60"
    ]

    dummies = pd.get_dummies(
        data[["Ticker", "Month", "Weekday"]],
        dtype=int
    )

    data = pd.concat([data, dummies], axis=1)
    features = numeric + dummies.columns.tolist()

    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.dropna(subset=features).copy()

    # Las últimas filas quedan sin etiqueta: sirven para inferencia.
    data["target"] = np.where(
        data["future_return"].notna(),
        (data["future_return"] > 0).astype(int),
        np.nan
    )

    return data, features


def probability_up(model, X):
    class_position = list(model.classes_).index(1)
    return model.predict_proba(X)[:, class_position]


def train_models(data, features):
    labeled = data.dropna(subset=["target", "label_end"]).copy()

    # Separación cronológica y eliminación de etiquetas
    # que crucen al siguiente periodo.
    train = labeled[
        (labeled["Date"] < "2020-01-01")
        & (labeled["label_end"] < "2020-01-01")
    ]

    valid = labeled[
        (labeled["Date"] >= "2020-01-01")
        & (labeled["Date"] < "2023-01-01")
        & (labeled["label_end"] < "2023-01-01")
    ]

    test = labeled[labeled["Date"] >= "2023-01-01"]

    candidates = {
        "decision_tree": DecisionTreeClassifier(
            max_depth=4,
            min_samples_leaf=50,
            random_state=42
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_leaf=50,
            random_state=42,
            n_jobs=-1
        )
    }

    validation_results = []

    for name, model in candidates.items():
        model.fit(train[features], train["target"].astype(int))
        prediction = model.predict(valid[features])

        validation_results.append({
            "model": name,
            "accuracy": accuracy_score(valid["target"], prediction),
            "precision": precision_score(
                valid["target"], prediction, zero_division=0
            )
        })

    validation_results = pd.DataFrame(validation_results)

    # Elegimos con validación, sin consultar el resultado de test.
    best_name = validation_results.sort_values(
        ["accuracy", "precision"], ascending=False
    ).iloc[0]["model"]

    best_model = candidates[best_name]

    development = labeled[
        (labeled["Date"] < "2023-01-01")
        & (labeled["label_end"] < "2023-01-01")
    ]

    best_model.fit(
        development[features],
        development["target"].astype(int)
    )

    test_prediction = best_model.predict(test[features])

    # Comparación sencilla: predecir siempre que subirá.
    always_up = np.ones(len(test), dtype=int)

    test_results = pd.DataFrame([
        {
            "model": best_name,
            "accuracy": accuracy_score(test["target"], test_prediction),
            "precision": precision_score(
                test["target"], test_prediction, zero_division=0
            )
        },
        {
            "model": "always_up",
            "accuracy": accuracy_score(test["target"], always_up),
            "precision": precision_score(
                test["target"], always_up, zero_division=0
            )
        }
    ])

    split_sizes = {
        "train": len(train),
        "validation": len(valid),
        "test": len(test)
    }

    return best_model, validation_results, test_results, split_sizes


def simulate(prices, target_weights, cost_rate=0.001):
    """
    Pesos al comienzo de cada intervalo cierre a cierre.
    El capital no invertido permanece en efectivo sin intereses.
    Costos aproximados sobre el volumen de compra y venta.
    """
    asset_returns = (
        prices / prices.shift(1) - 1
    ).reindex(target_weights.index)

    previous_weights = np.zeros(len(TICKERS))

    daily_results = []

    for date in target_weights.index:
        desired = target_weights.loc[date, TICKERS].to_numpy(float)
        returns_today = asset_returns.loc[date, TICKERS].to_numpy(float)

        turnover = np.abs(desired - previous_weights).sum()
        cost = cost_rate * turnover

        gross_return = np.dot(desired, returns_today)

        # Primero descontamos costos y después aplicamos el rendimiento.
        net_return = (1 - cost) * (1 + gross_return) - 1

        daily_results.append({
            "Date": date,
            "net_return": net_return,
            "turnover": turnover,
            "cost_fraction": cost
        })

        # Pesos después del movimiento del mercado.
        previous_weights = (
            desired * (1 + returns_today) / (1 + gross_return)
        )

    result = pd.DataFrame(daily_results).set_index("Date")
    result["equity"] = (1 + result["net_return"]).cumprod()

    # Incluye el capital inicial de 1 en el máximo histórico.
    high_water = result["equity"].cummax().clip(lower=1)
    result["drawdown"] = result["equity"] / high_water - 1

    return result


def summarize(result):
    r = result["net_return"]
    equity_final = result["equity"].iloc[-1]
    annual_volatility = r.std() * np.sqrt(252)

    sharpe = (
        r.mean() / r.std() * np.sqrt(252)
        if r.std() > 0 else np.nan
    )

    return {
        "total_return": equity_final - 1,
        "CAGR": equity_final ** (252 / len(r)) - 1,
        "annual_volatility": annual_volatility,
        "max_drawdown": result["drawdown"].min(),
        "sharpe_rf_0": sharpe,
        "total_turnover": result["turnover"].sum()
    }


def run_project(prices, output_dir="results"):
    prices = prices.reindex(columns=TICKERS).sort_index()

    if prices.isna().any().any() or prices.index.duplicated().any():
        raise ValueError("Revisar faltantes o fechas duplicadas.")

    data, features = prepare_data(prices)

    model, validation, test, sizes = train_models(data, features)

    signals = data[data["Date"] >= "2023-01-01"].copy()
    signals["probability_up"] = probability_up(
        model, signals[features]
    )

    probabilities = signals.pivot(
        index="Date", columns="Ticker", values="probability_up"
    ).reindex(index=prices.index, columns=TICKERS)

    # Umbral fijo del proyecto, no optimizado con test.
    # Cada ETF puede ocupar 1/8 del capital.
    signal_weights = probabilities.ge(0.55).astype(float) / len(TICKERS)

    # Señal de t ejecutada al cierre de t+1:
    # obtiene el rendimiento que termina en t+2.
    executed_weights = signal_weights.shift(2).fillna(0)

    first_signal_date = signals["Date"].min()
    first_position = prices.index.get_loc(first_signal_date) + 2
    evaluation_dates = prices.index[first_position:]

    strategy_weights = executed_weights.loc[evaluation_dates]

    equal_weights = pd.DataFrame(
        1 / len(TICKERS),
        index=evaluation_dates,
        columns=TICKERS
    )

    strategy = simulate(prices, strategy_weights)
    benchmark = simulate(prices, equal_weights)

    metrics = pd.DataFrame({
        "model_strategy": summarize(strategy),
        "equal_weight_daily": summarize(benchmark)
    }).T

    importance = pd.Series(
        model.feature_importances_, index=features
    ).sort_values(ascending=False)

    # El modelo se entrenó con datos anteriores a 2023.
    # Estas son probabilidades de investigación, no órdenes reales.
    latest = signals[
        signals["Date"] == signals["Date"].max()
    ][["Date", "Ticker", "probability_up"]].copy()

    latest["signal"] = (latest["probability_up"] >= 0.55).astype(int)

    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)

    validation.to_csv(folder / "validation_metrics.csv", index=False)
    test.to_csv(folder / "test_metrics.csv", index=False)
    metrics.to_csv(folder / "portfolio_metrics.csv")
    latest.to_csv(folder / "latest_signals.csv", index=False)
    importance.to_csv(folder / "feature_importance.csv")
    strategy.to_csv(folder / "strategy_history.csv")
    benchmark.to_csv(folder / "benchmark_history.csv")

    fig, ax = plt.subplots(figsize=(12, 5))
    strategy["equity"].plot(ax=ax, label="Estrategia del modelo")
    benchmark["equity"].plot(ax=ax, label="Pesos iguales diarios")
    ax.set_title("Evaluación fuera de muestra")
    ax.set_ylabel("Capital relativo")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(folder / "equity_comparison.png", dpi=150)
    plt.show()

    extra_checks(prices, data, features, signals, folder)

    return {
        "validation": validation,
        "test": test,
        "metrics": metrics,
        "importance": importance,
        "latest": latest,
        "split_sizes": sizes
    }



def extra_checks(prices, data, features, signals, folder):
    # Reviso la disponibilidad antes de interpretar las gráficas.
    availability = pd.DataFrame({
        "observaciones": prices.count(),
        "faltantes": prices.isna().sum(),
        "primera_fecha": prices.apply(lambda x: x.first_valid_index()),
        "ultima_fecha": prices.apply(lambda x: x.last_valid_index())
    })
    availability.to_csv(folder / "data_availability.csv")
    returns = (prices / prices.shift(1) - 1).iloc[1:]
    returns.corr().to_csv(folder / "return_correlations.csv")
    returns.describe().to_csv(folder / "return_summary.csv")

    # Para la exploración del objetivo uso solamente el desarrollo.
    development = data[
        (data["Date"] < "2023-01-01")
        & (data["label_end"] < "2023-01-01")
    ]
    development.groupby("Ticker")["target"].agg(["count", "mean"]).to_csv(
        folder / "target_by_ticker_development.csv"
    )
    development[features + ["target"]].corr()["target"].drop("target").sort_values().to_csv(
        folder / "feature_target_correlations_development.csv"
    )

    # Simulación vectorizada, como primer ejercicio del módulo 4.
    # Cada fila supone una operación independiente de 100 USD.
    trades = signals.dropna(subset=["future_return"]).copy()
    trades["selected"] = (trades["probability_up"] >= 0.55).astype(int)
    trades["gross_profit_usd"] = trades["selected"] * 100 * trades["future_return"]
    trades["fees_usd"] = trades["selected"] * 100 * 0.002
    trades["net_profit_usd"] = trades["gross_profit_usd"] - trades["fees_usd"]
    trades[["Date", "Ticker", "future_return", "selected", "gross_profit_usd", "fees_usd", "net_profit_usd"]].to_csv(
        folder / "independent_trade_simulation.csv", index=False
    )
    # Este total no es un rendimiento de portafolio: no fija el capital disponible.
    pd.DataFrame([{
        "selected_trades": int(trades["selected"].sum()),
        "gross_profit_usd": trades["gross_profit_usd"].sum(),
        "fees_usd": trades["fees_usd"].sum(),
        "net_profit_usd": trades["net_profit_usd"].sum()
    }]).to_csv(folder / "independent_trade_summary.csv", index=False)

    fig, ax = plt.subplots(figsize=(11, 5))
    (prices / prices.iloc[0] * 100).plot(ax=ax)
    ax.set(title="Evolución histórica: inicio = 100", ylabel="Valor relativo")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(folder / "normalized_prices.png", dpi=150)
    plt.close(fig)

    corr = returns.corr()
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(corr)), corr.columns, rotation=45)
    ax.set_yticks(range(len(corr)), corr.index)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iloc[i,j]:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title("Correlación de rendimientos diarios: descriptivo 2010–2025")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(folder / "correlations.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 4))
    for filename, label in [("strategy_history.csv", "Modelo"), ("benchmark_history.csv", "Pesos iguales")]:
        history = pd.read_csv(folder / filename, index_col=0, parse_dates=True)
        (history["drawdown"] * 100).plot(ax=ax, label=label)
    ax.set(title="Caídas desde máximos: periodo de prueba", ylabel="Caída (%)")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(folder / "drawdown_comparison.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    prices = download_prices()
    results = run_project(prices)

    print("Tamaños de los conjuntos:", results["split_sizes"])
    print("\nValidación:\n", results["validation"])
    print("\nTest:\n", results["test"])
    print("\nPortafolios:\n", results["metrics"])
    print("\nSeñales más recientes:\n", results["latest"])
