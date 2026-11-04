from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from app.models.base import Base

db = SQLAlchemy(model_class=Base)
migrate = Migrate(compare_type=True)
csrf = CSRFProtect()
