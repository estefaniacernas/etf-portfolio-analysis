# Verification

- Reviewed the code and notebook outputs.
- Ran the full script using a fresh download.
- Executed the notebook cells in order with local IPython, rather than a remote Colab kernel. Installation was skipped because dependencies were available.
- Checked synthetic examples: changing the last price does not change earlier features; the target matches the return from t+1 to t+2; flat prices and zero costs leave capital unchanged; a 0.1% initial fee reduces capital to 0.999 without repeated fees if no rebalancing occurs; drawdown includes the initial cost.
- Reviewed the training and validation boundaries. Future targets are not included among the predictors.
- The decision tree test accuracy remained 54.25% on repeated execution. Adjusted prices and random forest results can change slightly across fresh downloads.
- Model parameters and the threshold were not changed to improve observed test results.
- The English version translates comments, explanations, table headers, and plot labels. The code structure and numerical portfolio outputs were preserved; model fitting was not repeated for this translation. Only the descriptive price plot required a new download.
- Returns were not verified against another price provider or real trades.

These checks cover code behavior. They do not establish future profitability.
