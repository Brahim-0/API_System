import os
import secrets

from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, jsonify, make_response, send_from_directory
from APISystem import app, db, bcrypt, mail
from APISystem.APIkeys_operations import remove_key_function, generate_key_function
from APISystem.forms import (RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm)
from APISystem.models import User, Key, DataKey, RequestsKey
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


from APISystem.premium_access import validate_key, premium_access


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    return render_template('home.html')


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


def send_reset_email(user):
    token = user.get_reset_token()
    print(url_for('reset_token', token=token, _external=True))
    msg = Message('Password Reset Request',
                  sender='admin@example.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
    {url_for('reset_token', token=token, _external=True)}

    If you did not make this request then simply ignore this email and no changes will be made.'''

    #mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@app.route("/apikey", methods=['GET', 'POST'])
@login_required
def apikey():
    temp = Key.query.filter_by(user_email=current_user.email)
    free_keys = []
    data_premium_keys = []
    requests_premium_keys = []
    data_premium_keys_consumed = []
    requests_premium_keys_consumed = []
    for t in temp:
        if not validate_key(t.token):
            remove_key_function(t.token)
        if t.subscription == "premium-data":
            data_premium_keys.append(t.token)
            k = DataKey.query.filter_by(token=t.token).first()
            data_premium_keys_consumed.append(k.consumed)
        elif t.subscription == "premium-requests":
            requests_premium_keys.append(t.token)
            k = RequestsKey.query.filter_by(token=t.token).first()
            requests_premium_keys_consumed.append(k.consumed)
        else:
            free_keys.append(t.token)

    full = True if (len(free_keys) + len(data_premium_keys) + len(requests_premium_keys)) == app.config['accounts_limit'] else False
    empty = True if (len(free_keys) + len(data_premium_keys) + len(requests_premium_keys)) == 0 else False
    return render_template('apikey.html', title='API key', free_keys=free_keys, data_premium_keys=data_premium_keys, requests_premium_keys=requests_premium_keys, data_premium_keys_consumed=data_premium_keys_consumed, full=full,
                           requests_premium_keys_consumed=requests_premium_keys_consumed, empty=empty, bandwidth_limit=app.config['bandwidth_limit'],requests_limit=app.config['requests_limit'] )


@app.route("/generate_key/<subscription>")
@login_required
def generate_key(subscription):
    number_of_keys = Key.query.filter_by(user_email=current_user.email).count()
    if number_of_keys >= app.config['accounts_limit']:
        abort(403)
    else:
        generate_key_function(subscription=subscription)
        return redirect(url_for('apikey'))


@app.route("/remove_key/<key>", methods=['GET', 'POST'])
@login_required
def remove_key(key):
    remove_key_function(key)
    return redirect(url_for('apikey'))


@app.route("/text/<key>", methods=['GET', 'POST'])
@premium_access
def text(key):

    response = make_response(
            jsonify(msg="1"),
            200,
        )
    response.headers["Content-Type"] = "application/json"

    return response


@app.route("/img/<key>", methods=['GET', 'POST'])
@premium_access
def img(key):
    response = make_response(
        send_from_directory("static/profile_pics", "2e32b4c96a8d8f10.jpg", as_attachment=False),
        200,
    )
    response.headers["Content-Type"] = "application/json"
    return response




