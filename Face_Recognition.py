import face_recognition
import os
import cv2
import sqlite3
print(os.getcwd())

KNOWN_FACES_DIR = '/Uploaded_Faces'
TOLERANCE = 0.5
FRAME_THICKNESS = 3
FONT_THICKNESS = 2
MODEL = 'cnn'  # default: 'hog', other one can be 'cnn' - CUDA accelerated (if available) deep-learning pretrained model

connection = sqlite3.connect("/face_recognition.db")
cursor = connection.cursor()


# Returns (R, G, B) from name
def name_to_color(name):
    # Take 3 first letters, tolower()
    # lowercased character ord() value rage is 97 to 122, substract 97, multiply by 8
    color = [(ord(c.lower()) - 97) * 8 for c in name[:3]]
    return color


known_faces = []
known_names = []

# We oranize known faces as subfolders of KNOWN_FACES_DIR
# Each subfolder's name becomes our label (name)
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


# Now let's loop over a folder of faces we want to label
def Recognise_Face(face_image):
    found_faces = []
    found_ids = []
    # Load image
    image = face_recognition.load_image_file(face_image)

    # This time we first grab face locations - we'll need them to draw boxes
    locations = face_recognition.face_locations(image, model=MODEL)

    # Now since we know loctions, we can pass them to face_encodings as second argument
    # Without that it will search for faces once again slowing down whole process
    encodings = face_recognition.face_encodings(image, locations)

    # We passed our image through face_locations and face_encodings, so we can modify it
    # First we need to convert it from RGB to BGR as we are going to work with cv2
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # But this time we assume that there might be more faces in an image - we can find faces of dirrerent people
    for face_encoding, face_location in zip(encodings, locations):

        # We use compare_faces (but might use face_distance as well)
        # Returns array of True/False values in order of passed known_faces
        results = face_recognition.compare_faces(known_faces, face_encoding, TOLERANCE)

        # Since order is being preserved, we check if any face was found then grab index
        # then label (name) of first matching known face withing a tolerance

        match = None
        if True in results:  # If at least one is true, get a name of first of found labels
            match = known_names[results.index(True)]
            # Each location contains positions in order: top, right, bottom, left
            top_left = (face_location[3], face_location[0])
            bottom_right = (face_location[1], face_location[2])

            # Get color by name using our fancy function
            # Wite a name
            found_ids.append(match)
            find_query = "select * from REGISTERED_FACES where ID=" + str(match) + ';'
            cursor.execute(find_query)
            find_data = list(cursor.fetchall()[0])

            color = name_to_color(find_data[1])

            # Paint frame
            cv2.rectangle(image, top_left, bottom_right, color, FRAME_THICKNESS)

            # Now we need smaller, filled grame below for a name
            # This time we use bottom in both corners - to start from bottom and move 50 pixels down
            top_left = (face_location[3], face_location[2])
            bottom_right = (face_location[1], face_location[2] + 22)

            # Paint frame
            cv2.rectangle(image, top_left, bottom_right, color, cv2.FILLED)

            cv2.putText(image, find_data[1], (face_location[3] + 10, face_location[2] + 15), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (200, 200, 200), FONT_THICKNESS)
            found_faces.append(find_data[1])

    # Show image
    # cv2.imshow(filename, image)
    cv2.imwrite('/Processed_Result/result.jpg', image)
    return found_faces, found_ids
    # cv2.waitKey(0)
    # cv2.destroyWindow(filename)
