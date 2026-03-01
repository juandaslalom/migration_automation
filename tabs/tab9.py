import streamlit as st


def render_tab9() -> None:
    st.subheader("Portal Guardbands Migration – CLI Import")

    site_name = st.session_state.get("site_name", "")
    site_display = site_name if site_name else "<Site>"

    st.info("ℹ️ No action is required from this tool for this step.")

    st.markdown(
        f"""
        ### Instructions

        On the **upper server**, navigate to the Guardbands folder for each equipment and run the `.bat` file:

        ```
        E:\\Applied Materials\\SmartFactoryRx_{site_display}\\Guardbands\\<Equipment>
        ```

        Run the `.bat` file found inside each equipment folder.

        > **Note:** The script may take several minutes to complete.
        """
    )
