import easyocr
from PIL import Image
import numpy as np
import re
import os
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import io
import psycopg2

def image_to_text(path):
    input_img=Image.open(path)

    #converrting image to array format 
    image_array=np.array(input_img)
    
    reader=easyocr.Reader(['en'])
    text=reader.readtext(image_array,detail=0)
    
    return text,input_img

def extract_text(texts):
    extract_dictionary={"NAME":[],"DESIGNATION":[],"COMPANY_NAME":[],"WEBSITES":[],"CONTACT":[],"EMAIL":[],"ADDRESS":[],"PINCODE":[]}

    extract_dictionary["NAME"].append(texts[0])
    extract_dictionary["DESIGNATION"].append(texts[1])

    for i in range(2,len(texts)):

        if texts[i].startswith("+") or (texts[i].replace("-","") and '-' in texts[i]):
            extract_dictionary["CONTACT"].append(texts[i])

        elif "@" in texts[i] and ".com" in texts[i]:
            extract_dictionary["EMAIL"].append(texts[i])

        elif "WWW" in texts[i] or "Www" in texts[i] or "wWw" in texts[i] or "wwW" in texts[i]:
            small=texts[i].lower()
            extract_dictionary["WEBSITES"].append(small)

        elif "Tamil Nadu" in texts[i] or "TamilNadu" in texts[i] or texts[i].isdigit():
            extract_dictionary["PINCODE"].append(texts[i])

        elif re.match(r'^[A-Za-z]',texts[i]):
            extract_dictionary["COMPANY_NAME"].append(texts[i])

        else:
            remove_colon=re.sub(r'[,;]','',texts[i])
            extract_dictionary["ADDRESS"].append(remove_colon)
    
    for key,value in extract_dictionary.items():
        if len(value)>0:
            concatenate=" ".join(value)
            extract_dictionary[key]=concatenate

        else:
            value="NA"
            extract_dictionary[key]=value
            
    return extract_dictionary



st.set_page_config(layout="wide")
st.title("Bussiness Card")

with st.sidebar:
    select=option_menu("Menu",["Home","Upload&modify","delete"])
if select=="Home":
    st.markdown("### :blue[**Technologies Used :**]Python,eazsy ocr,Streamlit,SQL,Pandas")
    st.write("### :green[**About:**]Bizcard is a Python application designed to extract information from business cards.")
    st.write("### The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR, Bizcard is able to extract text from the images.")

