import streamlit as st
import os
from PIL import Image
import sqlite3
import time, datetime
import pandas as pd
import base64, shutil
from io import BytesIO
from pathlib import Path
import face_recognition
import cv2

# Create necessary directories
Path("./Processed_Result").mkdir(exist_ok=True)
Path("./Uploaded_Unknown_Faces").mkdir(exist_ok=True)
Path("./Uploaded_Faces").mkdir(exist_ok=True)
Path("./Tmp_Faces").mkdir(exist_ok=True)
# Making a connection with database
connection = sqlite3.connect("face_recognition.db")
cursor = connection.cursor()

KNOWN_FACES_DIR = 'Uploaded_Faces'
TOLERANCE = 0.5
FRAME_THICKNESS = 3
FONT_THICKNESS = 2
MODEL = 'cnn'  # default: 'hog', other one can be 'cnn' - CUDA accelerated (if available) deep-learning pretrained model


# Returns (R, G, B) from name
def name_to_color(name):
    # Take 3 first letters, tolower()
    # lowercased character ord() value rage is 97 to 122, substract 97, multiply by 8
    color = [(ord(c.lower()) - 97) * 8 for c in name[:3]]
    return color


# Remove dir or files
def remove_file_or_dir(path: str) -> None:
    """ Remove a file or directory """
    try:
        shutil.rmtree(path)
    except NotADirectoryError:
        os.remove(path)


# Storing Face & Name
known_faces = []
known_names = []
attendance = []


# Now let's loop over a folder of faces we want to label
def Recognise_Face(face_image):
    for name in os.listdir(KNOWN_FACES_DIR):

        # Next we load every file of faces of known person
        for filename in os.listdir(f'{KNOWN_FACES_DIR}/{name}'):
            # Load an image
            image = face_recognition.load_image_file(f'{KNOWN_FACES_DIR}/{name}/{filename}')

            # Get 128-dimension face encoding
            # Always returns a list of found faces, for this purpose we take first face only (assuming one face per image as you can't be twice on one image)
            encoding = face_recognition.face_encodings(image)[0]

            # Append encodings and name
            known_faces.append(encoding)
            known_names.append(name)

    print("Status: Recognising....")
    found_faces = []
    found_ids = []
    # Load image
    image = face_recognition.load_image_file(face_image)

    # This time we first grab face locations - we'll need them to draw boxes
    locations = face_recognition.face_locations(image, model=MODEL)
    encodings = face_recognition.face_encodings(image, locations)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # But this time we assume that there might be more faces in an image - we can find faces of dirrerent people
    for face_encoding, face_location in zip(encodings, locations):
        print("Status: Find Face Encodings....")

        # Returns array of True/False values in order of passed known_faces
        results = face_recognition.compare_faces(known_faces, face_encoding, TOLERANCE)

        # Since order is being preserved, we check if any face was found then grab index

        match = None
        if True in results:

            # If at least one is true, get a name of first of found labels
            match = known_names[results.index(True)]
            if match not in found_ids:
                # Each location contains positions in order: top, right, bottom, left
                top_left = (face_location[3], face_location[0])
                bottom_right = (face_location[1], face_location[2])

                # Found name of ID from the database
                found_ids.append(match)
                find_query = "select * from REGISTERED_FACES where ID=" + str(match) + ';'
                cursor.execute(find_query)
                find_data = list(cursor.fetchall()[0])

                # Giving the random color
                color = name_to_color(find_data[1])

                # Paint frame
                cv2.rectangle(image, top_left, bottom_right, color, FRAME_THICKNESS)

                # Now we need smaller, filled grame below for a name
                # This time we use bottom in both corners - to start from bottom and move 50 pixels down
                top_left = (face_location[3], face_location[2])
                bottom_right = (face_location[1], face_location[2] + 22)

                # Paint frame
                found_faces = set(found_faces)
                found_ids = set(found_ids)
                found_faces = list(found_faces)
                found_ids = list(found_ids)

                cv2.rectangle(image, top_left, bottom_right, color, cv2.FILLED)
                cv2.putText(image, find_data[1], (face_location[3] + 10, face_location[2] + 15),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (200, 200, 200), FONT_THICKNESS)
                found_faces.append(find_data[1])
                print("Status: Recognising {}....".format(find_data[1]))

    # Writing the result
    cv2.imwrite('./Processed_Result/result.jpg', image)
    return found_faces, found_ids


# Create Data store table
data_table_sql = '''CREATE TABLE IF NOT EXISTS REGISTERED_FACES
                    (ID varchar(15) NOT NULL,
                    Name varchar(100) NOT NULL,
                    PRIMARY KEY (ID));
'''
cursor.execute(data_table_sql)
connection.commit()


# To get data from the database
def find_all_data(column):
    find_query = "select " + column + " from REGISTERED_FACES;"
    cursor.execute(find_query)
    find_d = list(cursor.fetchall())
    all_name = []
    for i in find_d:
        all_name.append(i[0])
    return all_name


