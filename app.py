import streamlit as st
import h5py
import io

def compress_h5_recursive(uploaded_file):
    """
    Recursively copies and compresses an H5 file while maintaining structure.
    """
    output_buffer = io.BytesIO()
    
    # Read from the uploaded buffer
    with h5py.File(uploaded_file, 'r') as src:
        with h5py.File(output_buffer, 'w') as dest:
            
            def copy_and_compress(name, obj):
                if isinstance(obj, h5py.Group):
                    dest.create_group(name)
                elif isinstance(obj, h5py.Dataset):
                    # We apply GZIP level 9 compression to every dataset
                    dest.create_dataset(
                        name, 
                        data=obj[...], 
                        compression="gzip", 
                        compression_opts=9
                    )
                # Copy attributes (metadata) if they exist
                for attr_name, attr_value in obj.attrs.items():
                    dest[name].attrs[attr_name] = attr_value

            # Visit every item in the source file and apply the function
            src.visititems(copy_and_compress)
                
    return output_buffer.getvalue()

# --- UI Setup ---
st.set_page_config(page_title="Deep H5 Compressor", page_icon="📦")
st.title("📦 Recursive H5 Compressor")
st.markdown("This tool preserves all **groups, datasets, and metadata** while applying GZIP compression.")

uploaded_file = st.file_uploader("Upload .h5 file", type=["h5", "hdf5"])

if uploaded_file:
    original_bytes = uploaded_file.getvalue()
    st.info(f"Original Size: {len(original_bytes) / 1024:.2f} KB")

    if st.button("Run Compression"):
        try:
            with st.spinner("Processing hierarchy..."):
                compressed_h5 = compress_h5_recursive(uploaded_file)
                
                new_size = len(compressed_h5) / 1024
                st.success(f"Compression Finished! New Size: {new_size:.2f} KB")
                
                st.download_button(
                    label="Download Compressed .h5 File",
                    data=compressed_h5,
                    file_name=f"compressed_{uploaded_file.name}",
                    mime="application/x-hdf5"
                )
        except Exception as e:
            st.error(f"Error processing file: {e}")
