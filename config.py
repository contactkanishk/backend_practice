import os


class Config:
    SECRET_KEY = "supersecretkey"  # Change this in production
    JWT_SECRET_KEY = "supersecretkey"

    # MongoDB Config
    MONGO_URI = "mongodb://localhost:27017/"
    DATABASE_NAME = "user_database"

    # Email Configuration
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "trygeneralusage@gmail.com"
    MAIL_PASSWORD = "itveondvcywplqrf"
    MAIL_DEFAULT_SENDER = "trygeneralusage@gmail.com"
