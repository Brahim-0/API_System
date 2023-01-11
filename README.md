# API_System (RESTful API Framework)
This system can be used to access resources such databases and/or microservices. It is similar to the google's api console. The system is engineered to be easy for reuse.

# API system responsible for:
  - Creating and managing users account
  - Generate API keys for different subscriptions
  - Manage access to resources
  - Manage Bandwidth Usage for API keys
  - Manage Number of requests for API Keys

# Technologies used:
  - Flask
  - jwt (Encryption)
  - Sqlalchemy (ORM)
  - WTForm

# API keys subscriptions:
  - Free: can access only free content with no restrictions
  - Premium with bandwidth limit: can access premium content with bandwidth limit
  - Premium with requests limit: can access premium content with a number of requests limit
  note: All types of keys expire after the duration of the subscription.
  
# To use the system:
  - Set up the database:
  To create the current architecture and constraints, run the following in the venv:
  ```
     From app.py import db
  ```
  ```
	  db.create_all()
  ```
      # these lines will create the tables mapping to the objects in the models.py file.
    
  - The system parameters can be set in the __init__.py file:
  
  - Secret key:
  ```
  app.config['SECRET_KEY'] = os.environ.get('API_system_secret_key')
  ```
  - Database: (sqlite is used in this example)
  ```
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
  ```
  - Mail parameters:
  ```
  app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
mail = Mail(app)
  ```
  - Subscription duration: The default duration for which the key will be valid
  ```
  app.config['Subscription_duration'] = 10  # The duration in days
  ```
  - Number of keys limit: The number of keys allowd to active at once per account. Once the limit is reached, the system will not generate any API for the user
  ```
  app.config['accounts_limit'] = 4  # The number of keys allowed to be active at once.
  ```
  - Bandwidth limit:
    the keys with bandwidth limit can not exceed the limit set in this varibale
  ```
  app.config['bandwidth_limit'] = 7  # in Mb
  ```
  - Number of requests limit:
    the keys with requests limit can not exceed the limit set in this varibale
  ```
  app.config['requests_limit'] = 4  # The number of requests allowed
  ```
# Premium_access decorator:
  For endpoints exposing premium content, add the decorator premium_access to the route to perform all the needed checkings before delivering the response to the user. This is an example:
  ```
  @app.route("/img/<key>", methods=['GET', 'POST'])
@premium_access
def img(key):
    response = make_response(
        send_from_directory("static/profile_pics", "2e32b4c96a8d8f10.jpg", as_attachment=False),
        200,
    )
    response.headers["Content-Type"] = "application/json"
    return response
  ```
  In this case, the premium_access decorator will check the validity of the key and increment the appropriate counter, which is in this case the bandwidth counter after delivering the files.

# Screenshots: 
# API keys panel:
<img width="1214" alt="Screenshot 2023-01-03 at 11 33 02 AM" src="https://user-images.githubusercontent.com/55364095/210399848-323d645e-b582-47cb-92cd-6ed3dcaee8d9.png">

