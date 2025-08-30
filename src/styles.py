"""Shared CSS snippets for Streamlit user pages."""

CARD_STYLE = """
{
  background-color: #ffffff;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
  border: 1px solid rgba(0,0,0,0.06);
}
h3, p, li, label, span { color: #000; }
div[data-testid=\"stMetricValue\"], div[data-testid=\"stMetricLabel\"] { color: #000 !important; }
"""

SMALL_CARD_STYLE = """
{
  background-color: #ffffff;
  padding: 1rem;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  border: 1px solid rgba(0,0,0,0.06);
}
h3, p, li, label, span { color: #000; }
div[data-testid=\"stMetricValue\"], div[data-testid=\"stMetricLabel\"] { color: #000 !important; }
"""

WHITE_BUTTON_STYLE = """
button {
  background-color: #ffffff !important;
  border-color: #6f6f6fff !important;
  color: #000000 !important;
}
"""

YELLOW_BUTTON_STYLE = """
button {
  background-color: #ffd400 !important;
  border-color: #ffd400 !important;
  color: #000 !important;
}
button:hover, button:focus { filter: brightness(1.03); }
"""

DELETE_SESSION_BUTTON_STYLE = """
button {
  background-color: #ffffff !important;
  border-color: #6f6f6fff !important;
  color: #8B0000 !important; /* dark red */
}
button:hover, button:focus { filter: brightness(1.03); }
"""

INPUT_STYLE = """
input {
  background-color: #ffffff !important;
  border-color: #6f6f6fff !important;
  color: #000000 !important;
  box-shadow: 0 6px 18px rgba(0,0,0,0.08);
  border: 1px solid rgba(0,0,0,0.06);
}
"""

SELECT_STYLE = """
select, option { color: #000; }
"""

CHECKBOX_STYLE = """
label span {
  color: #000;
}
"""

DISCLAIMER_STYLE = """
p {
  color: #555;
  font-size: 0.8rem;
}
"""

HSTACK_LEFT = """
{
  display: flex;
  gap: 6px;
  justify-content: flex-start;
  align-items: center;
}
"""

HSTACK_RIGHT = """
{
  display: flex;
  gap: 6px;
  justify-content: flex-end;
  align-items: center;
}
"""
