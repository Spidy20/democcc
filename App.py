import streamlit as st
import os
from PIL import Image
from Face_Recognition import Recognise_Face
import sqlite3
import time, datetime
import pandas as pd

connection = sqlite3.connect("face_recognition.db")
cursor = connection.cursor()
# apt-get install build-essential cmake pkg-config
# apt-get install libx11-dev libatlas-base-dev
# apt-get install libgtk-3-dev libboost-python-dev

# Create Data store table
data_table_sql = '''CREATE TABLE IF NOT EXISTS REGISTERED_FACES
                    (ID varchar(15) NOT NULL,
                    Name varchar(100) NOT NULL,
                    PRIMARY KEY (ID));
'''
cursor.execute(data_table_sql)
connection.commit()

# To Store the attendance
# ts = time.time()
# Date = datetime.datetime.fromtimestamp(ts).strftime('%Y_%m_%d')
# timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
# Time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
# Hour, Minute, Second = timeStamp.split(":")
# att_table_name = str('attendance' + "_" + Date + "_Time_" + Hour + "_" + Minute + "_" + Second)
#
# atte_table_sql = "CREATE TABLE IF NOT EXISTS " + att_table_name + \
#                  '''(ID INT NOT NULL AUTOINCREMENT,
#                     Uploaded_image VARCHAR(50) NOT NULL,
#                     User_ID varchar(15) NOT NULL,
#                     Name varchar(50) NOT NULL,
#                     Latitude varchar(30) NOT NULL,
#                     Longitude varchar(40) NOT NULL,
#                     Timestamp VARCHAR(50) NOT NULL,
#                     PRIMARY KEY (ID));'''
atte_table_sql = '''CREATE TABLE IF NOT EXISTS FACE_ATTENDANCE
                    (ID INTEGER PRIMARY KEY NOT NULL,
                    Uploaded_image VARCHAR(50) NOT NULL,
                    User_ID varchar(15) NOT NULL,
                    Name varchar(50) NOT NULL,
                    Latitude varchar(30) NOT NULL,
                    Longitude varchar(40) NOT NULL,
                    Timestamp VARCHAR(50) NOT NULL);'''
cursor.execute(atte_table_sql)
connection.commit()

av_ids = os.listdir('./Uploaded_Faces')

def run():
    activities = ["Face Data Upload", "Face Recognition", "Admin"]
    st.sidebar.markdown("# Choose Input Source")
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    if choice == activities[0]:
        st.title("Face Data Upload")
        st.markdown('''<h5 style='text-align: left; color: #d73b5c;'>* You need to upload your HD Image, make sure 
        you are alone & properly visible"</h5>''',
                    unsafe_allow_html=True)
        unique_id = st.number_input('Enter Unique ID', min_value=1)
        user_name = st.text_input("Enter your Name")
        img_file = st.file_uploader("Choose an Image", type=['jpg', 'png'])
        if st.button("Upload") and unique_id != '' and user_name != '' and img_file is not None:

            if str(unique_id) not in av_ids:
                ## Data insert
                insert_sql = """insert into REGISTERED_FACES values (?,?)"""
                data_val = (str(unique_id), user_name)
                cursor.execute(insert_sql, data_val)
                connection.commit()

                os.mkdir('./Uploaded_Faces/' + str(unique_id))
                save_image_path = './Uploaded_Faces/' + str(unique_id) + '/' + img_file.name
                with open(save_image_path, "wb") as f:
                    f.write(img_file.getbuffer())
                user_img = Image.open(save_image_path)
                user_img = user_img.resize((250, 250))
                st.image(user_img)
                st.success("Successfully Data uploaded for the {}".format(user_name))
            else:
                st.error("{} is already exists".format(unique_id))
        else:
            st.warning("Please fill required details!!")

    elif choice == activities[1]:
        st.title("Face Recognition")
        st.markdown('''<h5 style='text-align: left; color: #d73b5c;'>* Make sure you have given your Face Data before 
        recognising."</h5>''',
                    unsafe_allow_html=True)
        reco_img_file = st.file_uploader("Choose an Image", type=['jpg', 'png'])
        if reco_img_file is not None:
            save_image_path = './Uploaded_Unknown_Faces/' + reco_img_file.name
            with open(save_image_path, "wb") as f:
                f.write(reco_img_file.getbuffer())
            found_faces, found_ids = Recognise_Face(save_image_path)
            print(found_faces, found_ids)
            user_img = Image.open('./Processed_Result/result.jpg')
            user_img = user_img.resize((350, 350))
            st.image(user_img)
            pc = 1
            # Data insert
            insert_sql = """insert into FACE_ATTENDANCE values (null,?,?,?,?,?,?)"""
            # Insert into table
            ts = time.time()
            cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
            timestamp = str(cur_date + '_' + cur_time)
            for i in range(len(found_faces)):
                st.write(pc, "{} found in this Image".format(found_faces[i]))
                data_val = (reco_img_file.name, str(found_ids[i]), found_faces[i], '23', '72', timestamp)
                cursor.execute(insert_sql, data_val)
                pc += 1
            connection.commit()
            # else:
            #     st.error("NO Faces Found")
    elif choice == activities[2]:
        st.title("Welcome to the Admin Side")
        st.markdown(
            '''<h5 style='text-align: left; color: #d73b5c;'>* Here you can manage the Registered Facial Data"</h5>''',
            unsafe_allow_html=True)
        st.sidebar.warning('ID / Password Required!')

        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'spidy20' and ad_password == 'kushal123':
                st.subheader("Registered Faces are: {}".format(len(av_ids)))
                col1, col2 = st.columns([7, 5])
                count = 1
                av_ids.sort()
                for i in range(len(av_ids)):
                    find_query = "select * from REGISTERED_FACES where ID=" + str(av_ids[i]) + ';'
                    cursor.execute(find_query)
                    find_data = list(cursor.fetchall()[0])
                    print(find_data)
                    with col1:
                        st.subheader("({}) Name: {}".format(count,find_data[1]))
                        st.write("Unique ID is: {}".format(av_ids[i]))
                        for image in os.listdir('./Uploaded_Faces/'+str(av_ids[i])):
                            img = Image.open('./Uploaded_Faces/'+str(av_ids[i])+'/'+image)
                            img = img.resize((125,125))
                            st.image(img)
                        count+=1
                cursor.execute("select * from FACE_ATTENDANCE;")
                full_data = cursor.fetchall()
                st.subheader("**User's Attendance**")
                df = pd.DataFrame(full_data, columns=['ID', 'Image Name', 'Face ID', 'Name', 'Longitude', 'Latitude','Timestamp'])
                st.dataframe(df)

            else:
                st.error("Wrong ID & Password Provided")

    connection.close()
run()
