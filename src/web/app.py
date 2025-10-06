"""
Main Streamlit Application for ContractGuard AI
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.agent.orchestrator import ContractGuardAgent
from src.utils.s3_helper import S3Helper
from src.utils.dynamodb_helper import DynamoDBHelper

logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="ContractGuard AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .risk-score-high {
        color: #d32f2f;
        font-size: 3rem;
        font-weight: bold;
    }
    .risk-score-medium {
        color: #f57c00;
        font-size: 3rem;
        font-weight: bold;
    }
    .risk-score-low {
        color: #388e3c;
        font-size: 3rem;
        font-weight: bold;
    }
    .stat-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = 'demo-user-123'  # For demo purposes
if 'current_contract_id' not in st.session_state:
    st.session_state.current_contract_id = None
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'

# Initialize helpers
@st.cache_resource
def get_helpers():
    return {
        'agent': ContractGuardAgent(),
        's3': S3Helper(),
        'db': DynamoDBHelper()
    }

helpers = get_helpers()


def main():
    """Main application entry point"""
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## ⚖️ ContractGuard AI")
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "📤 Upload Contract", "📋 My Contracts", "⚙️ Settings"],
            key="navigation"
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        ContractGuard AI is your autonomous legal partner for contract review and negotiation.
        
        **Features:**
        - 🔍 Autonomous risk analysis
        - 💡 AI-powered recommendations  
        - 📝 Multi-round negotiation planning
        - ✉️ Professional email drafting
        """)
        
        st.markdown("---")
        st.markdown("**⚠️ Legal Disclaimer**")
        st.markdown("""
        This is an assistive tool, not a replacement for licensed legal counsel. 
        Always consult a qualified attorney for legal advice.
        """)
    
    # Route to pages
    if "Dashboard" in page:
        show_dashboard()
    elif "Upload" in page:
        show_upload_page()
    elif "My Contracts" in page:
        show_contracts_list()
    elif "Settings" in page:
        show_settings()


def show_dashboard():
    """Dashboard page"""
    
    st.markdown('<div class="main-header">⚖️ ContractGuard AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your autonomous AI legal partner for contract review and negotiation</div>', unsafe_allow_html=True)
    
    # Get user contracts
    db = helpers['db']
    contracts = db.list_user_contracts(st.session_state.user_id)
    
    # Calculate stats
    total_contracts = len(contracts)
    high_risk = len([c for c in contracts if c.get('risk_analysis', {}).get('risk_level') == 'HIGH'])
    under_review = len([c for c in contracts if c.get('status') in ['ANALYZING', 'REVIEWED']])
    negotiating = len([c for c in contracts if c.get('status') == 'NEGOTIATING'])
    
    # Display stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{total_contracts}</div>
            <div class="stat-label">Total Contracts</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{high_risk}</div>
            <div class="stat-label">High Risk</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{under_review}</div>
            <div class="stat-label">Under Review</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{negotiating}</div>
            <div class="stat-label">Negotiating</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent contracts
    st.subheader("📋 Recent Contracts")
    
    if contracts:
        # Sort by most recent
        contracts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        for contract in contracts[:5]:  # Show top 5
            display_contract_card(contract)
    else:
        st.info("No contracts yet. Upload your first contract to get started!")
        if st.button("📤 Upload Contract", type="primary"):
            st.session_state.page = 'upload'
            st.rerun()
    
    # Quick actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Upload New Contract", use_container_width=True):
            st.session_state.page = 'upload'
            st.rerun()
    
    with col2:
        if st.button("📊 View All Contracts", use_container_width=True):
            st.session_state.page = 'contracts'
            st.rerun()
    
    with col3:
        if st.button("📚 Learn More", use_container_width=True):
            st.markdown("[Documentation](https://github.com/your-username/contractguard-ai)")


