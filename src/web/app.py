import streamlit as st
import json
import requests
from streamlit.components.v1 import html

def create_cv_form():
    st.title("CV Generator")
    
    with st.form("cv_form"):
        # Contact Information
        st.header("Contact Information")
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name")
            phone = st.text_input("Phone Number")
        with col2:    
            email = st.text_input("Email")

        # Profile Section
        st.header("Profile")
        title = st.text_input("Job Title")
        summary = st.text_area("Professional Summary")
        
        # Highlights/Skills
        st.subheader("Highlights")
        highlights = st.text_area("Key Highlights (One per line)")
        highlights_list = [x.strip() for x in highlights.split('\n') if x.strip()]
        
        # Accomplishments
        st.subheader("Accomplishments")
        accomplishments = st.text_area("Accomplishments (One per line)")
        accomplishments_list = [x.strip() for x in accomplishments.split('\n') if x.strip()]

        # Experience
        st.header("Experience")
        num_experiences = st.number_input("Number of experiences", min_value=1, max_value=10, value=1)
        
        experiences = []
        for i in range(num_experiences):
            st.subheader(f"Experience {i+1}")
            col1, col2 = st.columns(2)
            with col1:
                job_title = st.text_input(f"Job Title #{i+1}")
                company = st.text_input(f"Company #{i+1}")
                start_date = st.text_input(f"Start Date #{i+1} (MMM YYYY)")
            with col2:
                city = st.text_input(f"City #{i+1}")
                state = st.text_input(f"State #{i+1}")
                end_date = st.text_input(f"End Date #{i+1} (MMM YYYY or Current)")
            description = st.text_area(f"Job Description #{i+1}")
            
            experiences.append({
                "title": job_title,
                "company": company,
                "city": city,
                "state": state,
                "start_date": start_date,
                "end_date": end_date,
                "description": description
            })

        # Education
        st.header("Education")
        num_education = st.number_input("Number of education entries", min_value=1, max_value=5, value=1)
        
        education = []
        for i in range(num_education):
            st.subheader(f"Education {i+1}")
            col1, col2 = st.columns(2)
            with col1:
                degree = st.text_input(f"Degree #{i+1}")
                institution = st.text_input(f"Institution #{i+1}")
                year = st.text_input(f"Year #{i+1}")
            with col2:
                major = st.text_input(f"Major #{i+1}")
                edu_city = st.text_input(f"City #{i+1}", key=f"edu_city_{i}")
                edu_state = st.text_input(f"State #{i+1}", key=f"edu_state_{i}")
            notes = st.text_input(f"Additional Notes #{i+1}")
            
            education.append({
                "degree": degree,
                "year": year,
                "institution": institution,
                "city": edu_city,
                "state": edu_state,
                "major": major,
                "notes": notes
            })

        # Skills
        st.header("Skills")
        skills = st.text_area("Skills (One per line)")
        skills_list = [x.strip() for x in skills.split('\n') if x.strip()]

        submitted = st.form_submit_button("Generate CV")
        
        if submitted:
            # Create JSON structure
            cv_data = {
                "contact_information": {
                    "full_name": full_name,
                    "phone_number": phone,
                    "email": email
                },
                "profile": {
                    "title": title,
                    "summary": summary,
                    "highlights": highlights_list,
                    "accomplishments": accomplishments_list
                },
                "experience": experiences,
                "education": education,
                "skills": skills_list
            }
            
            # Convert to JSON string
            cv_json = json.dumps(cv_data, indent=2)
            
            try:
                # Call API to generate CV
                response = requests.post(
                    "http://127.0.0.1:5000/api/chatbot",
                    json={"query": cv_json}
                )
                
                if response.status_code == 200:
                    # Get the text response that looks like HTML
                    cv_text = response.text
                    st.success("CV Generated Successfully!")
                    
                    # Display the CV using a custom HTML wrapper
                    st.subheader("Generated CV")
                    html_wrapper = f"""
                    <div style="border: 1px solid #ddd; padding: 20px; border-radius: 5px;">
                        {cv_text}
                    </div>
                    """
                    st.markdown(html_wrapper, unsafe_allow_html=True)
                    
                    # Add download button for the text
                    st.download_button(
                        "Download CV",
                        cv_text,
                        file_name="cv.txt",
                        mime="text/plain"
                    )
                    
                    # Show raw text in expandable section
                    with st.expander("View Raw Text"):
                        st.code(cv_text)
                        
                else:
                    st.error(f"Error generating CV. Status code: {response.status_code}")
                    st.error(f"Response: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to server: {e}")

def main():
    st.set_page_config(
        page_title="CV Generator",
        page_icon="📄",
        layout="wide"
    )
    
    create_cv_form()

if __name__ == "__main__":
    main()