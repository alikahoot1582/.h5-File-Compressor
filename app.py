import streamlit as st
import h5py
import os
import tempfile

# Force a check to see if your config.toml is actually working
max_size = st.get_option("server.maxUploadSize")

st.set_page_config(page_title="H5 Compressor", page_icon="📦")
st.title("📦 H5 High-Compression Tool")

st.sidebar.write(f"**Server Limit:** {max_size} MB")
if max_size < 700:
    st.sidebar.warning("Warning: Config not detected. Using default 200MB limit.")

uploaded_file = st.file_uploader("Upload .h5 file (Max 799MB)", type=["h5", "hdf5"])

if uploaded_file is not None:
    st.success(f"File uploaded: {uploaded_file.name}")
    
    if st.button("Compress File"):
        try:
            with st.spinner("Processing... this may take a minute for large files."):
                # 1. Use a temporary file to store the upload to save RAM
                with tempfile.NamedTemporaryFile(delete=False, suffix=".h5") as tmp_in:
                    tmp_in.write(uploaded_file.getbuffer())
                    tmp_in_path = tmp_in.name

                tmp_out_path = tempfile.mktemp(suffix=".h5")

                # 2. Open both files and copy with compression
                with h5py.File(tmp_in_path, 'r') as f_in:
                    with h5py.File(tmp_out_path, 'w') as f_out:
                        for key in f_in.keys():
                            # Only compress datasets (not groups)
                            if isinstance(f_in[key], h5py.Dataset):
                                data = f_in[key][:]
                                f_out.create_dataset(
                                    key, 
                                    data=data, 
                                    compression="gzip", 
                                    compression_opts=9
                                )
                            # Copy attributes
                            for attr_name, attr_value in f_in[key].attrs.items():
                                f_out[key].attrs[attr_name] = attr_value

                # 3. Provide download link
                with open(tmp_out_path, "rb") as f:
                    btn = st.download_button(
                        label="Download Compressed File",
                        data=f,
                        file_name=f"compressed_{uploaded_file.name}",
                        mime="application/x-hdf5"
                    )

                # 4. Cleanup temp files
                os.remove(tmp_in_path)
                os.remove(tmp_out_path)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.info("Tip: Check if your H5 file is corrupted or uses unsupported data types.")
