import datetime

from flask import make_response, jsonify

from APISystem import db, app
from APISystem.APIkeys_operations import remove_key_function
from APISystem.models import User, Key, DataKey, RequestsKey


# Return True if the key is valid and False otherwise
def validate_key(key):  # check: expire_date.
    key = Key.query.filter_by(token=key).first()
    if key is None:
        return False
    if key.expire_date < datetime.datetime.now():
        remove_key_function(key.token)
        return False
    else:
        return True


# Return True if the key is premium and False otherwise
def validate_premium_key(key):
    k = Key.query.filter_by(token=key).first()
    if k is None:
        return False
    if k.subscription == "premium-data" or k.subscription == "premium-requests":
        if k.subscription == "premium-data":
            k = DataKey.query.filter_by(token=key).first()
            if k.consumed < app.config['bandwidth_limit']:
                return True
            else:
                return False

        if k.subscription == "premium-requests":
            k = RequestsKey.query.filter_by(token=key).first()
            if k.consumed < app.config['requests_limit']:
                return True
            else:
                return False

    else:
        return False


# increment the data or requests counter
def increment_counter(key, response):
    s = Key.query.filter_by(token=key).first().subscription
    if s == "premium-data":
        k = DataKey.query.filter_by(token=key).first()
        print(k.consumed)
        k.consumed = round(response.content_length / 1000000, 2) + k.consumed
        print(k.consumed)
        db.session.add(k)
        db.session.commit()
    elif s == "premium-requests":
        k = RequestsKey.query.filter_by(token=key).first()
        print(k.consumed)
        k.consumed = k.consumed + 1
        print(k.consumed)
        db.session.add(k)
        db.session.commit()
    else:
        print("Subscription type not recognized. No incrementation took place.")


def premium_access(
        end_point_func):  # annotation to decorate the route with premium access. # Check the used key is: premium, data or requests used
    def wrapper(key):
        if validate_key(key) and validate_premium_key(key):
            res = end_point_func(key)
            increment_counter(key=key, response=res)
            return res
        else:
            return make_response(
                jsonify(
                    {"message": "Invalid API key."}
                ),
                401
            )

    wrapper.__name__ = end_point_func.__name__
    return wrapper
