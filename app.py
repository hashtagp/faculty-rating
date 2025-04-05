import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib
matplotlib.use('Agg')

# Function to convert Matplotlib figure to ReportLab Image
def fig_to_image(fig):
    """Convert a Matplotlib figure to a ReportLab Image"""
    canvas = FigureCanvasAgg(fig)
    buf = io.BytesIO()
    canvas.print_png(buf)
    buf.seek(0)
    return Image(buf, width=7*inch, height=4*inch)

# Function to generate faculty report
def generate_faculty_report(faculty_data):
    """Generate a text report with rating categories and values"""
    faculty_name = faculty_data["Faculty Name"].iloc[0]
    report = f"Faculty Rating Report for: {faculty_name}\n"
    report += f"Generated on: {datetime.now().strftime('%Y-%m-%d')}\n"
    report += "=" * 50 + "\n\n"
    
    # Add overall average
    overall_avg = faculty_data["Rating"].mean()
    report += f"OVERALL AVERAGE: {overall_avg:.2f} / 5.0\n\n"
    report += "RATINGS BY CATEGORY:\n"
    report += "-" * 50 + "\n\n"
    
    # Sort ratings from highest to lowest
    sorted_data = faculty_data.sort_values(by="Rating", ascending=False)
    
    # Add each category and its rating
    for _, row in sorted_data.iterrows():
        category = row["Rating Category"].title()
        rating = row["Rating"]
        report += f"{category}: {rating:.2f}\n"
    
    return report

def generate_pdf_report(faculty_data, course_name):
    """Generate a PDF report with ratings in table format"""
    faculty_name = faculty_data["Faculty Name"].iloc[0]
    
    # Create buffer for PDF with reduced margins
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=36,  # 0.5 inch
        leftMargin=36,   # 0.5 inch
        topMargin=36,    # 0.5 inch
        bottomMargin=36  # 0.5 inch
    )
    elements = []
    styles = getSampleStyleSheet()
    
    try:
        # Add logo (adjust path as needed)
        logo = Image("REVA_logo.png", width=180, height=50)
        logo.hAlign = 'RIGHT'  # Right align the logo
        elements.append(logo)
        elements.append(Spacer(1, 10))  # Add small space after logo
    except:
        # If logo file not found, continue without it
        pass
    
    # Create custom styles
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1,  # Center alignment
        spaceAfter=10
    )
    
    faculty_style = ParagraphStyle(
        'FacultyName',
        parent=styles['Normal'],
        fontSize=12,
        alignment=0,  # Left alignment
        spaceBefore=10,
        spaceAfter=20
    )
    
    # Add headers
    elements.append(Paragraph("School of Computing and Information Technology", header_style))
    elements.append(Paragraph("Academic year 2024-2025", header_style))
    
    # Get course code if available
    clean_course_name = course_name.replace("Feedback on ", "").strip()
    if clean_course_name in st.session_state.course_code_mapping:
        course_code = st.session_state.course_code_mapping[clean_course_name]
        elements.append(Paragraph(f"Course: {clean_course_name} ({course_code})", header_style))
    else:
        elements.append(Paragraph(f"Course: {clean_course_name}", header_style))
    
    elements.append(Paragraph(f"Name of the Faculty: {faculty_name}", faculty_style))
    elements.append(Spacer(1, 20))
    
    # Calculate overall average
    overall_avg = faculty_data["Rating"].mean().round(2)
    elements.append(Paragraph(f"Overall Average: {overall_avg:.2f} / 5.0", styles['Heading3']))
    elements.append(Spacer(1, 20))
    
    # Prepare table data
    sorted_data = faculty_data.sort_values(by="Rating", ascending=False)
    table_data = [["Rating Category", "Score"]]  # Header row
    
    for _, row in sorted_data.iterrows():
        # Split long category names into multiple lines if longer than 40 chars
        category = row["Rating Category"].title()
        if len(category) > 70:
            # Split at space nearest to middle
            mid = category[:70].rfind(' ')
            if mid == -1:  # No space found, force split
                mid = 70
            category = category[:mid] + '\n' + category[mid:].strip()
            
        table_data.append([
            category,
            f"{row['Rating']:.2f}"
        ])
    
    # Create table with increased width and automatic word wrapping
    table = Table(table_data, colWidths=[5*inch, 1*inch])
    
    # Style the table with word wrap and vertical alignment
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),    
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('WORDWRAP', (0, 0), (-1, -1), True),  
    ])
    
    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 30))

    # Create and add bar chart with increased height
    fig, ax = plt.subplots(figsize=(10, 8))  # Increased height from 6 to 8
    bars = ax.bar(faculty_data["Rating Category"], faculty_data["Rating"], color="skyblue", width=0.4)  # Reduced width for taller appearance
    ax.set_title(f"Ratings Distribution", fontsize=12)
    ax.set_xlabel("Rating Category", fontsize=10)
    ax.set_ylabel("Rating", fontsize=10)
    ax.set_ylim(0, 5.5)  # Set y-axis limit to make bars appear taller
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Convert figure to ReportLab Image with increased height
    chart_img = fig_to_image(fig)
    chart_img.hAlign = 'CENTER'
    chart_img._height = 5*inch  # Increase image height in the PDF
    elements.append(chart_img)
    plt.close(fig)  # Close the figure to free memory
    
    # Force the footer to appear at the bottom of the page
    # First, calculate remaining space and add a spacer to push the footer down
    # A typical US Letter page is 11 inches high (minus margins)
    page_height = letter[1] - doc.topMargin - doc.bottomMargin
    
    # We already used about 7.5-8 inches (header + table + chart)
    # Add a spacer that will push the footer to the bottom
    elements.append(Spacer(1, 1.5*inch))  # Add extra space to push footer down
    
    # Add footer signatures
    footer_data = [["Academic Vertical Head", "Faculty", "Director/HOD"]]
    footer_table = Table(footer_data, colWidths=[2.0*inch, 2.0*inch, 2.0*inch])
    footer_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 30),  # Space for signature
    ])
    
    footer_table.setStyle(footer_style)
    elements.append(footer_table)
    
    # Build PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer

