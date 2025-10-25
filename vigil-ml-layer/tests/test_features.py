# import pytest
# import pandas as pd
# from src.features import engineer_features

# @pytest.fixture
# def sample_data():
#     data = {
#         "timestamp": pd.date_range(start="2025-01-01", periods=10, freq="1min"),
#         "node": ["agave1"] * 10,
#         "cpu_usage": [45, 46, 47, 48, 49, 50, 51, 52, 53, 54],
#         "rpc_error_rate": [0.1] * 10,
#         "rpc_latency_ms": [60] * 10,
#         "failure_imminent": [0]  *10
#     }
#     return pd.DataFrame(data)

# def test_engineer_features(sample_data):
#     processed_df = engineer_features(sample_data)
#     assert "cpu_trend" in processed_df.columns
#     assert processed_df["cpu_trend"].iloc[1] == 1  # 46 - 45
#     assert "cpu_rolling_mean" in processed_df.columns
#     assert len(processed_df) == 10
#     assert processed_df["cpu_rolling_mean"].iloc[4] == pytest.approx(47.0)  # Mean of first 5 entries

# def test_engineer_features_empty():
#     df = pd.DataFrame()
#     with pytest.raises(KeyError):
#         engineer_features(df)