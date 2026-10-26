"""Shared Flask extension instances.

They live in their own module so that models, services and the application
factory can import them without creating circular imports.
"""
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
cors = CORS()
