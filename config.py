import os


class Config(object):
    SECRET_KEY = 'admin'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:admin@localhost:5432/improplac'