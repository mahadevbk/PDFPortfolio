import streamlit as st
import fitz  # PyMuPDF
import os
import img2pdf
from PIL import Image
import io
from streamlit_pdf_viewer import pdf_viewer

st.set_page_config(layout="wide", page_title="Universal Digital Portfolio")

# --- DARK THEME UI ---
st.markdown("""
    <style>
    .stApp { background-color: #001e5c; color: white; }
    .stImage { border: 2px solid #4a90e2; border-radius: 10px; background: #022e85; padding: 5px; }
    .stButton>button { background-color: #022e85; color: white; border: 1px solid #4a90e2; width: 100%; }
    .stDownloadButton button { background-color: #00ff00 !important; color: black !important; font-weight: bold; width: 100%; border: none; height: 3rem; }
    .file-info { font-size: 0.8rem; color: #4a90e2; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State
if 'binder_items' not in st.session_state:
    st.session_state.binder_items = []

# --- UTILITIES ---
def get_pdf_preview(pdf_bytes):
    """Generates a thumbnail for the first page of a PDF."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(0.3, 0.3))
        return pix.tobytes()
    except:
        return None

def process_upload(uploaded_file):
    """Determines if a file should be a PAGE or an ATTACHMENT."""
    fname = uploaded_file.name
    ext = fname.split('.')[-1].lower()
    file_bytes = uploaded_file.getvalue()
    
    if ext == 'pdf':
        return {'name': fname, 'bytes': file_bytes, 'mode': 'page', 'type': 'PDF'}
    
    elif ext in ['jpg', 'jpeg', 'png']:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode == 'RGBA': img = img.convert('RGB')
        pdf_b = img2pdf.convert(file_bytes)
        return {'name': fname, 'bytes': pdf_b, 'mode': 'page', 'type': 'IMAGE'}
    
    elif ext in ['txt', 'md']:
        doc = fitz.open()
        page = doc.new_page()
        text = file_bytes.decode("utf-8", errors="ignore")
        page.insert_text((50, 50), text, fontsize=11)
        return {'name': fname, 'bytes': doc.tobytes(), 'mode': 'page', 'type': 'TEXT'}
    
    else:
        return {'name': fname, 'bytes': file_bytes, 'mode': 'attachment', 'type': ext.upper()}

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛒 Add to Portfolio")
    uploaded_files = st.file_uploader("Upload ANY file type", accept_multiple_files=True)
    
    if st.button("Add to Binder") and uploaded_files:
        for f in uploaded_files:
            item = process_upload(f)
            st.session_state.binder_items.append(item)
        st.rerun()

    st.divider()
    st.subheader("Settings")
    add_toc = st.checkbox("Include Table of Contents", value=True)

    if st.button("🗑️ Clear All"):
        st.session_state.binder_items = []
        st.rerun()

# --- MAIN CONTENT ---
st.title("📂 PDF Binder & Portfolio Creator")

st.markdown("""
### **How to build your Binder:**
1.  **Visual Pages:** Upload PDFs/Images to merge into the main document.
2.  **Native Attachments:** Upload CAD, ZIP, or Excel files to embed them *inside* the PDF.
3.  **Sequence:** Arrange your pages using the arrows.
---
""", unsafe_allow_html=True)

if st.session_state.binder_items:
    pages = [i for i in st.session_state.binder_items if i['mode'] == 'page']
    attachments = [i for i in st.session_state.binder_items if i['mode'] == 'attachment']

    # --- SECTION: BINDER PAGES ---
    st.subheader(f"📄 Visual Pages ({len(pages)})")
    if pages:
        cols = st.columns(4)
        for idx, item in enumerate(st.session_state.binder_items):
            if item['mode'] == 'page':
                with cols[idx % 4]:
                    thumb = get_pdf_preview(item['bytes'])
                    if thumb: st.image(thumb, use_container_width=True)
                    st.caption(f"{idx+1}. {item['name']}")
                    
                    c1, c2, c3 = st.columns(3)
                    if c1.button("⬅️", key=f"L_{idx}") and idx > 0:
                        st.session_state.binder_items[idx], st.session_state.binder_items[idx-1] = st.session_state.binder_items[idx-1], st.session_state.binder_items[idx]
                        st.rerun()
                    if c2.button("❌", key=f"X_{idx}"):
                        st.session_state.binder_items.pop(idx)
                        st.rerun()
                    if c3.button("➡️", key=f"R_{idx}") and idx < len(st.session_state.binder_items)-1:
                        st.session_state.binder_items[idx], st.session_state.binder_items[idx+1] = st.session_state.binder_items[idx+1], st.session_state.binder_items[idx]
                        st.rerun()

    # --- SECTION: NATIVE ATTACHMENTS ---
    if attachments:
        st.divider()
        st.subheader(f"📎 Native Attachments ({len(attachments)})")
        for idx, att in enumerate(st.session_state.binder_items):
            if att['mode'] == 'attachment':
                col_a, col_b = st.columns([0.8, 0.2])
                col_a.write(f"📦 **{att['name']}** (Type: {att['type']})")
                if col_b.button("Remove", key=f"del_att_{idx}"):
                    st.session_state.binder_items.pop(idx)
                    st.rerun()

    # --- FINAL EXPORT ---
    st.divider()
    portfolio_name = st.text_input("Final Portfolio Filename", "Project_Portfolio.pdf")
    
    if st.button("🏗️ CONSTRUCT & DOWNLOAD PORTFOLIO"):
        with st.spinner("Building Portfolio..."):
            final_pdf = fitz.open()
            
            # 1. OPTIONAL: Create TOC Page
            if add_toc:
                toc_page = final_pdf.new_page()
                toc_page.insert_text((50, 50), "Portfolio Table of Contents", fontsize=20, color=(0, 0, 0.5))
                y_pos = 100
                
                toc_page.insert_text((50, y_pos), "Visual Document Pages:", fontsize=14, color=(0, 0, 0))
                y_pos += 25
                for i, item in enumerate(pages):
                    toc_page.insert_text((70, y_pos), f"{i+1}. {item['name']}", fontsize=11)
                    y_pos += 15
                
                if attachments:
                    y_pos += 20
                    toc_page.insert_text((50, y_pos), "Embedded Native Attachments:", fontsize=14, color=(0, 0, 0))
                    y_pos += 25
                    for item in attachments:
                        toc_page.insert_text((70, y_pos), f"• {item['name']} ({item['type']})", fontsize=11)
                        y_pos += 15

            # 2. Merge all 'page' mode items
            for item in st.session_state.binder_items:
                if item['mode'] == 'page':
                    item_doc = fitz.open(stream=item['bytes'], filetype="pdf")
                    final_pdf.insert_pdf(item_doc)
            
            # Safety check for empty PDFs
            if final_pdf.page_count == 0:
                final_pdf.new_page().insert_text((50, 50), "Empty Portfolio")

            # 3. Embed all 'attachment' mode items using the updated method
            for item in st.session_state.binder_items:
                if item['mode'] == 'attachment':
                    final_pdf.embfile_add(
                        item['name'], 
                        item['bytes'],
                        filename=item['name'],
                        desc=f"Native {item['type']} file"
                    )
            
            output = io.BytesIO()
            final_pdf.save(output)
            
            st.download_button(
                label="🚀 DOWNLOAD COMPLETE BINDER",
                data=output.getvalue(),
                file_name=portfolio_name,
                mime="application/pdf"
            )
else:
    st.info("Your binder is empty. Upload files in the sidebar to begin.")

st.markdown("""
<div style='background-color: #0d5384; padding: 1rem; border-left: 5px solid #fff500; border-radius: 0.5rem; color: white;'>
Built with ❤️ using Streamlit.
</div>
""", unsafe_allow_html=True)
