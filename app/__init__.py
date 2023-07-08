import os
import io
import boto3
import pandas as pd
from flask import Flask
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy


load_dotenv()

ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
CSV = os.getenv("CSV")
PARQUET = os.getenv("PARQUET")

db = SQLAlchemy()

# initialize s3 client
s3 = boto3.client("s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# get files from s3
response = s3.get_object(Bucket=BUCKET_NAME, Key=CSV)
content = response["Body"]
cdata = pd.read_csv(content)
response = s3.get_object(Bucket=BUCKET_NAME, Key=PARQUET)
content = response["Body"]
pdata = pd.read_parquet(io.BytesIO(content.read()))


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["DEBUG"] = bool(os.getenv("FLASK_DEBUG"))
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("FLASK_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    from .main import main

    app.register_blueprint(main)

    return app