# Function to generate table visualization for faculty
def generate_table_visualization(faculty_data):
    """Generate a table visualization of faculty ratings as a figure"""
    if faculty_data.empty:
        return None
    
    faculty_name = faculty_data["Faculty Name"].iloc[0]
    
    # Calculate total average
    total_avg = faculty_data['Rating'].mean().round(4)
    
    # Create new row for total average
    new_row = pd.DataFrame({
        'Faculty Name': [faculty_name],
        'Rating Category': ['Total Average'],
        'Rating': [total_avg]
    })
    
    # Append new row to faculty data
    viz_data = pd.concat([faculty_data, new_row], ignore_index=True)
    
    # Prepare data for table
    headers = ['Rating Category', 'Average Rating']
    data = viz_data[['Rating Category', 'Rating']].values.tolist()
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis('off')  # Hide axes
    
    # Add title
    plt.title(f"Ratings for {faculty_name}", fontsize=14, pad=20)
    
    # Create table
    table = ax.table(
        cellText=data,
        colLabels=headers,
        loc='center',
        cellLoc='left',
        colWidths=[0.7, 0.3]
    )
    
    # Set font size and padding
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 1.5)
    
    plt.tight_layout()
    return fig

# Function to verify data processing
def verify_data_processing(faculty_ratings_df, comments_df, course_feedback_df):
    """Print verification of data processing including course information"""
    print("\nData Processing Verification:")
    print("-" * 50)
    
    # Verify faculty ratings
    print("\nFaculty Ratings Summary:")
    print(f"Total records: {len(faculty_ratings_df)}")
    print("\nUnique courses:")
    for course in sorted(faculty_ratings_df['Course'].unique()):
        course_data = faculty_ratings_df[faculty_ratings_df['Course'] == course]
        print(f"- {course}: {len(course_data)} ratings")
    
    # Verify faculty-course combinations
    faculty_course = faculty_ratings_df.groupby(['Faculty Name', 'Course']).size().reset_index()
    print("\nFaculty-Course combinations:")
    for _, row in faculty_course.iterrows():
        print(f"- {row['Faculty Name']} - {row['Course']}")
    
    # Verify comments
    if not comments_df.empty:
        print("\nComments Summary:")
        print(f"Total comments: {len(comments_df)}")
        print("\nComments per course:")
        for course in sorted(comments_df['Course'].unique()):
            course_comments = comments_df[comments_df['Course'] == course]
            print(f"- {course}: {len(course_comments)} comments")
    
    # Verify course feedback
    if not course_feedback_df.empty:
        print("\nCourse Feedback Summary:")
        print(f"Total feedback entries: {len(course_feedback_df)}")
        print("\nFeedback per course:")
        for course in sorted(course_feedback_df['Course'].unique()):
            course_fb = course_feedback_df[course_feedback_df['Course'] == course]
            print(f"- {course}: {len(course_fb)} feedback entries")

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
if 'course_code_mapping' not in st.session_state:
    st.session_state.course_code_mapping = {}