def display_contract_card(contract: dict):
    """Display a contract card"""
    
    contract_id = contract.get('contract_id', 'Unknown')
    title = contract.get('title', 'Untitled Contract')
    contract_type = contract.get('contract_type', 'Unknown')
    status = contract.get('status', 'Unknown')
    risk_analysis = contract.get('risk_analysis', {})
    risk_score = risk_analysis.get('overall_risk_score', 0)
    risk_level = risk_analysis.get('risk_level', 'UNKNOWN')
    
    # Color coding
    if risk_score >= 7:
        risk_color = "🔴"
        risk_class = "risk-score-high"
    elif risk_score >= 4:
        risk_color = "🟡"
        risk_class = "risk-score-medium"
    else:
        risk_color = "🟢"
        risk_class = "risk-score-low"
    
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        
        with col1:
            st.markdown(f"**{title}**")
            st.caption(f"{contract_type} • {contract_id[:8]}...")
        
        with col2:
            st.markdown(f"Status: `{status}`")
        
        with col3:
            if risk_score > 0:
                st.markdown(f"{risk_color} **{risk_score:.1f}**/10")
            else:
                st.markdown("⏳ Analyzing...")
        
        with col4:
            if st.button("View", key=f"view_{contract_id}"):
                show_contract_detail(contract_id)
        
        st.markdown("---")


def show_upload_page():
    """Contract upload page"""
    
    st.title("📤 Upload Contract")
    st.markdown("Upload a business contract for AI-powered risk analysis and negotiation support.")
    
    # Upload form
    with st.form("upload_form"):
        st.subheader("Contract Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            contract_title = st.text_input("Contract Title*", placeholder="e.g., Vendor Agreement with Acme Corp")
            contract_type = st.selectbox(
                "Contract Type*",
                ["MSA", "SaaS", "NDA", "Employment", "SOW", "Consulting", "Vendor", "Other"]
            )
        
        with col2:
            counterparty = st.text_input("Counterparty Name", placeholder="e.g., Acme Corporation")
            counterparty_email = st.text_input("Counterparty Email", placeholder="e.g., legal@acme.com")
        
        st.markdown("---")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Contract Document",
            type=['pdf', 'docx'],
            help="Supported formats: PDF, DOCX (max 25MB)"
        )
        
        st.markdown("---")
        
        st.subheader("Your Context (Optional)")
        st.markdown("Help the AI provide better recommendations by sharing context about your business.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            industry = st.selectbox(
                "Industry",
                ["Technology/SaaS", "Professional Services", "Manufacturing", "Retail", "Healthcare", "Finance", "Other"]
            )
            company_size = st.selectbox(
                "Company Size",
                ["1-10 employees", "11-50 employees", "51-100 employees", "101-500 employees", "500+ employees"]
            )
        
        with col2:
            risk_tolerance = st.select_slider(
                "Risk Tolerance",
                options=["Conservative", "Moderate", "Aggressive"],
                value="Moderate"
            )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Analyze Contract", type="primary", use_container_width=True)
        
        if submitted:
            if not contract_title or not uploaded_file:
                st.error("Please provide a contract title and upload a document.")
            else:
                process_upload(
                    uploaded_file,
                    contract_title,
                    contract_type,
                    counterparty,
                    counterparty_email,
                    industry,
                    company_size,
                    risk_tolerance
                )


