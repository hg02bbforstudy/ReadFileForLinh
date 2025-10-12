import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
import json
import base64

# Import the CV processor
from cv_processor_api import CVProcessor

# Streamlit page config
st.set_page_config(
    page_title="🐍 CV Reader - Streamlit Edition",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    
    .confidence-high { color: #28a745; font-weight: bold; }
    .confidence-medium { color: #ffc107; font-weight: bold; }
    .confidence-low { color: #dc3545; font-weight: bold; }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialize processor
@st.cache_resource
def get_cv_processor():
    return CVProcessor()

cv_processor = get_cv_processor()

# Header
st.markdown("""
<div class="main-header">
    <h1>🐍 CV Reader - Streamlit Edition</h1>
    <p>Trích xuất thông tin CV với Python & AI - Giao diện thân thiện</p>
    <small>✨ DOCX Advanced • PDF Deep Analysis • OCR Support • Vietnamese NLP</small>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Cấu hình")
    
    # Processing options
    st.subheader("📊 Tùy chọn xử lý")
    use_nlp = st.checkbox("🤖 Sử dụng NLP", value=True, help="Tăng độ chính xác cho tên, công ty")
    use_advanced_extraction = st.checkbox("🔍 Trích xuất nâng cao", value=True)
    confidence_threshold = st.slider("🎯 Ngưỡng tin cậy", 0.0, 1.0, 0.5, 0.1)
    
    st.divider()
    
    # Export options
    st.subheader("📥 Xuất dữ liệu")
    export_format = st.selectbox("Format", ["CSV", "JSON", "Excel"])
    
    st.divider()
    
    # Statistics
    st.subheader("📈 Thống kê")
    if 'processed_count' not in st.session_state:
        st.session_state.processed_count = 0
    
    st.metric("CV đã xử lý", st.session_state.processed_count)
    
    # Clear data
    if st.button("🗑️ Xóa dữ liệu", type="secondary"):
        for key in ['cv_data', 'results_history']:
            if key in st.session_state:
                del st.session_state[key]
        st.success("Đã xóa dữ liệu!")

# Main content
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📄 Upload CV")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Chọn file CV",
        type=['pdf', 'docx'],
        help="Hỗ trợ file PDF và DOCX, tối đa 10MB"
    )
    
    # Camera capture (placeholder)
    if st.button("📷 Chụp ảnh CV", type="secondary"):
        st.info("Tính năng chụp ảnh sẽ được hỗ trợ trong phiên bản web app đầy đủ")
    
    # Process button
    if uploaded_file is not None:
        if st.button("🚀 Xử lý CV", type="primary"):
            with st.spinner("Đang xử lý CV với Python AI..."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    # Extract text
                    if uploaded_file.name.lower().endswith('.docx'):
                        text, extraction_confidence = cv_processor.extract_text_from_docx(tmp_file_path)
                    elif uploaded_file.name.lower().endswith('.pdf'):
                        text, extraction_confidence = cv_processor.extract_text_from_pdf(tmp_file_path)
                    
                    # Extract fields
                    fields, confidence = cv_processor.extract_fields(text)
                    
                    # Adjust confidence
                    for key in confidence:
                        confidence[key] *= extraction_confidence
                    
                    # Store results
                    st.session_state.cv_data = {
                        'fields': fields,
                        'confidence': confidence,
                        'raw_content': text,
                        'filename': uploaded_file.name,
                        'processing_time': datetime.now().isoformat(),
                        'extraction_confidence': extraction_confidence
                    }
                    
                    st.session_state.processed_count += 1
                    
                    # Clean up
                    os.unlink(tmp_file_path)
                    
                    st.success(f"✅ Xử lý thành công! Độ tin cậy: {extraction_confidence:.1%}")
                    
                except Exception as e:
                    st.error(f"❌ Lỗi xử lý: {str(e)}")

with col2:
    st.header("📊 Kết quả trích xuất")
    
    if 'cv_data' in st.session_state:
        cv_data = st.session_state.cv_data
        
        # Overview metrics
        st.subheader("📈 Tổng quan")
        col_metrics = st.columns(4)
        
        avg_confidence = sum(cv_data['confidence'].values()) / len(cv_data['confidence'])
        high_conf_fields = sum(1 for c in cv_data['confidence'].values() if c > 0.7)
        total_fields = len(cv_data['confidence'])
        
        with col_metrics[0]:
            st.metric("Độ tin cậy TB", f"{avg_confidence:.1%}")
        with col_metrics[1]:
            st.metric("Trường tin cậy cao", f"{high_conf_fields}/{total_fields}")
        with col_metrics[2]:
            st.metric("Độ tin cậy trích xuất", f"{cv_data['extraction_confidence']:.1%}")
        with col_metrics[3]:
            st.metric("Thời gian xử lý", "< 2s")
        
        st.divider()
        
        # Detailed results
        st.subheader("📋 Chi tiết kết quả")
        
        field_labels = {
            'name': '👤 Họ tên',
            'email': '📧 Email',
            'phone': '📞 Số điện thoại',
            'dob': '🎂 Ngày sinh',
            'gender': '⚥ Giới tính',
            'education': '🎓 Học vấn',
            'school': '🏫 Trường học',
            'major': '📚 Chuyên ngành',
            'currentPosition': '💼 Vị trí hiện tại',
            'experience': '⚡ Kinh nghiệm',
            'appliedPosition': '🎯 Vị trí ứng tuyển'
        }
        
        # Editable form
        with st.form("edit_cv_data"):
            edited_fields = {}
            
            for field, value in cv_data['fields'].items():
                if field in field_labels:
                    conf = cv_data['confidence'][field]
                    
                    # Confidence indicator
                    if conf > 0.7:
                        conf_class = "confidence-high"
                        conf_icon = "🟢"
                    elif conf > 0.4:
                        conf_class = "confidence-medium"
                        conf_icon = "🟡"
                    else:
                        conf_class = "confidence-low"
                        conf_icon = "🔴"
                    
                    col_field, col_conf = st.columns([3, 1])
                    
                    with col_field:
                        edited_fields[field] = st.text_input(
                            field_labels[field],
                            value=value or '',
                            key=f"field_{field}"
                        )
                    
                    with col_conf:
                        st.markdown(f"""
                        <div class="metric-card">
                            {conf_icon} <span class="{conf_class}">{conf:.1%}</span>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Update button
            if st.form_submit_button("💾 Cập nhật", type="primary"):
                st.session_state.cv_data['fields'].update(edited_fields)
                st.success("✅ Đã cập nhật dữ liệu!")
                st.rerun()
        
        st.divider()
        
        # Export section
        st.subheader("📥 Xuất dữ liệu")
        
        export_cols = st.columns(3)
        
        with export_cols[0]:
            if st.button("📊 Xuất CSV"):
                df = pd.DataFrame([cv_data['fields']])
                csv = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Tải CSV",
                    data=csv,
                    file_name=f"cv_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with export_cols[1]:
            if st.button("📄 Xuất JSON"):
                json_data = json.dumps(cv_data, ensure_ascii=False, indent=2)
                st.download_button(
                    label="⬇️ Tải JSON",
                    data=json_data,
                    file_name=f"cv_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with export_cols[2]:
            if st.button("📈 Xuất Excel"):
                df = pd.DataFrame([cv_data['fields']])
                # Convert to Excel
                excel_buffer = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
                df.to_excel(excel_buffer.name, index=False, engine='openpyxl')
                
                with open(excel_buffer.name, 'rb') as f:
                    st.download_button(
                        label="⬇️ Tải Excel",
                        data=f.read(),
                        file_name=f"cv_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                os.unlink(excel_buffer.name)
        
        # Raw content (collapsible)
        with st.expander("📝 Nội dung gốc"):
            st.text_area(
                "Raw text",
                value=cv_data['raw_content'][:2000] + ('...' if len(cv_data['raw_content']) > 2000 else ''),
                height=200,
                disabled=True
            )
    
    else:
        st.info("👆 Vui lòng upload và xử lý file CV để xem kết quả")
        
        # Sample data visualization
        st.subheader("📊 Demo với dữ liệu mẫu")
        
        sample_data = {
            'Trường': ['Họ tên', 'Email', 'Số ĐT', 'Học vấn', 'Kinh nghiệm'],
            'Độ tin cậy': [0.95, 0.88, 0.92, 0.76, 0.83],
            'Trạng thái': ['🟢 Cao', '🟢 Cao', '🟢 Cao', '🟡 Trung bình', '🟢 Cao']
        }
        
        df_sample = pd.DataFrame(sample_data)
        st.dataframe(df_sample, use_container_width=True)
        
        # Confidence chart
        st.bar_chart(df_sample.set_index('Trường')['Độ tin cậy'])

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🐍 <strong>CV Reader - Python Edition</strong></p>
    <p>Powered by Streamlit • Python • NLP • OCR</p>
    <p><small>© 2025 - Phiên bản nâng cao với độ chính xác cao</small></p>
</div>
""", unsafe_allow_html=True)