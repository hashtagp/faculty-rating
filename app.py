import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

# Set page config
st.set_page_config(page_title="Faculty Ratings Dashboard", layout="wide")

# Streamlit App Title
st.title("📊 Faculty Ratings Dashboard")

# Add app description
st.markdown("""
This app allows you to process and visualize faculty feedback data. 
You can either upload raw feedback data for processing or analyze pre-processed faculty ratings.
""")

# Initialize session state to store processed data
if 'faculty_ratings_df' not in st.session_state:
    st.session_state.faculty_ratings_df = None
if 'comments_df' not in st.session_state:
    st.session_state.comments_df = None  
if 'course_feedback_df' not in st.session_state:
    st.session_state.course_feedback_df = None
if 'avg_ratings' not in st.session_state:
    st.session_state.avg_ratings = None

# Create tabs
tab1, tab2 = st.tabs(["Process & Visualize Data", "About"])

with tab1:
    # Select processing mode
    process_mode = st.radio(
        "Select Mode:",
        ["Process Raw Feedback Data", "Analyze Processed Data"],
        horizontal=True
    )
    
    if process_mode == "Process Raw Feedback Data":
        # Upload File - Raw Data
        uploaded_file = st.file_uploader("Upload Raw Feedback Data (CSV or Excel)", type=["xlsx", "csv"])
        
        if uploaded_file is not None:
            try:
                # Read file
                if uploaded_file.name.endswith(".csv"):
                    raw_df = pd.read_csv(uploaded_file)
                else:
                    raw_df = pd.read_excel(uploaded_file)
                
                st.success("✅ Raw data file uploaded successfully!")
                
                # Display raw data sample
                with st.expander("Preview Raw Data"):
                    st.dataframe(raw_df.head())
                
                # Process button
                if st.button("Process Raw Data"):
                    with st.spinner("Processing data... This may take a moment."):
                        # Initialize empty lists to store the transformed data
                        student_names = []
                        srns = []
                        sections = []
                        faculty_names = []
                        courses = []
                        rating_types = []
                        ratings = []
                        course_feedbacks = []
                        comments = []

                        # Helper function to identify which columns belong to which course/faculty
                        def identify_course_columns(columns):
                            course_blocks = []
                            current_block = []
                            current_course = None

                            for i, col in enumerate(columns):
                                if isinstance(col, str) and col.startswith('Feedback on '):
                                    if current_block:
                                        course_blocks.append((current_course, current_block))
                                        current_block = []
                                    current_course = col
                                    current_block = []
                                elif current_course is not None:
                                    current_block.append(i)

                            # Add the last block
                            if current_block:
                                course_blocks.append((current_course, current_block))

                            return course_blocks

                        # Get the course blocks
                        course_blocks = identify_course_columns(raw_df.columns)

                        # Process each row
                        for index, row in raw_df.iterrows():
                            student_name = row.get('Name of the Student', None)
                            srn = row.get('SRN', None)
                            section = row.get('Section', None)

                            if pd.isna(student_name) or pd.isna(srn):
                                continue

                            # Process each course block
                            for course_name, column_indices in course_blocks:
                                # Find faculty name column
                                faculty_col = [i for i in column_indices if 'Name of the Faculty' in raw_df.columns[i]]
                                if not faculty_col:
                                    continue

                                faculty_name = row[raw_df.columns[faculty_col[0]]]

                                # Find question columns
                                question_cols = [i for i in column_indices if 'Please give a rating' in raw_df.columns[i]]

                                # Process each question
                                for q_col in question_cols:
                                    question = raw_df.columns[q_col]
                                    rating = row[raw_df.columns[q_col]]

                                    if not pd.isna(rating):
                                        student_names.append(student_name)
                                        srns.append(srn)
                                        sections.append(section)
                                        faculty_names.append(faculty_name)
                                        courses.append(course_name)
                                        rating_types.append(question)
                                        ratings.append(rating)

                                # Get comments if available
                                comment_col = [i for i in column_indices if raw_df.columns[i] == 'Comments']
                                if comment_col:
                                    comment = row[raw_df.columns[comment_col[0]]]
                                    if not pd.isna(comment):
                                        comments.append({
                                            'Student': student_name,
                                            'SRN': srn,
                                            'Faculty': faculty_name,
                                            'Course': course_name,
                                            'Comment': comment
                                        })

                                # Get course feedback questions
                                course_feedback_cols = [i for i in column_indices if 'The course' in raw_df.columns[i]]
                                for cf_col in course_feedback_cols:
                                    question = raw_df.columns[cf_col]
                                    rating = row[raw_df.columns[cf_col]]

                                    if not pd.isna(rating):
                                        course_feedbacks.append({
                                            'Student': student_name,
                                            'SRN': srn,
                                            'Course': course_name,
                                            'Question': question,
                                            'Rating': rating
                                        })

                        # Create the main faculty ratings DataFrame
                        faculty_ratings_df = pd.DataFrame({
                            'Student Name': student_names,
                            'SRN': srns,
                            'Section': sections,
                            'Faculty Name': faculty_names,
                            'Course': courses,
                            'Rating Category': rating_types,
                            'Rating': ratings
                        })

                        # Create the comments DataFrame
                        comments_df = pd.DataFrame(comments)

                        # Create the course feedback DataFrame
                        course_feedback_df = pd.DataFrame(course_feedbacks)
                        
                        # Clean faculty names
                        faculty_ratings_df['Faculty Name'] = faculty_ratings_df['Faculty Name'].astype(str).str.replace(r"Section[ -]?[A-Z]?[ -]?", "", regex=True).str.strip()
                        
                        # Clean the rating categories
                        faculty_ratings_df['Rating Category'] = (
                            faculty_ratings_df['Rating Category']
                            .str.strip()
                            .str.lower()
                            .str.replace(r"\s+", " ", regex=True)
                            .str.split("(").str[0]
                            .str.strip()
                        )
                        
                        # Convert rating to numeric
                        faculty_ratings_df['Rating'] = pd.to_numeric(faculty_ratings_df['Rating'], errors='coerce')
                        
                        # Save data to session state for persistence
                        st.session_state.faculty_ratings_df = faculty_ratings_df
                        st.session_state.comments_df = comments_df
                        st.session_state.course_feedback_df = course_feedback_df
                        
                        # Compute averages for visualization
                        avg_ratings = (
                            faculty_ratings_df.groupby(["Faculty Name", "Rating Category"], as_index=False)
                            .agg({"Rating": "mean"})
                        )
                        
                        # Save averages to session state
                        st.session_state.avg_ratings = avg_ratings
                
                # Display processed data if available in session state
                if st.session_state.faculty_ratings_df is not None:
                    st.subheader("Processed Data")
                    
                    # Create tabs for different datasets
                    data_tabs = st.tabs(["Faculty Ratings", "Student Comments", "Course Feedback"])
                    
                    with data_tabs[0]:
                        st.write(f"Faculty Ratings: {len(st.session_state.faculty_ratings_df)} records")
                        st.dataframe(st.session_state.faculty_ratings_df.head(10))
                        
                        # Download button for faculty ratings
                        faculty_buffer = io.BytesIO()
                        with pd.ExcelWriter(faculty_buffer, engine='openpyxl') as writer:
                            st.session_state.faculty_ratings_df.to_excel(writer, index=False)
                        faculty_buffer.seek(0)
                        
                        st.download_button(
                            label="Download Faculty Ratings Data",
                            data=faculty_buffer,
                            file_name="faculty_ratings.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    with data_tabs[1]:
                        if not st.session_state.comments_df.empty:
                            st.write(f"Student Comments: {len(st.session_state.comments_df)} records")
                            st.dataframe(st.session_state.comments_df.head(10))
                            
                            # Download button for comments
                            comments_buffer = io.BytesIO()
                            with pd.ExcelWriter(comments_buffer, engine='openpyxl') as writer:
                                st.session_state.comments_df.to_excel(writer, index=False)
                            comments_buffer.seek(0)
                            
                            st.download_button(
                                label="Download Student Comments Data",
                                data=comments_buffer,
                                file_name="student_comments.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            st.info("No student comments found in the data.")
                    
                    with data_tabs[2]:
                        if not st.session_state.course_feedback_df.empty:
                            st.write(f"Course Feedback: {len(st.session_state.course_feedback_df)} records")
                            st.dataframe(st.session_state.course_feedback_df.head(10))
                            
                            # Download button for course feedback
                            course_buffer = io.BytesIO()
                            with pd.ExcelWriter(course_buffer, engine='openpyxl') as writer:
                                st.session_state.course_feedback_df.to_excel(writer, index=False)
                            course_buffer.seek(0)
                            
                            st.download_button(
                                label="Download Course Feedback Data",
                                data=course_buffer,
                                file_name="course_feedback_ratings.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            st.info("No course feedback found in the data.")
                    
                    # Visualization section
                    st.subheader("Visualize Faculty Ratings")
                    
                    # Select Faculty
                    faculties = st.session_state.avg_ratings["Faculty Name"].unique()
                    
                    if len(faculties) == 0:
                        st.error("❌ No faculty names detected! Please check your data.")
                    else:
                        selected_faculty = st.selectbox("🎓 Select a Faculty", faculties)
                        
                        # Filter Data for Selected Faculty
                        faculty_data = st.session_state.avg_ratings[st.session_state.avg_ratings["Faculty Name"] == selected_faculty]
                        
                        # Plot Ratings
                        fig, ax = plt.subplots(figsize=(12, 8))  # Increased height from 6 to 8
                        bars = ax.bar(faculty_data["Rating Category"], faculty_data["Rating"], color="skyblue", width=0.6)  # Added width parameter

                        ax.set_title(f"📈 Average Ratings for {selected_faculty}", fontsize=14)
                        ax.set_xlabel("Rating Category", fontsize=12)
                        ax.set_ylabel("Average Rating (1-5)", fontsize=12)
                        ax.set_ylim(0, 5.5)  # Keep the same y-limit
                        plt.xticks(rotation=45, ha="right", fontsize=10)
                        
                        # Add labels on bars
                        for bar, category, rating in zip(bars, faculty_data["Rating Category"], faculty_data["Rating"]):
                            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{rating:.2f}", ha="center", va="bottom", fontsize=10)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        
                        # Save figure option
                        save_fig_buffer = io.BytesIO()
                        fig.savefig(save_fig_buffer, format='png', dpi=300, bbox_inches='tight')
                        save_fig_buffer.seek(0)
                        
                        st.download_button(
                            label="Download Chart",
                            data=save_fig_buffer,
                            file_name=f"{selected_faculty}_ratings.png",
                            mime="image/png"
                        )
                
            except Exception as e:
                st.error(f"⚠️ Error processing the file: {e}")
                st.exception(e)
                
    else:  # Analyze Processed Data
        # Clear session state when switching to the other mode
        if st.session_state.faculty_ratings_df is not None:
            st.session_state.faculty_ratings_df = None
            st.session_state.comments_df = None
            st.session_state.course_feedback_df = None
            st.session_state.avg_ratings = None
            
        # Upload File - Processed Data
        uploaded_file = st.file_uploader("Upload Processed Faculty Ratings (CSV or Excel)", type=["xlsx", "csv"])
        
        if uploaded_file is not None:
            try:
                # Read file
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file, encoding="utf-8")
                else:
                    df = pd.read_excel(uploaded_file, engine="openpyxl")
                
                st.success("✅ File uploaded successfully!")
                
                # Display data sample
                with st.expander("Preview Data"):
                    st.dataframe(df.head())
                
                # Identify Faculty Name Column
                faculty_col = [col for col in df.columns if "faculty" in col.lower()]
                if not faculty_col:
                    st.error("❌ No Faculty Name column found! Check your file.")
                    st.stop()
                faculty_col = faculty_col[0]
                
                # Clean Faculty Names if not already cleaned
                if "Faculty Name" not in df.columns:
                    df["Faculty Name"] = df[faculty_col].astype(str).str.replace(r"Section[ -]?[A-Z]?[ -]?", "", regex=True).str.strip()
                
                # Drop rows with missing faculty names
                df = df.dropna(subset=["Faculty Name"])
                
                # Extract Rating Columns Dynamically
                rating_cols = [col for col in df.columns if any(x in col.lower() for x in ["course", "rating", "evaluation"])]
                if not rating_cols and "Rating Category" not in df.columns:
                    st.error("❌ No Rating columns found! Check your file.")
                    st.stop()
                
                # Process data if it's not already in the right format
                if "Rating Category" not in df.columns or "Rating" not in df.columns:
                    # Melt Data for Analysis
                    melted_df = df.melt(id_vars=["Faculty Name"], value_vars=rating_cols, var_name="Rating Category", value_name="Rating")
                    
                    # Fix Duplicate Questions: Normalize Category Names
                    melted_df["Rating Category"] = (
                        melted_df["Rating Category"]
                        .str.strip()
                        .str.lower()
                        .str.replace(r"\s+", " ", regex=True)
                        .str.split("(").str[0]
                        .str.strip()
                    )
                    
                    melted_df = melted_df.dropna(subset=["Rating"])
                    
                    # Convert Rating to Numeric
                    melted_df["Rating"] = pd.to_numeric(melted_df["Rating"], errors="coerce")
                    
                    # Compute Averages
                    avg_ratings = (
                        melted_df.groupby(["Faculty Name", "Rating Category"], as_index=False)
                        .agg({"Rating": "mean"})
                    )
                else:
                    # If data is already in the right format
                    avg_ratings = df
                
                # Store in session state
                st.session_state.avg_ratings = avg_ratings
                
                # Select Faculty
                faculties = avg_ratings["Faculty Name"].unique()
                
                if len(faculties) == 0:
                    st.error("❌ No faculty names detected! Please check your data.")
                    st.stop()
                
                selected_faculty = st.selectbox("🎓 Select a Faculty", faculties)
                
                # Filter Data for Selected Faculty
                faculty_data = avg_ratings[avg_ratings["Faculty Name"] == selected_faculty]
                
                # Plot Ratings
                fig, ax = plt.subplots(figsize=(12, 8))  # Increased height from 6 to 8
                bars = ax.bar(faculty_data["Rating Category"], faculty_data["Rating"], color="skyblue", width=0.6)  # Added width parameter

                ax.set_title(f"📈 Average Ratings for {selected_faculty}", fontsize=14)
                ax.set_xlabel("Rating Category", fontsize=12)
                ax.set_ylabel("Average Rating (1-5)", fontsize=12)
                ax.set_ylim(0, 5.5)  # Keep the same y-limit
                plt.xticks(rotation=45, ha="right", fontsize=10)
                
                # Add labels on bars
                for bar, category, rating in zip(bars, faculty_data["Rating Category"], faculty_data["Rating"]):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{rating:.2f}", ha="center", va="bottom", fontsize=10)
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # Save figure option
                save_fig_buffer = io.BytesIO()
                fig.savefig(save_fig_buffer, format='png', dpi=300, bbox_inches='tight')
                save_fig_buffer.seek(0)
                
                st.download_button(
                    label="Download Chart",
                    data=save_fig_buffer,
                    file_name=f"{selected_faculty}_ratings.png",
                    mime="image/png"
                )
                
            except Exception as e:
                st.error(f"⚠️ Error processing the file: {e}")
                st.exception(e)

with tab2:
    st.header("About This App")
    st.markdown("""
    ### Faculty Ratings Dashboard
    
    This app helps analyze and visualize faculty feedback data. It offers two main functions:
    
    1. **Process Raw Feedback Data**: Upload raw feedback forms and convert them into structured data
    2. **Analyze Processed Data**: Upload already processed faculty ratings data for visualization
    
    ### Features:
    
    - Clean and transform raw feedback data
    - Generate visualizations of faculty ratings
    - Download processed data as Excel files
    - Download visualizations as PNG images
    
    ### How to Use:
    
    1. Select the desired mode (Process Raw Data or Analyze Processed Data)
    2. Upload your data file (CSV or Excel format)
    3. Follow the on-screen instructions to process or visualize your data
    
    For raw data processing, the app will generate three datasets:
    - Faculty ratings
    - Student comments
    - Course feedback ratings
    
    Each dataset can be downloaded separately for further analysis.
    """)