import streamlit as st
import h5py
import os
import tempfile
import time

# --- Page Config ---
st.set_page_config(page_title="H5 Turbo Compressor", page_icon="⚡", layout="wide")

def compress_h5_file(input_path, output_path):
    """
    Reads from input_path and writes a compressed version to output_path.
    Uses GZIP Level 9 for maximum space saving.
    """
    with h5py.File(input_path, 'r') as src, h5py.File(output_path, 'w') as dest:
        def copy_and_compress(name, obj):
            if isinstance(obj, h5py.Group):
                # Create the group in the destination
                dest.create_group(name)
            elif isinstance(obj, h5py.Dataset):
                # Create compressed dataset
                # We use obj[...] to read the data into memory temporarily per dataset
                dest.create_dataset(
                    name, 
                    data=obj[...], 
                    compression="gzip", 
                    compression_opts=9,
                    chunks=True # Enabling chunking helps with compression efficiency
                )
            
            # Copy all metadata/attributes for this specific object
            for attr_name, attr_value in obj.attrs.items():
                dest[name].attrs[attr_name] = attr_value

        # Recursively walk through the H5 tree
        src.visititems(copy_and_compress)

# --- UI Layout ---
st.title("⚡ Professional H5 Compressor")
st.info("Limit set to 799 MB. Large files are processed via disk to save RAM.")

uploaded_file = st.file_uploader("Upload your .h5 or .hdf5 file", type=["h5", "hdf5"])

if uploaded_file is not None:
    # 1. Display Stats
    orig_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    col1, col2 = st.columns(2)
    col1.metric("Original Size", f"{orig_size_mb:.2f} MB")

    if st.button("Start High-Compression (GZIP 9)"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 2. Setup Temporary Files
        # We save the upload to disk so h5py can read it without hitting RAM limits
        with tempfile.NamedTemporaryFile(delete=False, suffix=".h5") as tmp_in:
            tmp_in.write(uploaded_file.getbuffer())
            tmp_in_path = tmp_in.name
        
        tmp_out_path = tmp_in_path.replace(".h5", "_out.h5")

        try:
            status_text.text("Compressing datasets... Please wait.")
            progress_bar.progress(40)
            
            start_time = time.time()
            compress_h5_file(tmp_in_path, tmp_out_path)
            duration = time.time() - start_time
            
            progress_bar.progress(100)
            status_text.text(f"Done in {duration:.2f} seconds!")

            # 3. Final Stats and Download
            with open(tmp_out_path, "rb") as f:
                compressed_bytes = f.read()
            
            new_size_mb = len(compressed_bytes) / (1024 * 1024)
            reduction = ((orig_size_mb - new_size_mb) / orig_size_mb) * 100
            
            col2.metric("Compressed Size", f"{new_size_mb:.2f} MB", delta=f"-{reduction:.1f}%")

            st.download_button(
                label="📥 Download Compressed H5",
                data=compressed_bytes,
                file_name=f"compressed_{uploaded_file.name}",
                mime="application/x-hdf5",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Error during compression: {e}")
        
        finally:
            # 4. Clean up the server's hard drive
            if os.path.exists(tmp_in_path): os.remove(tmp_in_path)
            if os.path.exists(tmp_out_path): os.remove(tmp_out_path)
