import cv2
import tensorflow as tf
from tensorflow.keras.models import load_model
from flask import Flask, render_template, Response
import numpy as np
from pygame import mixer
from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint ('auth',__name__)



face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
model = load_model(r'C:\Users\Harsh Vardhan\Desktop\webapp\DrowsinessDetection.h5')


mixer.init()
sound= mixer.Sound(r'C:\Users\Harsh Vardhan\Desktop\webapp\alarm.wav')

def gen_frames():
    
    cap = cv2.VideoCapture(0)
    Score = 0

    while True:
        ret, frame = cap.read()
        height,width = frame.shape[0:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces= face_cascade.detectMultiScale(gray, scaleFactor= 1.2, minNeighbors=3)
        eyes= eye_cascade.detectMultiScale(gray, scaleFactor= 1.1, minNeighbors=1)

        cv2.rectangle(frame, (0,height-50),(200,height),(0,0,0),thickness=cv2.FILLED)

        for (x,y,w,h) in faces:
            cv2.rectangle(frame,pt1=(x,y),pt2=(x+w,y+h), color= (255,0,0), thickness=3 )
            
        for (ex,ey,ew,eh) in eyes:
            cv2.rectangle(frame,pt1=(ex,ey),pt2=(ex+ew,ey+eh), color= (255,0,0), thickness=3 )
            
            # preprocessing steps
            eye= frame[ey:ey+eh,ex:ex+ew]
            eye= cv2.resize(eye,(80,80))
            eye= eye/255
            eye= eye.reshape(80,80,3)
            eye= np.expand_dims(eye,axis=0)
            # preprocessing is done now model prediction
            prediction = model.predict(eye)
            
            # if eyes are closed
            if prediction[0][0]>0.50:
                cv2.putText(frame,'closed',(10,height-20),fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,fontScale=1,color=(255,255,255),
                            thickness=1,lineType=cv2.LINE_AA)
                cv2.putText(frame,'Score'+str(Score),(100,height-20),fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,fontScale=1,color=(255,255,255),
                            thickness=1,lineType=cv2.LINE_AA)
                Score=Score+1
                if(Score>3):
                    try:
                        sound.play()
                    except:
                        pass
                
            # if eyes are open
            elif prediction[0][1]>0.50:
                cv2.putText(frame,'open',(10,height-20),fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,fontScale=1,color=(255,255,255),
                            thickness=1,lineType=cv2.LINE_AA)      
                cv2.putText(frame,'Score'+str(Score),(100,height-20),fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,fontScale=1,color=(255,255,255),
                            thickness=1,lineType=cv2.LINE_AA)
                Score = Score-1
                if (Score<0):
                    Score=0
                
            
        # cv2.imshow('frame',frame)
        # if cv2.waitKey(33) & 0xFF==ord('q'):
        #     break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield the encoded frame as bytes
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        
        
        
@auth.route('/', methods= ['GET','POST'])
def Login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email = email).first()
        if user:
            if user.password == password:
                flash("Logged In",category='success')
                login_user(user, remember=True)
                return render_template("index.html", user = current_user)
            else:
                flash("Incorrect password", category='error')
        else:
            flash("User don\'t exist", category='error')

    return render_template("login.html", user = current_user)


@auth.route('/logout')
@login_required
def Logout():
    logout_user()
    return redirect(url_for('auth.Login'))

@auth.route('/signup', methods = ['get','post'])
def Signup():
    if request.method == "POST":
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')

        user = User.query.filter_by(email = email).first()
        if user:
            flash("Email already exists", category='error')
        elif len(email) < 4:
            flash("Email length error", category= 'error')
        elif len(password) < 5:
            flash("Password is too short", category='error')
        else:
            new_user = User(email = email, name = name, password = password)
            db.session.add(new_user)
            db.session.commit()
            flash("Account successfully created", category='success')
            # login_user(new_user, remember=True)
            return redirect(url_for('auth.Login')) 


    return render_template("signup.html", user = current_user)    



@auth.route('/contact')
@login_required
def contact():
    return render_template('contact.html', user = current_user)


@auth.route('/home')
@login_required
def index():
    return render_template('index.html', user = current_user)
@auth.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
