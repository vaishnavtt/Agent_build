from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here so that Base.metadata.create_all registers them
import app.models.workflow  # noqa: F401, E402