def process_upload(file, title, contract_type, counterparty, counterparty_email, industry, company_size, risk_tolerance):
    """Process uploaded contract"""
    
    with st.spinner("Uploading and analyzing contract... This may take up to 2 minutes."):
        try:
            import uuid
            from datetime import datetime
            
            # Generate contract ID
            contract_id = f"contract-{uuid.uuid4()}"
            
            # Upload to S3
            s3 = helpers['s3']
            s3_key = f"uploads/{st.session_state.user_id}/{contract_id}/{file.name}"
            
            # Save file temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=file.name) as tmp_file:
                tmp_file.write(file.getvalue())
                tmp_path = tmp_file.name
            
            # Upload to S3
            s3_uri = s3.upload_file(tmp_path, s3_key)
            
            # Create contract record
            db = helpers['db']
            contract_data = {
                'contract_id': contract_id,
                'user_id': st.session_state.user_id,
                'title': title,
                'contract_type': contract_type,
                'counterparty': counterparty,
                'counterparty_email': counterparty_email,
                's3_bucket': s3.bucket_name,
                's3_key': s3_key,
                'status': 'UPLOADED',
                'user_context': {
                    'industry': industry,
                    'company_size': company_size,
                    'risk_tolerance': risk_tolerance
                }
            }
            
            db.create_contract(contract_data)
            
            # Trigger agent processing
            agent = helpers['agent']
            
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("📄 Parsing contract...")
            progress_bar.progress(25)
            
            status_text.text("🔍 Analyzing risk...")
            progress_bar.progress(50)
            
            # Process contract
            result = agent.process_contract(contract_id, st.session_state.user_id)
            
            status_text.text("💡 Generating recommendations...")
            progress_bar.progress(75)
            
            status_text.text("✅ Complete!")
            progress_bar.progress(100)
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            st.success(f"✅ Contract analyzed successfully!")
            
            # Show results preview
            st.markdown("---")
            st.subheader("Analysis Preview")
            
            risk_score = result.get('overall_risk_score', 0)
            risk_level = result.get('risk_level', 'UNKNOWN')
            
            col1, col2 = st.columns(2)
            
            with col1:
                if risk_score >= 7:
                    st.markdown(f'<div class="risk-score-high">🔴 {risk_score:.1f}/10</div>', unsafe_allow_html=True)
                elif risk_score >= 4:
                    st.markdown(f'<div class="risk-score-medium">🟡 {risk_score:.1f}/10</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="risk-score-low">🟢 {risk_score:.1f}/10</div>', unsafe_allow_html=True)
                
                st.caption(f"Risk Level: {risk_level}")
            
            with col2:
                high_risk_count = len(result.get('high_risk_clauses', []))
                st.metric("High-Risk Clauses", high_risk_count)
            
            st.markdown("---")
            
            if st.button("View Full Analysis", type="primary"):
                show_contract_detail(contract_id)
            
        except Exception as e:
            logger.error(f"Error processing upload: {str(e)}")
            st.error(f"Error processing contract: {str(e)}")


def show_contract_detail(contract_id: str):
    """Show detailed contract analysis"""
    
    db = helpers['db']
    contract = db.get_contract(contract_id)
    
    if not contract:
        st.error("Contract not found")
        return
    
    st.title(f"📄 {contract.get('title', 'Contract Analysis')}")
    
    # Metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Type", contract.get('contract_type', 'Unknown'))
    with col2:
        st.metric("Status", contract.get('status', 'Unknown'))
    with col3:
        st.metric("Counterparty", contract.get('counterparty', 'N/A'))
    
    st.markdown("---")
    
    # Risk Analysis
    risk_analysis = contract.get('risk_analysis', {})
    
    if risk_analysis:
        st.subheader("🎯 Risk Analysis")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            risk_score = risk_analysis.get('overall_risk_score', 0)
            risk_level = risk_analysis.get('risk_level', 'UNKNOWN')
            
            # Risk gauge
            if risk_score >= 7:
                st.markdown(f'<div class="risk-score-high">{risk_score:.1f}/10</div>', unsafe_allow_html=True)
            elif risk_score >= 4:
                st.markdown(f'<div class="risk-score-medium">{risk_score:.1f}/10</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="risk-score-low">{risk_score:.1f}/10</div>', unsafe_allow_html=True)
            
            st.caption(f"**Risk Level:** {risk_level}")
        
        with col2:
            st.markdown("**Summary:**")
            st.write(risk_analysis.get('summary', 'No summary available'))
        
        st.markdown("---")
        
        # High-risk clauses
        high_risk_clauses = risk_analysis.get('high_risk_clauses', [])
        
        if high_risk_clauses:
            st.subheader("⚠️ High-Risk Clauses")
            
            for i, clause in enumerate(high_risk_clauses, 1):
                with st.expander(f"🔴 {clause.get('clause_type', 'Clause')} (Risk: {clause.get('risk_score', 0)}/10)"):
                    st.markdown(f"**Concerns:**")
                    for concern in clause.get('concerns', []):
                        st.markdown(f"- {concern}")
                    
                    st.markdown(f"**Impact:** {clause.get('impact', 'N/A')}")
                    st.markdown(f"**Current Text:** _{clause.get('clause_text', 'N/A')}_")
                    
                    if st.button(f"Get Recommendation", key=f"rec_{i}"):
                        st.info("Recommendation feature coming soon!")
        
        # Medium-risk clauses
        medium_risk_clauses = risk_analysis.get('medium_risk_clauses', [])
        
        if medium_risk_clauses:
            with st.expander(f"🟡 Medium-Risk Clauses ({len(medium_risk_clauses)})"):
                for clause in medium_risk_clauses:
                    st.markdown(f"**{clause.get('clause_type')}** (Risk: {clause.get('risk_score')}/10)")
                    st.caption(f"{', '.join(clause.get('concerns', []))}")
                    st.markdown("---")
        
        # Actions
        st.markdown("---")
        st.subheader("🎯 Next Steps")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🤝 Start Negotiation", type="primary", use_container_width=True):
                st.info("Negotiation planning feature coming soon!")
        
        with col2:
            if st.button("📥 Download Report", use_container_width=True):
                st.info("Download feature coming soon!")
        
        with col3:
            if st.button("✅ Approve Contract", use_container_width=True):
                db.update_contract_status(contract_id, "APPROVED")
                st.success("Contract approved!")
                st.rerun()
    
    else:
        st.info("Analysis in progress... Please check back in a moment.")
        if st.button("Refresh"):
            st.rerun()