elif select=="Upload&modify":
    st.markdown("## Upload image:")
    img = st.file_uploader("", type=["png", "jpg", "jpeg"])

    if img is not None:
        st.image(img,width=300)

        text_img,input_img=image_to_text(img)
        
        text_dict=extract_text(text_img)

        if text_dict:
            st.success("Text Extract Succesfully")

        df=pd.DataFrame(text_dict,index=[0])

        Image_bytes=io.BytesIO()
        input_img.save(Image_bytes,format="png")

        image_data=Image_bytes.getvalue()

        data={"Image":[image_data]}

        df1=pd.DataFrame(data)

        contact_df=pd.concat([df,df1],axis=1)
        
        st.dataframe(contact_df)

        button_1=st.button("SAVE")

        if button_1:
            mydb=psycopg2.connect(
                                        dbname="Bizcards",
                                        user="postgres",
                                        password="1412",
                                        port="5432")
            cursor=mydb.cursor()

            create_table = '''CREATE TABLE IF NOT EXISTS bizcards_details (
                                                                                name VARCHAR(200),
                                                                                designation VARCHAR(200),
                                                                                company_name VARCHAR(200),
                                                                                website TEXT,
                                                                                contact VARCHAR(200),
                                                                                email VARCHAR(200),                                 
                                                                                address TEXT,
                                                                                pincode VARCHAR(200),
                                                                                image TEXT
                                                                                )'''

            cursor.execute(create_table)
            mydb.commit()

            insert_query = '''INSERT INTO bizcards_details (name, designation, company_name, website,contact,email,address, pincode, image)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)'''

            data = contact_df.values.tolist()[0]  # Assuming contact_df is a Pandas DataFrame
            cursor.execute(insert_query, data)
            mydb.commit()

            st.success("Saved Successfully")

        method=st.radio("if select method",["None","Preview","Modify"])
        
        if method=="None":
            st.write("")

        if method=="Preview":
            mydb=psycopg2.connect(
                                        dbname="Bizcards",
                                        user="postgres",
                                        password="1412",
                                        port="5432")
            cursor=mydb.cursor()

            select_query="select*from bizcards_details"

            cursor.execute(select_query)
            table=cursor.fetchall()
            mydb.commit()

            table_df=pd.DataFrame(table,columns=("NAME","DESIGNATION","COMPANY_NAME","WEBSITE","CONTACT","EMAIL","ADDRESS","PINCODE","IMAGE"))

            st.write(table_df)

        elif method=="Modify":
            mydb=psycopg2.connect(
                                        dbname="Bizcards",
                                        user="postgres",
                                        password="1412",
                                        port="5432")
            cursor=mydb.cursor()

            select_query="select*from bizcards_details"

            cursor.execute(select_query)
            table=cursor.fetchall()
            mydb.commit()

            table_df=pd.DataFrame(table,columns=("NAME","DESIGNATION","COMPANY_NAME","WEBSITE","CONTACT","EMAIL","ADDRESS","PINCODE","IMAGE"))

            st.write(table_df)

            col1,col2=st.columns(2)

            with col1:
                selected_name=st.selectbox("Select the Name:",table_df["NAME"])

                df_3=table_df[table_df["NAME"]==selected_name]

                df_4=df_3.copy()

                st.write(df_4)

            col1,col2=st.columns(2)
            with col1:

                ca_name=st.text_input("Name",df_3["NAME"].unique()[0])
                ca_designation=st.text_input("Designation",df_3["DESIGNATION"].unique()[0])
                ca_company=st.text_input("Company Name",df_3["COMPANY_NAME"].unique()[0])
                ca_website=st.text_input("Website",df_3["WEBSITE"].unique()[0])
                ca_cont=st.text_input("Contact",df_3["CONTACT"].unique()[0])

                df_4["NAME"]=ca_name
                df_4["DESIGNATION"]=ca_designation
                df_4["COMPANY_NAME"]=ca_company
                df_4["WEBSITE"]=ca_website
                df_4["CONTACT"]=ca_cont

            with col2:
                ca_em=st.text_input("Email",df_3["EMAIL"].unique()[0])
                ca_address=st.text_input("Address",df_3["ADDRESS"].unique()[0])
                ca_pinc=st.text_input("Pincode",df_3["PINCODE"].unique()[0])
                ca_image=st.text_input("Image",df_3["IMAGE"].unique()[0])

                df_4["EMAIL"]=ca_em
                df_4["ADDRESS"]=ca_address
                df_4["PINCODE"]=ca_pinc
                df_4["IMAGE"]=ca_image

            st.dataframe(df_4)

            col1,col2=st.columns(2)
            with col1:
                button_3=st.button("Modify")

            if button_3:
                mydb=psycopg2.connect(
                                        dbname="Bizcards",
                                        user="postgres",
                                        password="1412",
                                        port="5432")
            cursor=mydb.cursor()

            cursor.execute(f"delete from bizcards_details where name='{selected_name}'")
            mydb.commit()

            insert_query = '''INSERT INTO bizcards_details (name, designation, company_name, website,contact,email,address, pincode, image)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            
            datas=df_4.values.tolist()[0]
            cursor.execute(insert_query,datas)
            mydb.commit()

            st.success("MODIFY")

elif select=="delete":
    mydb=psycopg2.connect( dbname="Bizcards",
                                user="postgres",
                                password="1412",
                                port="5432")
    cursor=mydb.cursor()

    col1,col2=st.columns(2)
    with col1:
        select_query="select name from bizcards_details"

        cursor.execute(select_query)
        table_1=cursor.fetchall()
        mydb.commit()

        name=[]

        for i in table_1:
            name.append(i[0])

        Name_select=st.selectbox("Select Name",name)

    with col2:
        select_query=f"select designation from bizcards_details where NAME='{Name_select}'"
        cursor.execute(select_query)
        table_2=cursor.fetchall()
        mydb.commit()

        designation_1=[]

        for j in table_2:
            designation_1.append(j[0])

        designation_select=st.selectbox("Designation select",designation_1)

        if Name_select and designation_select:
            st.write(f"Select Name : {Name_select}")

            st.write(f"Designation: {designation_select}")

            remove=st.button("Deleted",use_container_width=True)

            if remove:
                mydb=psycopg2.connect( dbname="Bizcards",
                            user="postgres",
                            password="1412",
                            port="5432")
                cursor=mydb.cursor()

                cursor.execute(f"delete from bizcards_details where NAME='{Name_select}' and designation='{designation_select}'")

                mydb.commit()

                st.warning("DELETED")


        
               



        




