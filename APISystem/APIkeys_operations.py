import string
from random import choice

from flask_login import current_user

from APISystem import db
from APISystem.models import User, Key, DataKey, RequestsKey


def remove_key_function(key):
    Key.query.filter_by(token=key).delete()
    try:
        DataKey.query.filter_by(token=key).delete()
    except:
        print("Error when deleting token from DataKey table.")
    try:
        RequestsKey.query.filter_by(token=key).delete()
    except:
        print("Error when deleting token from RequestsKey table.")

    db.session.commit()


def generate_key_function(subscription, size=120, chars=string.ascii_letters + string.digits):
    generated_key = ''.join(choice(chars) for _ in range(size))
    while Key.query.filter_by(token=generated_key).count():
        generated_key = ''.join(choice(chars) for _ in range(size))

    if subscription == "free" or subscription == "premium-data" or subscription == "premium-requests":

        k = Key(token=generated_key, user_email=current_user.email, subscription=subscription)
        db.session.add(k)
        db.session.commit()

        if subscription == "premium-data":
            print("in")
            d = DataKey(token=generated_key)
            db.session.add(d)
            db.session.commit()

        if subscription == "premium-requests":
            r = RequestsKey(token=generated_key)
            db.session.add(r)
            db.session.commit()

    return generated_key
