import pandas as pd
import os
import streamlit as st


import streamlit as st
import pandas as pd

def streamlit_dataset_upload(default_data_path):
    if "data_loaded" not in st.session_state:  # Check if data has been loaded
        st.session_state.data_loaded = False  # Initialize the flag

    if not st.session_state.data_loaded:
        try:
            # Attempt to load data from the default path
            if default_data_path.endswith(".csv"):
                df = pd.read_csv(default_data_path)
                df.columns = pd.MultiIndex.from_tuples([tuple(c.split(".")) for c in df.columns])
            elif default_data_path.endswith(".h5"):
                df = pd.read_hdf(default_data_path)
            else:
                raise ValueError("Unsupported file format.")
            st.session_state["data"] = df  # Save data to session state
            st.session_state.data_loaded = True  # Set the flag to True
        except Exception as e:
            st.error(f"Failed to load data from default path: {e}")
            st.markdown("### Data Upload")
            st.markdown(
                "Please upload the ```.csv``` file containing all of the transactions you want to analyze."
            )
            fl = st.file_uploader("Upload a file", type=["csv", "xlsx", "html", "h5"])
            if fl is not None:
                st.write(fl.name)
                if fl.name.endswith(".csv"):
                    df = pd.read_csv(fl)
                    df.columns = pd.MultiIndex.from_tuples([tuple(c.split(".")) for c in df.columns])
                elif fl.name.endswith(".h5"):
                    df = pd.read_hdf(fl)
                else:
                    st.error("Unsupported file format.")
                    return None
                st.session_state["data"] = df  # Save data to session state
                st.session_state.data_loaded = True  # Set the flag to True
            else:
                st.warning("Please upload a file to proceed.")
                return None
    else:
        df = st.session_state["data"]

    return df