def show_contracts_list():
    """Show list of all user contracts"""
    
    st.title("📋 My Contracts")
    
    db = helpers['db']
    contracts = db.list_user_contracts(st.session_state.user_id)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All", "ANALYZING", "REVIEWED", "NEGOTIATING", "APPROVED", "REJECTED"]
        )
    
    with col2:
        filter_type = st.selectbox(
            "Filter by Type",
            ["All", "MSA", "SaaS", "NDA", "Employment", "SOW", "Other"]
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Most Recent", "Highest Risk", "Lowest Risk", "Title A-Z"]
        )
    
    # Apply filters
    filtered_contracts = contracts
    
    if filter_status != "All":
        filtered_contracts = [c for c in filtered_contracts if c.get('status') == filter_status]
    
    if filter_type != "All":
        filtered_contracts = [c for c in filtered_contracts if c.get('contract_type') == filter_type]
    
    # Apply sorting
    if sort_by == "Most Recent":
        filtered_contracts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    elif sort_by == "Highest Risk":
        filtered_contracts.sort(key=lambda x: x.get('risk_analysis', {}).get('overall_risk_score', 0), reverse=True)
    elif sort_by == "Lowest Risk":
        filtered_contracts.sort(key=lambda x: x.get('risk_analysis', {}).get('overall_risk_score', 0))
    elif sort_by == "Title A-Z":
        filtered_contracts.sort(key=lambda x: x.get('title', ''))
    
    st.markdown("---")
    
    # Display contracts
    if filtered_contracts:
        st.caption(f"Showing {len(filtered_contracts)} contract(s)")
        
        for contract in filtered_contracts:
            display_contract_card(contract)
    else:
        st.info("No contracts match your filters.")


def show_settings():
    """Settings page"""
    
    st.title("⚙️ Settings")
    
    st.subheader("User Profile")
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name", value="Demo User")
            email = st.text_input("Email", value="demo@contractguard.ai")
            company = st.text_input("Company", value="ContractGuard Demo")
        
        with col2:
            industry = st.selectbox(
                "Industry",
                ["Technology/SaaS", "Professional Services", "Manufacturing", "Retail", "Healthcare", "Finance", "Other"]
            )
            company_size = st.selectbox(
                "Company Size",
                ["1-10 employees", "11-50 employees", "51-100 employees", "101-500 employees", "500+ employees"]
            )
            risk_tolerance = st.select_slider(
                "Default Risk Tolerance",
                options=["Conservative", "Moderate", "Aggressive"],
                value="Moderate"
            )
        
        submitted = st.form_submit_button("Save Profile")
        
        if submitted:
            st.success("Profile updated successfully!")
    
    st.markdown("---")
    
    st.subheader("Preferences")
    
    email_notifications = st.checkbox("Email notifications for contract analysis completion", value=True)
    email_approvals = st.checkbox("Email notifications for approval requests", value=True)
    
    st.markdown("---")
    
    st.subheader("About ContractGuard AI")
    st.markdown("""
    **Version:** 1.0.0  
    **Built for:** AWS AI Agent Global Hackathon 2025  
    **GitHub:** [github.com/your-username/contractguard-ai](https://github.com/your-username/contractguard-ai)
    
    **Technologies:**
    - Amazon Bedrock (Claude 3.5 Sonnet)
    - Amazon Bedrock AgentCore
    - AWS Lambda, DynamoDB, S3, Textract
    - Streamlit
    """)


if __name__ == "__main__":
    main()