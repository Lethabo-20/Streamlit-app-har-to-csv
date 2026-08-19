import streamlit as st
import json
import pandas as pd

st.set_page_config(
    page_title="HAR to CSV Converter",
    page_icon="📊",
    layout="wide"
)
# Title
st.title("📊 HAR to CSV Converter")

st.write(
    "Upload a HAR (HTTP Archive) file and convert its request data into a CSV file."
)


# File uploader
uploaded_file = st.file_uploader(
    "Upload your HAR file",
    type=None
)


if uploaded_file is not None:

    st.success(f"File uploaded: {uploaded_file.name}")

    try:
        # Read HAR file
        har_data = json.load(uploaded_file)

        # Get HAR entries
        entries = har_data["log"]["entries"]

        st.info(f"Found {len(entries)} requests in the HAR file.")

        # Extract useful information
        records = []

        for entry in entries:

            request = entry.get("request", {})
            response = entry.get("response", {})
            content = response.get("content", {})

            record = {
                "Timestamp": entry.get("startedDateTime"),
                "Method": request.get("method"),
                "URL": request.get("url"),
                "HTTP Version": request.get("httpVersion"),
                "Status": response.get("status"),
                "Status Text": response.get("statusText"),
                "Response MIME Type": content.get("mimeType"),
                "Response Size": content.get("size"),
                "Time (ms)": entry.get("time")
            }

            records.append(record)

        # Convert to DataFrame
        df = pd.DataFrame(records)

        # Display preview
        st.subheader("Data Preview")

        st.dataframe(
            df,
            use_container_width=True
        )

        # Convert DataFrame to CSV
        csv_data = df.to_csv(index=False).encode("utf-8")

        # Download button
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name="har_data.csv",
            mime="text/csv"
        )

    except Exception as e:

        st.error(
            "Unable to process this HAR file."
        )

        st.exception(e)

