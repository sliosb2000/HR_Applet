# import streamlit as st
# # import pandas as pd
# from pathlib import Path
# from dotenv import load_dotenv
# import os

# from docxtpl import DocxTemplate, Listing
# from docx.enum.text import WD_ALIGN_PARAGRAPH

# from pdf2json import extract_resume_json

# #/app/.env no matter how Streamlit is launched
# APP_DIR = Path(__file__).resolve().parents[1]   # points to app/
# load_dotenv(APP_DIR / ".env", override=False)

# API_KEY = os.getenv("API_KEY",'ollama')
# BASE_URL = os.getenv("BASE_URL",'http://localhost:11434/v1')
# LLM_MODEL = os.getenv("LLM_MODEL",'llama3.1:latest')
# context = None

# # --- Page Config --- 
# st.set_page_config(page_title="CV to template tool", layout="wide")

# # st.markdown("HR Automation Tool")



# # st.markdown("Step #1 Upload pdf resume")
# # --- 1. File upload: Source data : HR filled Offer letter (CSV, XLSX, or Word table) ---
# data_file = st.file_uploader(
#     label="Upload source data : PDF resume",
#     type=["pdf"],
#     help="",
#     key="data_upload"
# )

# if data_file:
#     context = extract_resume_json(data_file, api_key=API_KEY, base_url=BASE_URL, model=LLM_MODEL)
#     st.json(context)
#     #json to fill the template
#     doctemplate = r"data/EFOR-PE DC TEMPLATE.docx"
#     tpl = DocxTemplate(doctemplate)

#     for experience in context["experiences"]:
#         bullet_text = "\n".join(f"• {resp}" for resp in experience["responsibilities"])
#         experience["bullet_list"] = Listing(bullet_text)

#     edu_sd = tpl.new_subdoc()
#     for edu in context["educations"]:
#         # Use a bullet style that exists in the template.
#         p = edu_sd.add_paragraph()
#         p.alignment = WD_ALIGN_PARAGRAPH.CENTER

#         r = p.add_run(f"• {edu["name"]}")
#         r.bold = True
#         p.add_run(f" – {edu['field_of_study']}, {edu['university_name']} ({edu['graduation_year']})")

#     # Put it where your template expects it
#     context["education"] = {"bullet_list": edu_sd}

#     sd = tpl.new_subdoc()
#     for c in context["certifications"]:
#         p = sd.add_paragraph()
#         p.alignment = WD_ALIGN_PARAGRAPH.CENTER
#         p.add_run("• ")
#         p.add_run(c["name"])

#     context["certifications"] = {"bullet_list": sd}

#     # 4) render and save
#     tpl.render(context)
#     tpl.save(f"output_documents/EFOR TEMPLATE FILLED {context["first_name"]}_{context["last_name"]}_{context["job_position"]}.docx")


# if context is not None:
#     # --- 4. download filled document ---
#     st.download_button(
#         label="Generate & Download Word Document",
#         data=Path(f"output_documents/EFOR TEMPLATE FILLED {context["first_name"]}_{context["last_name"]}_{context["job_position"]}.docx").read_bytes(),
#         file_name=f"{context["first_name"]}_{context["last_name"]}_{context["job_position"]}_.docx",
#         mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#     )