# Create tabs
tab1, tab2 = st.tabs(["Process & Visualize Data", "About"])

with tab1:
    # Course code mapping upload
    with st.expander("Upload Course Code Mapping (Optional)"):
        st.info("Upload an Excel file with columns for course names and their corresponding course codes.")
        course_mapping_file = st.file_uploader("Course Code Mapping File (Excel)", type=["xlsx", "csv"], key="course_mapping")
        
        if course_mapping_file is not None:
            try:
                if course_mapping_file.name.endswith(".csv"):
                    mapping_df = pd.read_csv(course_mapping_file)
                else:
                    mapping_df = pd.read_excel(course_mapping_file)
                
                # Check if dataframe has required columns
                required_cols = ["course_name", "course_code"]
                if not all(col.lower() in [c.lower() for c in mapping_df.columns] for col in required_cols):
                    st.warning("The mapping file should have columns for 'course_name' and 'course_code'.")
                else:
                    # Find the actual column names (case insensitive)
                    course_name_col = next(col for col in mapping_df.columns if col.lower() == "course_name")
                    course_code_col = next(col for col in mapping_df.columns if col.lower() == "course_code")
                    
                    # Create mapping dictionary
                    mapping_dict = dict(zip(mapping_df[course_name_col], mapping_df[course_code_col]))
                    st.session_state.course_code_mapping = mapping_dict
                    
                    st.success(f"✅ Course mapping loaded successfully! {len(mapping_dict)} courses mapped.")
                    
                    # Show mapping preview
                    st.write("Mapping Preview:")
                    preview_df = pd.DataFrame(list(mapping_dict.items()), columns=["Course Name", "Course Code"])
                    st.dataframe(preview_df.head(5))
            except Exception as e:
                st.error(f"⚠️ Error loading course mapping file: {e}")

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
                        
                        # Verify data processing
                        verify_data_processing(faculty_ratings_df, comments_df, course_feedback_df)
                
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
                        faculty_data = st.session_state.faculty_ratings_df[
                            st.session_state.faculty_ratings_df["Faculty Name"] == selected_faculty
                        ].copy()
                        
                        # Get unique course name for this faculty
                        course_name = faculty_data["Course"].iloc[0].replace("Feedback on ", "") if len(faculty_data) > 0 else "N/A"
                        
                        # Update averages computation
                        avg_ratings = faculty_data.groupby(["Faculty Name", "Rating Category"], as_index=False).agg({"Rating": "mean"})
                        
                        # Select visualization type
                        viz_type = st.radio(
                            "Choose Visualization Type:",
                            ["Bar Chart", "Table"],
                            horizontal=True
                        )
                        
                        if viz_type == "Bar Chart":
                            # Plot Ratings using avg_ratings
                            fig, ax = plt.subplots(figsize=(12, 8))  # Increased height from 6 to 8
                            bars = ax.bar(avg_ratings["Rating Category"], avg_ratings["Rating"], color="skyblue", width=0.6)  # Added width parameter

                            ax.set_title(f"📈 Average Ratings for {selected_faculty}", fontsize=14)
                            ax.set_xlabel("Rating Category", fontsize=12)
                            ax.set_ylabel("Average Rating (1-5)", fontsize=12)
                            ax.set_ylim(0, 5.5)  # Keep the same y-limit
                            plt.xticks(rotation=45, ha="right", fontsize=10)
                            
                            # Add labels on bars
                            for bar, category, rating in zip(bars, avg_ratings["Rating Category"], avg_ratings["Rating"]):
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
                                file_name=f"{selected_faculty}_ratings_chart.png",
                                mime="image/png"
                            )
                        else:  # Table visualization
                            # Generate table visualization using avg_ratings
                            table_fig = generate_table_visualization(avg_ratings)
                            if table_fig:
                                st.pyplot(table_fig)
                                
                                # Save table figure option
                                table_buffer = io.BytesIO()
                                table_fig.savefig(table_buffer, format='png', dpi=300, bbox_inches='tight')
                                table_buffer.seek(0)
                                
                                st.download_button(
                                    label="Download Table Image",
                                    data=table_buffer,
                                    file_name=f"{selected_faculty}_ratings_table.png",
                                    mime="image/png"
                                )
                        
                        # Add horizontal line for visual separation
                        st.markdown("---")
                        
                        # Generate text report for rating categories
                        faculty_report = generate_faculty_report(avg_ratings)

                        # Create columns for layout
                        report_col1, report_col2 = st.columns([1, 2])

                        with report_col1:
                            # Add text report download button
                            st.download_button(
                                label="Download Text Report",
                                data=faculty_report,
                                file_name=f"{selected_faculty}_ratings_report.txt",
                                mime="text/plain"
                            )
                            
                            # Add PDF report download button
                            pdf_buffer = generate_pdf_report(avg_ratings, course_name)
                            st.download_button(
                                label="Download PDF Report",
                                data=pdf_buffer,
                                file_name=f"{selected_faculty}_ratings_report.pdf",
                                mime="application/pdf"
                            )

                        with report_col2:
                            # Preview the report
                            st.text("Report Preview:")
                            st.text_area("", faculty_report, height=250)
                
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
                
                # Select visualization type
                viz_type = st.radio(
                    "Choose Visualization Type:",
                    ["Bar Chart", "Table"],
                    horizontal=True
                )
                
                if viz_type == "Bar Chart":
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
                        file_name=f"{selected_faculty}_ratings_chart.png",
                        mime="image/png"
                    )
                else:  # Table visualization
                    # Generate table visualization
                    table_fig = generate_table_visualization(faculty_data)
                    if table_fig:
                        st.pyplot(table_fig)
                        
                        # Save table figure option
                        table_buffer = io.BytesIO()
                        table_fig.savefig(table_buffer, format='png', dpi=300, bbox_inches='tight')
                        table_buffer.seek(0)
                        
                        st.download_button(
                            label="Download Table Image",
                            data=table_buffer,
                            file_name=f"{selected_faculty}_ratings_table.png",
                            mime="image/png"
                        )
                
                # Add horizontal line for visual separation
                st.markdown("---")
                
                # Generate text report for rating categories
                faculty_report = generate_faculty_report(faculty_data)

                # Create columns for layout
                report_col1, report_col2 = st.columns([1, 2])

                with report_col1:
                    # Add text report download button
                    st.download_button(
                        label="Download Text Report",
                        data=faculty_report,
                        file_name=f"{selected_faculty}_ratings_report.txt",
                        mime="text/plain"
                    )
                    
                    # Add PDF report download button
                    pdf_buffer = generate_pdf_report(faculty_data, "N/A")
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_buffer,
                        file_name=f"{selected_faculty}_ratings_report.pdf",
                        mime="application/pdf"
                    )

                with report_col2:
                    # Preview the report
                    st.text("Report Preview:")
                    st.text_area("", faculty_report, height=250)
                
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
    - Generate visualizations of faculty ratings (bar charts or tables)
    - Download processed data as Excel files
    - Download visualizations as PNG images
    - Create text reports with ratings information
    
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
