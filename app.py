import os
import streamlit as st
from agent import analyze_contract

st.title("📝 Smart Contract Compliance Checker")
st.write("Upload a contract to check for **risks, compliance issues, and unfair terms**.")

uploaded_file = st.file_uploader("Upload your contract (PDF, DOCX, TXT, PNG, JPG)", type=["pdf", "docx", "txt", "png", "jpg"])

if uploaded_file is not None:
    file_path = f"temp_file.{uploaded_file.name.split('.')[-1]}"

    try:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success("File uploaded successfully! Analyzing...")

        result = analyze_contract(file_path)

        st.subheader("🔍 Contract Analysis Results")
        st.write(result)

    except Exception as e:
        st.error(f"An error occurred: {e}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)  # Clean up temporary file
