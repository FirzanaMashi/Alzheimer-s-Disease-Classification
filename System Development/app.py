import base64
from datetime import timedelta
from flask import Flask, render_template, request, redirect, send_file, url_for, session, jsonify
from datetime import datetime, date, timedelta
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from tensorflow import keras
from PIL import Image
import numpy as np
import cv2
import os


app = Flask(__name__)

app.permanent_session_lifetime = timedelta(minutes=240)

app.secret_key = 'ADRad'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123'
app.config['MYSQL_DB'] = 'adrad'

mysql = MySQL(app)

#Login
@app.route('/', methods=['GET', 'POST'])
def login():

    errormessage = ''
    
    #Check existing account
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:

        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM radiologist WHERE BINARY username = %s AND BINARY password = %s', (username, password,))
        acc = cursor.fetchone()

        if acc:
            session['logins'] = True
            session['radID'] = acc['radID']
            session['fullname'] = acc['fullname']
            session['username'] = acc['username']

            return redirect(url_for('home'))
        else:
            errormessage = 'Incorrect username or password! Kindly enter registered username or password.'


    return render_template('index.html', errormessage=errormessage)

#Logout
@app.route('/logout')
def logout():
    #Remove session
    session.pop('logins', None)
    session.pop('radID', None)
    session.pop('fullname', None)
    session.pop('username', None)
    session.pop('email', None)

    return redirect(url_for('login'))

