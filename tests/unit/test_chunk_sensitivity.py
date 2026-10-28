from scripts.run_chunk_sensitivity import CONFIGURATIONS, summarize


def test_sensitivity_varies_one_parameter_from_baseline():
    assert (200, 40) in CONFIGURATIONS
    assert len(set(CONFIGURATIONS)) == 5
    assert all(size == 200 or overlap == 40 for size, overlap in CONFIGURATIONS)


def test_sensitivity_excludes_unlabelled_pages_from_denominator():
    rows = [
        dict(filing_hit=True, page_hit=True, selected_page_hit=False, selected_tokens=100),
        dict(filing_hit=True, page_hit=None, selected_page_hit=None, selected_tokens=200),
    ]
    result = summarize(rows)
    assert result["page_labelled_case_count"] == 1
    assert result["page_recall"] == 1.0
    assert result["selected_page_recall"] == 0.0
    assert result["mean_selected_tokens"] == 150
