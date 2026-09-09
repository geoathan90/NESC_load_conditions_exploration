import pandas as pd

from nesc_weather.statistics import spatial_domain_summary


def test_spatial_summary_includes_context_aware_tail_metrics() -> None:
    cells = pd.DataFrame(
        {
            "t2m_c_p05": [-5.0, -3.0],
            "t2m_c_min": [-12.0, -9.0],
            "dewpoint_depression_c_p05": [0.3, 0.8],
            "cbh_p05": [120.0, 250.0],
            "fg10_p99": [18.0, 22.0],
            "precip_rate_mmh_p99": [2.0, 3.0],
            "snowfall_rate_mmh_p99": [1.0, 1.5],
            "tcslw_p99": [0.3, 0.5],
        }
    )

    result = spatial_domain_summary(cells)
    metrics = set(result["metric"])

    assert {
        "t2m_c_p05",
        "t2m_c_min",
        "dewpoint_depression_c_p05",
        "cbh_p05",
        "fg10_p99",
        "precip_rate_mmh_p99",
        "snowfall_rate_mmh_p99",
        "tcslw_p99",
    } <= metrics

    coldest = result.loc[result["metric"] == "t2m_c_min"].iloc[0]
    assert coldest["domain_min"] == -12.0
    assert coldest["domain_max"] == -9.0
