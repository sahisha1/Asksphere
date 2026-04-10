"""
Main Streamlit Application
This creates the web interface for our AI knowledge platform
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.rag_pipeline import RAGPipeline
from src.document_loader import DocumentLoader
from src.vector_store import VectorStore

# Page configuration
st.set_page_config(
    page_title="Company AI Knowledge Platform",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
    }
    .source-card {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag' not in st.session_state:
    st.session_state.rag = RAGPipeline()
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Sidebar for authentication and settings
with st.sidebar:
    st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=80)
    st.title("Company AI Knowledge")
    
    # Role selection
    st.subheader("👤 User Role")
    user_role = st.selectbox(
        "Select your role",
        options=["employee", "manager", "hr", "executive"],
        help="Different roles see different information"
    )
    
    st.divider()
    
    # Document upload
    st.subheader("📄 Add Documents")
    uploaded_file = st.file_uploader(
        "Upload PDF or TXT",
        type=['pdf', 'txt']
    )
    
    if uploaded_file:
        # Save uploaded file
        save_path = os.path.join("data", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Add sensitivity level
        sensitivity = st.slider("Document sensitivity", 1, 5, 2)
        
        if st.button("Index Document"):
            with st.spinner("Indexing..."):
                loader = DocumentLoader()
                docs = loader.load_all_documents()
                
                # Add to vector store
                for doc in docs:
                    doc.metadata['sensitivity'] = sensitivity
                    doc.metadata['role_access'] = user_role
                
                st.success(f"Added {len(docs)} document chunks!")
    
    st.divider()
    
    # Stats
    st.subheader("📊 Stats")
    st.metric("Role", user_role.upper())
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main chat interface
st.markdown('<h1 class="main-header">🧠 Company AI Knowledge Platform</h1>', unsafe_allow_html=True)
st.caption("Ask anything about company policies, documents, and knowledge")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources if it's an assistant message
        if message["role"] == "assistant" and "sources" in message:
            with st.expander("📚 View Sources"):
                for source in message["sources"]:
                    st.markdown(f"""
                    <div class="source-card">
                        <strong>📁 {source.get('source', 'Unknown')}</strong><br>
                        <small>Type: {source.get('file_type', 'N/A')}</small>
                    </div>
                    """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask a question..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Query the RAG pipeline
            result = st.session_state.rag.answer_question(
                question=prompt,
                user_role=user_role
            )
            
            if result['answer']:
                st.markdown(result['answer'])
                
                # Show confidence
                if result['confidence'] > 0:
                    st.caption(f"Confidence: {result['confidence']:.0%}")
                
                # Show sources
                if result['sources']:
                    with st.expander(f"📚 Sources ({len(result['sources'])})"):
                        for source in result['sources']:
                            st.markdown(f"""
                            <div class="source-card">
                                <strong>📁 {source.get('source', 'Unknown')}</strong><br>
                                <small>Role access: {source.get('allowed_roles', ['all'])}</small>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.error("Sorry, I couldn't find an answer.")
        
        # Save assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": result['answer'],
            "sources": result['sources']
        })

# Footer
st.divider()
st.caption("🔒 Role-based access enabled | 📚 Knowledge from company documents | 🧠 Powered by RAG")