# Generate download link
def get_image_download_link(img, filename, text):
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/jpg;base64,{img_str}" download="{filename}">{text}</a>'
    return href


# Generate Attendance CSV
def get_table_download_link(df,filename,text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


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
            with open('./Tmp_Faces/'+img_file.name, "wb") as f:
                f.write(img_file.getbuffer())
            found_f, found_i = Recognise_Face('./Tmp_Faces/'+img_file.name)
            if found_f:
                st.error("Failure !! This Face is matching with the {}({}).".format(found_f[0],found_i[0]))
                os.remove('./Tmp_Faces/' + img_file.name)
            else:
                if str(unique_id) not in av_ids:
                    # Data insert
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
            if found_faces:
                user_img = Image.open('./Processed_Result/result.jpg')
                user_img = user_img.resize((350, 350))
                st.image(user_img)
                # Download Result
                result = Image.open('./Processed_Result/result.jpg')
                st.markdown(get_image_download_link(result, reco_img_file.name, 'Download Result'),
                            unsafe_allow_html=True)
                pc = 1
                # Data insert
                insert_sql = """insert into FACE_ATTENDANCE values (null,?,?,?,?,?,?)"""
                # Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)
                # for i in range(len(found_faces)):
                #     st.write(pc, "{} found in this Image".format(found_faces[i]))
                #     data_val = (reco_img_file.name, str(found_ids[i]), found_faces[i], '23', '72', timestamp)
                #     cursor.execute(insert_sql, data_val)
                #     pc += 1
                all_names = find_all_data('Name')
                all_ids = find_all_data('ID')
                present_count = 0
                for i in range(len(all_names)):
                    tmp = [all_ids[i], all_names[i], '23', '72']
                    if all_ids[i] in found_ids:
                        tmp.append('Present')
                        tmp.append(timestamp)
                        tmp.append(reco_img_file.name)
                        present_count+=1
                    else:
                        tmp.append("Absent")
                        tmp.append('')
                        tmp.append('')
                    attendance.append(tmp)
                full_attendance = pd.DataFrame(attendance,columns=['Unique ID','Name', 'Latitude', 'Longitude', 'Status', 'Timestamp','Uploaded Image'])
                st.subheader("✅ Attendance Report")
                att_percentage = present_count * 100 // len(all_names)
                st.success("Total: {} Students, Present: {}".format(len(all_names),present_count))
                st.info("Total Attendance is: {}%".format(att_percentage))
                st.subheader("Full Attendance📝")
                st.dataframe(full_attendance)
                st.markdown(get_table_download_link(full_attendance,'Attendance_{}.csv'.format(timestamp) ,'Download Attendance'), unsafe_allow_html=True)
                connection.commit()
            else:
                st.info("No Recognise Faces found, please give your face data or regresh the page.")
    elif choice == activities[2]:
        st.title("Welcome to the Admin Side")
        st.markdown(
            '''<h5 style='text-align: left; color: #d73b5c;'>* Here you can manage the Registered Facial Data"</h5>''',
            unsafe_allow_html=True)
        st.sidebar.warning('ID / Password Required!')

        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'ADMIN' and ad_password == 'ADMIN':
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
                        st.subheader("({}) Name: {}".format(count, find_data[1]))
                        st.write("Unique ID is: {}".format(av_ids[i]))
                        for image in os.listdir('./Uploaded_Faces/' + str(av_ids[i])):
                            img = Image.open('./Uploaded_Faces/' + str(av_ids[i]) + '/' + image)
                            img = img.resize((125, 125))
                            st.image(img)
                        count += 1
                # cursor.execute("select * from FACE_ATTENDANCE;")
                # full_data = cursor.fetchall()
                # st.subheader("**User's Attendance**")
                # df = pd.DataFrame(full_data,
                #                   columns=['ID', 'Image Name', 'Face ID', 'Name', 'Longitude', 'Latitude', 'Timestamp'])
                # if df.empty:
                #     pass
                # else:
                #     st.dataframe(df)
                #     st.markdown(get_table_download_link(df, 'Attendance.csv', 'Download Attendance'),
                #                 unsafe_allow_html=True)
            else:
                st.error("Wrong ID & Password Provided")
        st.warning("Reset system will delete all the stored data of faces & Attendance")
        if st.button("Reset System"):
            try:
                if ad_user == 'ADMIN' and ad_password == 'ADMIN':
                    remove_file_or_dir('Processed_Result')
                    remove_file_or_dir('Uploaded_Faces')
                    remove_file_or_dir('Uploaded_Unknown_Faces')
                    remove_file_or_dir('Tmp_Faces')
                    remove_file_or_dir('face_recognition.db')
                    st.success("Successfully Reset!")
                    st.info("Please refresh the page to get in working.")
                else:
                    st.error("Wrong ID & Password Provided")
            except Exception as e:
                print(e)
                st.error("Error: can't able to reset system.")

    connection.close()


run()