#Signup 
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    errormessage = ''

    if request.method == 'POST' and 'fullname' in request.form \
        and 'username' in request.form \
        and 'email' in request.form \
        and 'password' in request.form \
        and 'cpassword' in request.form:

        #Get data
        fullname = request.form['fullname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cpassword = request.form['cpassword']

        #Check existing account
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM radiologist WHERE email = %s', (email,))
        accemail = cursor.fetchone()

        cursor.execute('SELECT * FROM radiologist WHERE username = %s', (username,))
        accusername = cursor.fetchone()

        passpattern = re.compile(r'^(?=.*[A-Za-z\d])(?=.*[!@#$%^&*()_+={}\[\]:;<>,.?~\\-]).{8,}$')

        if accemail: 
            errormessage = 'The account using this email has existed! Enter new email!'
        elif accusername:
            errormessage = 'The account using this username already exists. Enter new username!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            errormessage = 'Invalid email address. Enter valid email address'
        elif not passpattern.match(password):
            errormessage = 'Password must be at least 8 characters long and contain at least one special character.'
        elif cpassword != password:
            errormessage = 'The confirmation password does not match!'
        else:
            cursor.execute(
                'INSERT INTO radiologist (fullname, username, email, password) ' 
                'VALUES (%s, %s, %s, %s)',
                (fullname, username, email, password,))
            mysql.connection.commit()
            errormessage = 'Your account have successfully registered.'

    elif request.method =='POST':
        errormessage = 'Please completely fill out the form.'

    return render_template('signup.html', errormessage=errormessage)

#Home/Dashboard
@app.route('/home')
def home():
    if 'logins' not in session:
        return redirect(url_for('login'))
    
    radID = session.get('radID')
    if radID is None:
        return "Your session is not exist."
    
    username = session.get('username')
    
    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT patient.patientID, patient.pfullName, patient.pAge, patient.pDOB, patient.pPhonenum, 
                           radiologist.fullname as radName 
                           FROM patient JOIN radiologist ON patient.radID = radiologist.radID 
                           ORDER BY patient.patientID DESC""")
    patients = cursor.fetchall()
    latestdata = patients[:5]

    #Non Demented cases count
    cursor.execute("""SELECT COUNT(a.adStages) FROM admri a
                    JOIN (SELECT patientID, MAX(mriID) AS latestmri FROM admri
                    GROUP BY patientID) 
                    b ON a.patientID = b.patientID AND a.mriID = b.latestmri
                    WHERE a.adStages = 'Normal'""")
    normres = cursor.fetchone()[0]

    #Very Mild Demented cases count
    cursor.execute("""SELECT COUNT(a.adStages) FROM admri a
                    JOIN (SELECT patientID, MAX(mriID) AS latestmri FROM admri
                    GROUP BY patientID) 
                    b ON a.patientID = b.patientID AND a.mriID = b.latestmri
                    WHERE a.adStages = 'Very Mild Demented'""")
    vmildres = cursor.fetchone()[0]

    #Mild Demented cases count
    cursor.execute("""SELECT COUNT(a.adStages) FROM admri a
                    JOIN (SELECT patientID, MAX(mriID) AS latestmri FROM admri
                    GROUP BY patientID) 
                    b ON a.patientID = b.patientID AND a.mriID = b.latestmri
                    WHERE a.adStages = 'Mild Demented'""")
    mildres = cursor.fetchone()[0]

    #Moderate demented cases count
    cursor.execute("""SELECT COUNT(a.adStages) FROM admri a
                    JOIN (SELECT patientID, MAX(mriID) AS latestmri FROM admri
                    GROUP BY patientID) 
                    b ON a.patientID = b.patientID AND a.mriID = b.latestmri
                    WHERE a.adStages = 'Moderate Demented'""")
    modres = cursor.fetchone()[0]

    #Count total cases patient
    cursor.execute("SELECT COUNT(*) FROM patient")
    totpatient = cursor.fetchone()[0]


    return render_template('home.html', latestdata=latestdata, username=username, normalc = normres, vmildc = vmildres, mildc = mildres, modc = modres, 
                           totpatient=totpatient)

#Fetch data for bar chart
@app.route('/barchart')
def barchart():
    cursor = mysql.connection.cursor()
    
    #Fetch counts for each Alzheimer's stage based on the gender and latest MRI result
    cursor.execute("""SELECT COUNT(a.adStages) AS femaleNormal
                        FROM admri a
                        JOIN (
                            SELECT patientID, MAX(mriID) AS latestmri
                            FROM admri
                            GROUP BY patientID
                        ) b ON a.patientID = b.patientID AND a.mriID = b.latestmri
                        JOIN patient p ON a.patientID = p.patientID
                        WHERE a.adStages = 'Normal' AND p.pGender = 'Female'""")
    normresf = cursor.fetchone()[0]

    cursor.execute("""SELECT COUNT(a.adStages) AS maleNormal
                        FROM admri a
                        JOIN (
                            SELECT patientID, MAX(mriID) AS latestmri
                            FROM admri
                            GROUP BY patientID
                        ) b ON a.patientID = b.patientID AND a.mriID = b.latestmri
                        JOIN patient p ON a.patientID = p.patientID
                        WHERE a.adStages = 'Normal' AND p.pGender = 'Male'""")

    normresm = cursor.fetchone()[0]

    cursor.execute("""SELECT COUNT(a.adStages) AS femaleVeryMild
                        FROM admri a
                        JOIN (
                            SELECT patientID, MAX(mriID) AS latestmri
                            FROM admri
                            GROUP BY patientID
                        ) b ON a.patientID = b.patientID AND a.mriID = b.latestmri
                        JOIN patient p ON a.patientID = p.patientID
                        WHERE a.adStages = 'Very Mild Demented' AND p.pGender = 'Female'""")
    vmildresf = cursor.fetchone()[0]

    cursor.execute("""SELECT COUNT(a.adStages) AS maleVeryMild
                        FROM admri a
                        JOIN (
                            SELECT patientID, MAX(mriID) AS latestmri
                            FROM admri
                            GROUP BY patientID
                        ) b ON a.patientID = b.patientID AND a.mriID = b.latestmri
                        JOIN patient p ON a.patientID = p.patientID
                        WHERE a.adStages = 'Very Mild Demented' AND p.pGender = 'Male'""")
    vmildresm = cursor.fetchone()[0]

    cursor.execute("""SELECT COUNT(a.adStages) AS female_normal_count
                        FROM admri a
                        JOIN (
                            SELECT patientID, MAX(mriID) AS latestmri
                            FROM admri
                            GROUP BY patientID
                        ) b ON a.patientID = b.patientID AND a.mriID = b.latestmri
                        JOIN patient p ON a.patientID = p.patientID
                        WHERE a.adStages = 'Mild Demented' AND p.pGender = 'Female'""")
    mildresf = cursor.fetchone()[0]

    cursor.execute("""SELECT COUNT(a.adStages) AS female_normal_count
                        FROM admri a
                        JOIN (
                            SELECT patientID, MAX(mriID) AS latestmri
                            FROM admri
                            GROUP BY patientID
                        ) b ON a.patientID = b.patientID AND a.mriID = b.latestmri
                        JOIN patient p ON a.patientID = p.patientID
                        WHERE a.adStages = 'Mild Demented' AND p.pGender = 'Male'""")
    mildresm = cursor.fetchone()[0]

    cursor.execute("""SELECT COUNT(a.adStages) AS female_normal_count
                        FROM admri a
                        JOIN (
                            SELECT patientID, MAX(mriID) AS latestmri
                            FROM admri
                            GROUP BY patientID
                        ) b ON a.patientID = b.patientID AND a.mriID = b.latestmri
                        JOIN patient p ON a.patientID = p.patientID
                        WHERE a.adStages = 'VModerate Demented' AND p.pGender = 'Female'""")
    modresf = cursor.fetchone()[0]

    cursor.execute("""SELECT COUNT(a.adStages) AS female_normal_count
                        FROM admri a
                        JOIN (
                            SELECT patientID, MAX(mriID) AS latestmri
                            FROM admri
                            GROUP BY patientID
                        ) b ON a.patientID = b.patientID AND a.mriID = b.latestmri
                        JOIN patient p ON a.patientID = p.patientID
                        WHERE a.adStages = 'Moderate Demented' AND p.pGender = 'Male'""")
    modresm = cursor.fetchone()[0]
    cursor.close()

    print(normresf, normresm, vmildresf, vmildresm, mildresf, mildresm, modresf, modresm)
    # Render the template with the data
    return jsonify(normresf=normresf, normresm=normresm, vmildresf=vmildresf, vmildresm=vmildresm,
                   mildresf=mildresf, mildresm=mildresm, modresf=modresf, modresm=modresm)
                        

#Register patient
@app.route('/regPatient', methods=['GET', 'POST'])
def regPatient():

    errormessage = ''
    form_data = {}

    if 'logins' not in session:
        return redirect(url_for('login'))
    
    radID = session['radID']
    
    if request.method == 'POST': 
        pFullname = request.form['pFullname']
        pIcnumber = request.form['pIcnumber']
        pAge = request.form['pAge']
        pGender = request.form['pGender']
        pPhonenum = request.form['pPhonenum']
        pDob = datetime.strptime(request.form['pDob'], '%Y-%m-%d').date()
        gfullname = request.form['gfullname']
        gphonenum = request.form['gphonenum']

        #Check whether the patiet's information existed
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM patient WHERE pIcnumber = %s', (pIcnumber,))
        pacc = cursor.fetchone()

        form_data = {
            'pFullname': request.form.get('pFullname', ''),
            'pIcnumber': request.form.get('pIcnumber', ''),
            'pAge': request.form.get('pAge', ''),
            'pGender': request.form.get('pGender', ''),  # Include other fields similarly
            'pPhonenum': request.form.get('pPhonenum', ''),
            'pDob': request.form.get('pDob', ''),
            'gfullname': request.form.get('gfullname', ''),
            'gphonenum': request.form.get('gphonenum', '')
        }

        if pacc:
            errormessage='This patient information existed in the database. Kindly enter new patient.'
        #Check if IC number is in a valid format
        elif '-' in pIcnumber or len(pIcnumber) != 12 or not pIcnumber.isdigit():
            errormessage = 'Invalid IC number format. Please enter a valid 12-digit IC number without dashes.'
        #Check if the selected date is not more than the current date
        elif pDob > date.today():
            errormessage = 'Selected date of birth is more than the current date. Please choose a valid date.'
        else:
            #Insert the new patient information
            cursor.execute(
                'INSERT INTO patient (pFullname, pIcnumber, pAge, pGender, pPhonenum, pDob, gfullname, gphonenum, radID)'
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', 
                (pFullname, pIcnumber, pAge, pGender, pPhonenum, pDob, gfullname, gphonenum, radID,))
            mysql.connection.commit()
            cursor.close()   
            
            return redirect(url_for('patientList'))
          
    elif request.method == 'POST':
        errormessage = 'Kindly fill all the required information before submitting the patient form.'
       
    return render_template('regPatient.html', errormessage=errormessage, form_data=form_data)

#Patient List
@app.route('/patientList', methods = ['POST','GET'])
def patientList():

    # Session
    if 'logins' not in session:
        return redirect(url_for('login'))
    
    radID = session.get('radID')
    if radID is None:
        return "Your session is not exist."
    

    cursor = mysql.connection.cursor()
    
    if request.method == 'POST':
        searchquery = request.form.get('searchP', '')

        #Search the patient by their name
        if searchquery:
            cursor.execute("""SELECT patient.patientID, patient.pfullName, patient.pDOB, patient.pAge, 
                           patient.pGender, patient.gfullname, 
                           radiologist.fullname as radName 
                           FROM patient JOIN radiologist ON patient.radID = radiologist.radID 
                           WHERE pFullname LIKE %s""", 
                           (f"%{searchquery}%",))
        else:
            cursor.execute("""SELECT patient.patientID, patient.pfullName, patient.pDOB, patient.pAge, 
                           patient.pGender, patient.gfullname, 
                           radiologist.fullname as radName 
                           FROM patient JOIN radiologist ON patient.radID = radiologist.radID""")
    else:
        cursor.execute("""SELECT patient.patientID, patient.pfullName, patient.pDOB, patient.pAge, 
                           patient.pGender, patient.gfullname, 
                           radiologist.fullname as radName 
                           FROM patient JOIN radiologist ON patient.radID = radiologist.radID""")
    
    
    patientList = cursor.fetchall()
    totalrec = len(patientList)


    # Calculation for pagination   
    perpage = 7
    page = request.args.get('page', 1, type=int)

    totalpages = -(-totalrec // perpage)
    start = (page - 1) * perpage
    end = start + perpage
    patientsonpage = patientList[start:end]

    cursor.close()

    print(patientList)
    
    return render_template('patientList.html', patientList = patientsonpage, page=page, totalpages = totalpages)

#Prediction
def prediction(imgpath):

    img = cv2.imread(imgpath)

    #Load the pre-trained model
    model_path = "ADModel22.keras"
    loaded_model = keras.models.load_model(model_path)

    #Convert image to grayscale
    grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    #Thresholding and erosion/dilation
    _, binaryimg = cv2.threshold(grayimg, 15, 255, cv2.THRESH_BINARY)
    kernel = np.ones((7, 7), np.uint8)
    binaryimg = cv2.morphologyEx(binaryimg, cv2.MORPH_OPEN, kernel)

    #Find contours and select the largest contour
    contours, _ = cv2.findContours(binaryimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largestcontour = max(contours, key=cv2.contourArea)

    #Find extreme points
    left = tuple(largestcontour[largestcontour[:, :, 0].argmin()][0])
    right = tuple(largestcontour[largestcontour[:, :, 0].argmax()][0])
    top = tuple(largestcontour[largestcontour[:, :, 1].argmin()][0])
    bottom = tuple(largestcontour[largestcontour[:, :, 1].argmax()][0])

    #Crop the image
    cropimg = img[top[1]:bottom[1], left[0]:right[0]]
    imgs = cv2.cvtColor(cropimg, cv2.COLOR_BGR2GRAY)

    #Apply median blur to reduce salt-pepper noise
    kernels = 3
    blurimg = cv2.medianBlur(imgs, kernels)

    #Apply CLAHE to enhance mri contrast
    clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8, 8))
    claheimg = clahe.apply(blurimg)

    #Resize image
    rszimg = cv2.resize(claheimg, (100,100))
    rsz_img = cv2.cvtColor(rszimg, cv2.COLOR_BGR2RGB)

    #Prepare image for prediction
    image_fromarray = Image.fromarray(rsz_img)
    expand_input = np.expand_dims(image_fromarray, axis=0)
    input_data = np.array(expand_input)
    input_data = input_data/255

    pred = loaded_model.predict(input_data)
    result = pred.argmax()
    if result == 0:
        result = "Normal"
    elif result == 1:
        result = "Very Mild Demented"
    elif result == 2:
        result = "Mild Demented"
    elif result == 3:
        result = "Moderate Demented"
    
    return result

#Upload Image
@app.route('/upload/<int:patientid>', methods=['GET', 'POST'])
def upload(patientid):

    if 'logins' not in session:
        return redirect(url_for('login'))
    
    radID = session.get('radID')
    if radID is None:
        return "Your session is not exist."
    
    session['patientId'] = patientid
    
    return render_template('upload.html')

#Result
@app.route('/result', methods=['GET', 'POST'])
def result():

    errormessage = ''

    if 'logins' not in session:
        return redirect(url_for('login'))
    
    radID = session.get('radID')
    if radID is None:
        return "Your session is not exist."
    
    result = None
    imgpath = None

    #Check if the uploaded file is a JPEG or PNG image
    ext = {'jpg', 'jpeg', 'png'}

    if request.method == 'POST':
        image = request.files['mriimg']

        if image and '.' in image.filename and image.filename.rsplit('.', 1)[1].lower() in ext:
            imgpath = "static/"+image.filename
            image.save(imgpath)
            
            result = prediction(imgpath)

            print("Session Patient ID:", session.get('patientId'))

            #Encode image to base64
            with open(imgpath, "rb") as image_file:
                cvtimg = base64.b64encode(image_file.read())

            #Automatically set the date when the MRI is uploaded
            patientid = session.get('patientId')
            scandate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO admri (scandate, adStages, mriImage, patientid) VALUES (%s, %s, %s, %s)", 
                        (scandate, result, cvtimg, patientid))
            
            cursor.execute("SELECT * FROM patient WHERE patientID = %s", (patientid,))
            patient = cursor.fetchone()
            
            mysql.connection.commit()
            cursor.close()
        else:
          errormessage = 'Invalid file format. Please upload a JPEG or PNG image.'  

    return render_template('result.html', prediction=result, img_path=imgpath, cvtimg = cvtimg, patient=patient, errormessage=errormessage)

#Patient Details
@app.route('/patientDetails/<int:patientid>', methods=['GET'])
def patientDetails(patientid):

    if 'logins' not in session:
        return redirect(url_for('login'))
    
    radID = session.get('radID')
    if radID is None:
        return "Your session is not exist."
    
    cursor = mysql.connection.cursor()

    #Retrieve patient
    cursor.execute("SELECT * FROM patient WHERE patientID = %s", (patientid,))
    patientdetails = cursor.fetchone()

    #Retrieve mri record
    cursor.execute("SELECT * FROM admri WHERE patientID = %s ORDER BY mriID DESC", (patientid,))
    mridata = cursor.fetchall()

    cursor.close()

    return render_template('patientDetails.html', patientdetails=patientdetails, mridata=mridata)

#Decode MRI Image
@app.route('/MRI/<int:image_id>', methods=['GET'])
def getMRI(image_id):

    cursor = mysql.connection.cursor()
    #Retrieve the encoding of MRI based on the MRI ID
    cursor.execute("SELECT mriImage FROM admri WHERE mriID = %s", (image_id,))
    data = cursor.fetchone()

    if data:
        #Decode the encoded image
        encoded_image = data[0]
        decoded_image = base64.b64decode(encoded_image)

        #Create the directory if it doesn't exist to save the backup image
        imgdir = 'static/images/'
        if not os.path.exists(imgdir):
            os.makedirs(imgdir)

        #Save the decoded image to a file
        imgpath = os.path.join(imgdir, f"MRI Image_{image_id}.jpeg")
        with open(imgpath, "wb") as image_file:
            image_file.write(decoded_image)

        #Return the image file
        return send_file(imgpath, mimetype='image/jpeg')
    else:
        return "Image not found", 404


if __name__ == "__main__":
    app.run(debug=True)

