# ETF selection with a classification model

I wanted to see whether a model could help me select ETFs and how that would compare with dividing capital equally across all of them. I also looked at drawdowns and trading costs.

## Data

- Source: Yahoo Finance through yfinance, using adjusted daily prices.
- Period: January 4, 2010 through December 31, 2025. The requested end date, January 1, 2026, is exclusive.
- Universe: SPY, QQQ, IWM, EFA, EEM, TLT, IEF, and GLD.
- 4,024 sessions per ETF: 32,192 date–asset observations before rolling windows and labels.
- No missing prices or duplicate dates in the checked download.
- The universe is a fixed retrospective selection, not a historical universe accounting for fund closures or survivorship bias.

| Ticker | General exposure |
|---|---|
| SPY | US large-cap equities |
| QQQ | Nasdaq-100 |
| IWM | US small-cap equities |
| EFA | Developed-market equities outside the US and Canada |
| EEM | Emerging-market equities |
| IEF | US Treasury bonds with 7–10 year maturities |
| TLT | US Treasury bonds with maturities above 20 years |
| GLD | Gold |

## Method

1. Check dates, availability, and prices.
2. Calculate returns, volatility, and correlations.
3. Create eight numerical features: returns over 1, 5, 20, and 60 sessions; 20-session volatility; and price relative to its 10-, 20-, and 60-session moving averages. Add ticker, month, and weekday dummies.
4. Define a positive-return classification target. For a signal at the close of t, assume entry at the close of t+1 and exit at the close of t+2. Keep future outcomes out of the predictors.
5. Compare DecisionTreeClassifier (depth 4) and RandomForestClassifier (100 trees, depth 5), both with at least 50 samples per leaf and random seed 42.
6. Train before 2020, validate in 2020–2022, and test from 2023 onward. Exclude labels whose outcome dates cross split boundaries. Select by validation accuracy, using precision as a tie-breaker, and refit on development data available before 2023.
7. Apply a fixed probability threshold of 0.55 in the trading simulation. This project does not include hyperparameter or threshold optimization.
8. Compare a vectorized independent-trade simulation with a sequential simulation that tracks limited portfolio capital.

## Simulation assumptions

- Initial capital is normalized to 1. Assets share a USD quotation basis; there is no conversion to MXN.
- No leverage or short selling. Fractional positions are allowed.
- Each positive signal uses 1/8 of capital. Unallocated capital stays in cash without earning interest.
- Benchmark: all eight ETFs, equally weighted and rebalanced daily.
- Approximate cost of 0.1% per side, applied to absolute weight turnover. This is not a specific broker's fee schedule. Slippage is not modeled separately.
- Capital gains are reinvested. Final holdings are marked to market without a forced final liquidation.
- Sharpe assumes a zero risk-free rate; annualization uses 252 sessions. Taxes are excluded.
- The model stays fixed after development training. Signals dated December 2025 are historical.

## Results


The decision tree was selected on validation. Its test accuracy was 54.25%, compared with 53.90% for always predicting a positive return. That is a difference of 0.35 percentage points. The gap is small. I did not run a statistical significance test to establish whether it holds beyond this sample. Observations from different ETFs on the same date are also not independent.

| Metric | Model strategy | Daily equal weight |
|---|---:|---:|
| Total return | 2.09% | 58.95% |
| Compound annual growth rate | 0.70% | 16.85% |
| Annualized volatility | 1.56% | 10.98% |
| Maximum drawdown | -2.38% | -10.93% |
| Sharpe (risk-free rate = 0%) | 0.453 | 1.473 |


Selecting ETFs with the model did not improve returns in this simulation. The strategy gained 2.09%, while the equal-weight benchmark gained 58.95%. The strategy also had a lower Sharpe ratio.

Its maximum drawdown was smaller, but it also invested less capital because allocations stayed in cash when there was no signal. I cannot attribute the smaller drawdown only to better ETF selection. A comparison with similar invested exposure would help separate these effects.

What stood out to me was that getting slightly more predictions right did not lead to making more money. The size of each gain and loss, trading costs, and the amount of capital left in cash also matter.

I kept the parameters fixed after looking at test results. If I continue with other features or a different rebalancing frequency, I will need another evaluation period rather than choosing rules that fit these test results.

## Files

| File | Contents |
|---|---|
| etf_portfolio_analysis.ipynb | Executed notebook with explanations |
| etf_project.py | Functions and full analysis workflow |
| requirements.txt | Environment package versions |
| RESULTADOS.md | Results discussion and plots |
| VERIFICACION.md | Checks and reproduction limits |
| results/ | Metrics, simulations, correlations, feature importance, and plots |
| execution_manifest.json | Environment information and output checksums |

## Reproduce

The recorded environment used Python 3.12.14. From the project folder:

```bash
python -m venv .venv
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. On Linux/macOS, use `source .venv/bin/activate`. Then run:

```bash
python -m pip install -r requirements.txt
python etf_project.py
```

In Colab, open the notebook and run the cells in order. The `%%writefile` cell recreates the script. Original price CSV files do not need to be uploaded to GitHub because downloading them is part of the workflow.

The CSV files in results are analysis outputs, not the original price dataset. Yahoo may revise adjusted prices, and library versions can affect results, so later executions may differ slightly.

## Limitations

Eight ETFs and one chronological split do not establish a stable trading advantage. Classification accuracy uses the model's predicted class, while trading uses a 0.55 threshold. There is no probability calibration, significance test, exposure-matched comparison, or walk-forward evaluation. Full-history return correlations are descriptive; feature–target correlations use development data only. Tree feature importance does not establish causality.

## Course materials

Adapted from [Analytics in Stock Markets Zoomcamp](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp): Modules 1–2 (data and transformations), 3 (modeling), 4 (simulation), and 5 (scripts and automation). The ETF universe, horizon, and parameter choices belong to this project.

The course project description is in [projects](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp/tree/main/projects).
