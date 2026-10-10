# FutureFund ML Model Card

## Model Overview
The future XGBoost model will target financial-stress estimation based entirely on the synthetic conditions set forth in Dataset V2.

## Intended Use
To estimate whether a specific financial profile + decision + assumption trajectory will likely hit a stressed state defined mathematically as cash balance falling below necessary monthly outflows. 

**Disclaimer**: A good score on this synthetic dataset does not establish real-world predictive accuracy. Stress-event fields such as emergency expenses and temporary income shocks must not be presented as applied simulation variables unless explicitly introduced in a future phase.

## Training Data (Synthetic Dataset V2)
Generated via `app/ml/generate_data.py`, comprising:
- **Base Profiles**: 5,000 distinct synthetic household layouts.
- **Scenario Rows**: 15,000 (3 universes x 5,000 profiles).
- **Label Definition**: `financial_stress_label = 1` if closing cash balance < committed monthly outflow in any simulated month >= 1.
- **Natural Label Distribution**: Approx 46.6% (0 - Safe) / 53.4% (1 - Stressed). Modifiable by adjusting assumption ranges via the reproducible `generate_profile` script.
- **Leakage Prevention**: Future ending savings, minimum cash balances, first reserve-breach occurrences, and subsequent interest metrics are strictly isolated into an outcome file, preventing target leakage into the ML feature space. Profile groups must be uniformly split (i.e., not split across train and test sets).
