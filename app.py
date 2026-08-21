import streamlit as st
import json
import pandas as pd


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="HAR to CSV Converter",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# FUNCTIONS
# ============================================================

def flatten_dict(data, parent_key="", separator="."):
    """
    Recursively flatten a nested dictionary.

    Example:

    {
        "request": {
            "method": "GET",
            "url": "https://example.com"
        }
    }

    becomes:

    {
        "request.method": "GET",
        "request.url": "https://example.com"
    }
    """

    flattened = {}

    if not isinstance(data, dict):
        return {parent_key: data}

    for key, value in data.items():

        new_key = (
            f"{parent_key}{separator}{key}"
            if parent_key
            else str(key)
        )

        if isinstance(value, dict):

            nested = flatten_dict(
                value,
                new_key,
                separator
            )

            flattened.update(nested)

        elif isinstance(value, list):

            # Lists cannot directly exist inside CSV cells.
            # Preserve them as JSON strings.
            flattened[new_key] = json.dumps(
                value,
                ensure_ascii=False
            )

        else:

            flattened[new_key] = value

    return flattened


def validate_har(data):
    """
    Check whether the uploaded JSON appears to be a valid HAR file.
    """

    if not isinstance(data, dict):
        return False

    if "log" not in data:
        return False

    if not isinstance(data["log"], dict):
        return False

    if "entries" not in data["log"]:
        return False

    if not isinstance(data["log"]["entries"], list):
        return False

    return True


def process_har(har_data):
    """
    Convert all HAR entries into a flattened DataFrame.
    """

    entries = har_data["log"]["entries"]

    records = []

    for index, entry in enumerate(entries):

        flattened_entry = flatten_dict(entry)

        # Keep track of original HAR entry number
        flattened_entry["har_entry_number"] = index + 1

        records.append(flattened_entry)

    df = pd.DataFrame(records)

    # Put entry number first
    if "har_entry_number" in df.columns:

        columns = [
            "har_entry_number"
        ] + [
            column
            for column in df.columns
            if column != "har_entry_number"
        ]

        df = df[columns]

    return df


# ============================================================
# APPLICATION
# ============================================================

st.title("📊 HAR to CSV Converter")

st.write(
    """
Upload a HAR (HTTP Archive) file and convert its contents
into a CSV dataset while preserving as much of the original
HAR information as possible.
"""
)


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Upload your HAR file",
    type=None,
    help=(
        "Upload a HAR file exported from Chrome, Firefox, "
        "Edge, Safari, or another HAR-compatible tool."
    )
)


# ============================================================
# PROCESS FILE
# ============================================================

if uploaded_file is not None:

    st.success(
        f"File uploaded: {uploaded_file.name}"
    )

    try:

        # ----------------------------------------------------
        # READ FILE
        # ----------------------------------------------------

        file_bytes = uploaded_file.getvalue()

        try:

            har_data = json.loads(
                file_bytes.decode("utf-8")
            )

        except UnicodeDecodeError:

            st.error(
                "The uploaded file could not be decoded as UTF-8."
            )

            st.stop()

        except json.JSONDecodeError:

            st.error(
                "The uploaded file is not valid JSON. "
                "A HAR file must contain JSON data."
            )

            st.stop()


        # ----------------------------------------------------
        # VALIDATE HAR
        # ----------------------------------------------------

        if not validate_har(har_data):

            st.error(
                """
                The uploaded file does not appear to be a valid
                HAR file.

                A valid HAR file should contain:

                log → entries
                """
            )

            st.stop()


        # ----------------------------------------------------
        # HAR INFORMATION
        # ----------------------------------------------------

        log_data = har_data["log"]

        entries = log_data["entries"]

        creator = log_data.get(
            "creator",
            {}
        )

        version = log_data.get(
            "version",
            "Unknown"
        )


        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        st.subheader("HAR File Information")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Requests",
                len(entries)
            )

        with col2:

            st.metric(
                "HAR Version",
                version
            )

        with col3:

            creator_name = creator.get(
                "name",
                "Unknown"
            )

            st.metric(
                "Creator",
                creator_name
            )

        with col4:

            file_size_mb = (
                len(file_bytes)
                / (1024 * 1024)
            )

            st.metric(
                "File Size",
                f"{file_size_mb:.2f} MB"
            )


        # ----------------------------------------------------
        # CONVERT HAR ENTRIES
        # ----------------------------------------------------

        with st.spinner(
            "Processing HAR data..."
        ):

            df = process_har(
                har_data
            )


        # ----------------------------------------------------
        # DATASET INFORMATION
        # ----------------------------------------------------

        st.subheader(
            "Extracted Dataset"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Rows",
                len(df)
            )

        with col2:

            st.metric(
                "Columns",
                len(df.columns)
            )

        with col3:

            st.metric(
                "Memory Usage",
                f"{df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB"
            )


        # ----------------------------------------------------
        # DATA PREVIEW
        # ----------------------------------------------------

        st.subheader(
            "Data Preview"
        )

        st.dataframe(
            df,
            use_container_width=True,
            height=500
        )


        # ----------------------------------------------------
        # COLUMN INFORMATION
        # ----------------------------------------------------

        with st.expander(
            "View extracted columns"
        ):

            column_data = pd.DataFrame({
                "Column": df.columns,
                "Data Type": [
                    str(df[column].dtype)
                    for column in df.columns
                ],
                "Non-Null Values": [
                    df[column].notna().sum()
                    for column in df.columns
                ]
            })

            st.dataframe(
                column_data,
                use_container_width=True
            )


        # ----------------------------------------------------
        # CSV EXPORT
        # ----------------------------------------------------

        st.subheader(
            "Export"
        )

        csv_data = df.to_csv(
            index=False
        ).encode("utf-8")


        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name="har_data.csv",
            mime="text/csv",
            use_container_width=True
        )


        # ----------------------------------------------------
        # ORIGINAL JSON EXPORT
        # ----------------------------------------------------

        st.download_button(
            label="⬇️ Download Complete HAR JSON",
            data=json.dumps(
                har_data,
                indent=2,
                ensure_ascii=False
            ).encode("utf-8"),
            file_name="har_data.json",
            mime="application/json",
            use_container_width=True
        )


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        st.error(
            "An unexpected error occurred while processing the HAR file."
        )

        with st.expander(
            "View technical error"
        ):

            st.exception(e)
