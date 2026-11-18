import json
from pathlib import Path
from typing import Dict, Optional

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def get_default_years_path() -> Path:
    """Returns the default path to current_years.json."""
    return get_project_root() / "current_years.json"

def load_current_years(file_path: Optional[str] = None) -> Dict[str, int]:
    """
    Loads current graduation years from JSON file.
    
    Args:
        file_path: Optional path to JSON file. Defaults to current_years.json in root.
        
    Returns:
        dict: Mapping of class name (e.g., 'Senior') to graduation year.
    """
    path = Path(file_path) if file_path else get_default_years_path()
    if not path.exists():
        return {
            "Senior": 2026,
            "Junior": 2027,
            "Sophomore": 2028,
            "Freshman": 2029
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_current_years(years: Dict[str, int], file_path: Optional[str] = None) -> None:
    """
    Saves current graduation years to JSON file.
    
    Args:
        years: Mapping of class name to graduation year.
        file_path: Optional path to JSON file.
    """
    path = Path(file_path) if file_path else get_default_years_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(years, f, indent=4)

def update_class_year(class_name: str, year_number: int, file_path: Optional[str] = None) -> Dict[str, int]:
    """
    Updates the graduation year for a specific class.
    
    Args:
        class_name: Name of the class (Freshman, Sophomore, Junior, Senior).
        year_number: New graduation year.
        file_path: Optional path to JSON file.
        
    Returns:
        dict: Updated graduation years dictionary.
    """
    years = load_current_years(file_path)
    normalized_name = class_name.capitalize()
    if normalized_name not in years:
        raise ValueError(f"Invalid class name '{class_name}'. Valid options are: {', '.join(years.keys())}.")
    years[normalized_name] = year_number
    save_current_years(years, file_path)
    return years

def calculate_transition_years(grad_year: int) -> Dict[str, int]:
    """
    Calculates updated graduation years for all classes given the graduating year (2 digits).
    
    Args:
        grad_year: 2-digit graduation year of graduating seniors (e.g., 26 for 2026).
        
    Returns:
        dict: Updated graduation years for Freshman, Sophomore, Junior, Senior.
    """
    return {
        "Senior": int(f"20{grad_year + 1:02d}"),
        "Junior": int(f"20{grad_year + 2:02d}"),
        "Sophomore": int(f"20{grad_year + 3:02d}"),
        "Freshman": int(f"20{grad_year + 4:02d}")
    }

def format_class_role_name(year: int) -> str:
    """Formats the role name for a class graduation year (e.g., Class of '26)."""
    return f"Class of '{str(year)[-2:]}"

def format_class_channel_name(year: int) -> str:
    """Formats the channel name for a class graduation year (e.g., co-2026)."""
    return f"co-{year}"
