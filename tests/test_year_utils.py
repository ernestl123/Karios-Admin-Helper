import json
import pytest
from utils.year_utils import (
    load_current_years,
    save_current_years,
    update_class_year,
    calculate_transition_years,
    format_class_role_name,
    format_class_channel_name
)

def test_load_and_save_current_years(tmp_path):
    test_file = tmp_path / "years.json"
    data = {
        "Senior": 2026,
        "Junior": 2027,
        "Sophomore": 2028,
        "Freshman": 2029
    }
    save_current_years(data, str(test_file))
    loaded = load_current_years(str(test_file))
    assert loaded == data

def test_load_current_years_default_fallback(tmp_path):
    non_existent = tmp_path / "does_not_exist.json"
    years = load_current_years(str(non_existent))
    assert "Senior" in years
    assert "Freshman" in years

def test_update_class_year_success(tmp_path):
    test_file = tmp_path / "years.json"
    data = {
        "Senior": 2026,
        "Junior": 2027,
        "Sophomore": 2028,
        "Freshman": 2029
    }
    save_current_years(data, str(test_file))
    updated = update_class_year("Senior", 2030, str(test_file))
    assert updated["Senior"] == 2030

    reloaded = load_current_years(str(test_file))
    assert reloaded["Senior"] == 2030

def test_update_class_year_invalid_name(tmp_path):
    test_file = tmp_path / "years.json"
    data = {"Senior": 2026}
    save_current_years(data, str(test_file))

    with pytest.raises(ValueError, match="Invalid class name 'SuperSenior'"):
        update_class_year("SuperSenior", 2030, str(test_file))

def test_calculate_transition_years():
    # When Class of 26 graduates:
    # Senior -> 2027, Junior -> 2028, Sophomore -> 2029, Freshman -> 2030
    years = calculate_transition_years(26)
    assert years["Senior"] == 2027
    assert years["Junior"] == 2028
    assert years["Sophomore"] == 2029
    assert years["Freshman"] == 2030

def test_format_class_role_and_channel_name():
    assert format_class_role_name(2026) == "Class of '26"
    assert format_class_role_name(2030) == "Class of '30"
    assert format_class_channel_name(2026) == "co-2026"
    assert format_class_channel_name(2030) == "co-2030"
