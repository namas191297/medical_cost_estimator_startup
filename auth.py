# auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User
from . import db
from flask import Flask, render_template, request, redirect, url_for
import stripe
import numpy as np
from sklearn import *
import pickle

app = Flask(__name__)

pub_key = 'pk_test_dDaNUE1Nb54dE3sfxA9rL8CY00twdlA3VM'
secret_key = 'sk_test_OPnayGdSE77JC1qarpbAGlIP00MCMkorTa'

stripe.api_key = secret_key

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password): 
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login')) # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('main.profile'))

@auth.route('/profile')
@login_required
def index():
    return render_template('profile.html', pub_key=pub_key)

@auth.route('/thanks')
@login_required
def thanks():
    return render_template('thanks.html', result="")

@auth.route('/pay', methods=['POST'])
def pay():

    customer = stripe.Customer.create(email=request.form['stripeEmail'], source=request.form['stripeToken'])

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=150,
        currency='usd',
        description='The Product'
    )

    return redirect(url_for('auth.thanks'))

if __name__ == '__main__':
    auth.run(debug=True)

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['POST'])
def signup_post():

    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again  
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

@auth.route('/estimate', methods=['POST'])
def estimate():
    firstName = request.form['fname']
    lastName = request.form['lname']
    age = float(request.form['age'])
    sex = float(request.form['sex'])
    bmi = float(request.form['bmi'])
    children = float(request.form['children'])
    smoker = float(request.form['smoking'])

    model = pickle.load(open('model/final_model.sav', 'rb'))
    predict_input = [age, sex, bmi, children, smoker]
    predict_input = np.array(predict_input)
    predict_input = predict_input.reshape(-1,5)
    prediction = np.round(model.predict(predict_input)[0],2)
    resultstr = f"{firstName}'s estimated cost is ${prediction} !"

    return render_template('thanks.html', result=resultstr)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))



   