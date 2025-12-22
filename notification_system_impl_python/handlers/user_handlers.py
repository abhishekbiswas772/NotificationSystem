from helpers.custom_exceptions import UserHandlersException
from models.users import Users
from helpers.helpers import get_id
from werkzeug.security import generate_password_hash, check_password_hash
from configs.db import db


class UserHandler:
    def __init__(self):
        self.db = db
        if not self.db:
            raise UserHandlersException("failed to connect database")

    def login_user(self, username : str, password: str) -> Users:
        if not username or username == "":
            raise UserHandlersException("Username cannot be empty")
        if not password or password == "":
            raise UserHandlersException("password cannot be empty")
        try:
            user = Users.query.filter_by(username = username).first()
            if not user:
                raise UserHandlersException("user is not present, please signup")
            password_match = check_password_hash(user.password, password)
            if not password_match:
                raise UserHandlersException("password is not matched")
            return user
        except Exception as e:
            print(e)
            raise UserHandlersException(str(e))


    def create_user(self, username : str, password: str, email: str) -> Users:
        if not username or username == "":
            raise UserHandlersException("username is missing")

        if not password or password == "":
            raise UserHandlersException("password is missing")

        if not email or email == "":
            raise UserHandlersException("email is missing")
        
        try:
            exiting_user = Users.query.filter(email = email).first()
            if exiting_user:
                raise UserHandlersException("user already exitis")
            generate_passwd_hash = generate_password_hash(password=password)
            user = Users(
                id = get_id(),
                email = email,
                password = generate_passwd_hash
            )
            self.db.session.add(user)
            self.db.session.commit()
            if not user:
                raise UserHandlersException("error in making user")
            return user
        except Exception as e:
            print(e)
            self.db.session.rollback()
            raise UserHandlersException(str(e))
