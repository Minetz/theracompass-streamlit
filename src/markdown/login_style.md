<style>
.stApp {
    background-color: #fff9db;
    color: #000000;
    /*color: #fcec73ff;*/
}

/* Make expander headers yellow with dark text (open and closed) */
/* Newer Streamlit markup: details/summary */
div[data-testid="stExpander"] > details > summary {
    background-color: #ffd400 !important;
    color: #000 !important;
    border: 1px solid #ffd400 !important;
}
div[data-testid="stExpander"] > details[open] > summary {
    background-color: #ffd400 !important;
    color: #000 !important;
}
/* Older markup (button-based) fallback */
div[data-testid="stExpander"] > div[role="button"],
section[data-testid="stExpander"] .st-expanderHeader {
    background-color: #ffd400 !important;
    color: #000 !important;
    border: 1px solid #ffd400 !important;
}
/* Chevron icon color */
div[data-testid="stExpander"] summary svg,
div[data-testid="stExpander"] div[role="button"] svg {
    color: #000 !important;
    fill: #000 !important;
}

</style>
