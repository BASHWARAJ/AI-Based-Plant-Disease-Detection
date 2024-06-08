import os

from collections.abc import MutableMapping
import pyrebase
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from flask import Flask, redirect, render_template, request, session, url_for
from PIL import Image
import torchvision.transforms.functional as TF
import CNN
import numpy as np
import torch
import pandas as pd

#import firebase_admin
#from firebase_admin import credentials, db

# Initialize Firebase Admin SDK
#cred = credentials.Certificate('path/to/serviceAccountKey.json')
#irebase_admin.initialize_app(cred, {
 #   'databaseURL': 'https://your-project-id.firebaseio.com/'
#})

# Load disease and supplement information
disease_info = pd.read_csv('C:/Users/sagar/Desktop/PROJBACKUP/Flask Deployed App/disease_info.csv' , encoding='cp1252')
supplement_info = pd.read_csv('C:/Users/sagar/Desktop/PROJBACKUP/Flask Deployed App/supplement_info.csv',encoding='cp1252')

# Load the CNN model
model = CNN.CNN(39)
model.load_state_dict(torch.load("C:/Users/sagar/Desktop/PROJBACKUP/Flask Deployed App/plant_disease_model_1_latest.pt"))
model.eval()

# Function to perform prediction using the model
def prediction(image_path: str) -> int:
    file_path = os.path.join("C:/Users/sagar/Desktop/PROJBACKUP/test_images", image_path)
    image = Image.open(file_path)
    image = image.resize((224, 224))
    input_data = TF.to_tensor(image)
    input_data = input_data.view((-1, 3, 224, 224))
    output = model(input_data)
    output = output.detach().numpy()
    index = np.argmax(output)
    return index

# Create Flask app instance
app = Flask(__name__)
app.secret_key = 'Jj\xab\x9b,\x10y\xd5y\x81\x86\xf0\xa6\xa8\\f\x08\x93\x12\xed\x8c\xde\x9b\xc0'

Config = {
     "apiKey": "AIzaSyDiUvaL4NwGb9D-piQUFjiKhRKUxBtjPhU",
    "authDomain": "farmmassist-fdcc2.firebaseapp.com",
    "databaseURL": "https://farmmassist-fdcc2-default-rtdb.firebaseio.com",
    "projectId": "farmmassist-fdcc2",
    "storageBucket": "farmmassist-fdcc2.appspot.com",
    "messagingSenderId": "926679513077",
    "appId": "1:926679513077:web:f436c902fbe1fecf1312bc",
    "measurementId": "G-Z4SD30W9M5"
    
  };



#initialize firebase
firebase = pyrebase.initialize_app(Config)
auth = firebase.auth()
db = firebase.database()

#Initialze person as dictionary
person = {"is_logged_in": False, "name": "", "email": "", "uid": ""}

@app.route('/')
def login():
    return render_template('login.html')

@app.route("/result", methods = ["POST", "GET"])
def result():
    if request.method == "POST":        #Only if data has been posted
        result = request.form           #Get the data
        email = result["email"]
        password = result["pass"]
        try:
            #Try signing in the user with the given information
            user = auth.sign_in_with_email_and_password(email, password)
            #Insert the user data in the global person
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            #Get the name of the user
            data = db.child("users").get()
            person["name"] = data.val()[person["uid"]]["name"]
            #Redirect to welcome page
            return redirect(url_for('home'))
        except:
            #If there is any error, redirect back to login
            return redirect(url_for('login'))
    else:
        if person["is_logged_in"] == True:
            return redirect(url_for('home'))
        else:
            return redirect(url_for('login'))

#Sign up/ Register
@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":        #Only listen to POST
        result = request.form           #Get the data submitted
        email = result["email"]
        password = result["pass"]
        name = result["name"]
        try:
            #Try creating the user account using the provided data
            auth.create_user_with_email_and_password(email, password)
            #Login the user
            user = auth.sign_in_with_email_and_password(email, password)
            #Add data to global person
            global person
            person["is_logged_in"] = True
            person["email"] = user["email"]
            person["uid"] = user["localId"]
            person["name"] = name
            #Append data to the firebase realtime database
            data = {"name": name, "email": email}
            db.child("users").child(person["uid"]).set(data)
            #Go to welcome page
            return redirect(url_for('home'))
        except:
            #If there is any error, redirect to register
            return redirect(url_for('signup'))

    else:
        if person["is_logged_in"] == True:
            return redirect(url_for('home'))
        else:
            return redirect(url_for('signup'))
        

@app.route('/logout')
def logout():
    # Clear the user session by resetting the 'person' dictionary
    person["is_logged_in"] = False
    person["name"] = ""
    person["email"] = ""
    person["uid"] = ""
    
    # Redirect the user to the login page
    return render_template('login.html')

@app.route('/forgot-password')
def forgot_password():
    return render_template("forgot-password.html")

@app.route('/contact')
def contact():
    return render_template('contact-us.html')

@app.route('/index')
def ai_engine_page():
    return render_template('index.html')

@app.route('/home')
def home():
        if person["is_logged_in"] == True:
            return render_template('home.html')
        else:
            return redirect(url_for('login'))
    

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        image = request.files['image']
        filename = "test_image"
        file_path = os.path.join('C:/Users/sagar/Desktop/PROJBACKUP/test_images', filename)
        image.save(file_path)

        pred = prediction(filename)
        title = disease_info['disease_name'][pred]
        description = disease_info['description'][pred]
        prevent = disease_info['Possible Steps'][pred]
        image_url = disease_info['image_url'][pred]
        supplement_name = supplement_info['supplement name'][pred]
        supplement_image_url = supplement_info['supplement image'][pred]
        supplement_buy_link = supplement_info['buy link'][pred]
        
        return render_template('submit.html', title=title, desc=description, prevent=prevent, 
                               image_url=image_url, pred=pred, sname=supplement_name, 
                               simage=supplement_image_url, buy_link=supplement_buy_link)

@app.route('/market', methods=['GET', 'POST'])
def market():
    return render_template('market.html', supplement_image=list(supplement_info['supplement image']),
                           supplement_name=list(supplement_info['supplement name']), 
                           disease=list(disease_info['disease_name']), buy=list(supplement_info['buy link']))

if __name__ == '__main__':
    app.run(debug=True)