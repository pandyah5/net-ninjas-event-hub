from flask import Flask
from flask_cors import CORS
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from elasticsearch import Elasticsearch
import os
import logging, sys

## Initialize and import databases schemas
db = SQLAlchemy()
from app.database import Credentials, EventDetails

# Initialize logger module
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

## Initialize elastic search server for autocomplete functionality
elasticsearch_host = os.environ["ELASTICSEARCH_HOST"]
es = Elasticsearch([f"http://{elasticsearch_host}:9200"])

## Global constants
DB_NAME = "database.db"
R_USER = "user"
R_ORGANIZER = "organizer"

def create_app(debug):
    app = Flask(__name__)
    app.debug = debug
    app.config["SECRET_KEY"] = "4829jfnwurduh4293k"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_NAME}"
    app.config["GRAPHIC_DIRECTORY"] = path = os.path.join(
        app.root_path, "assets", "event-assets"
    )
    db.init_app(app)
    bootstrap = Bootstrap(app=app)

    ## Make the app CORS compliant
    CORS(app)

    ## Register the paths so that we can use the routes defined there. E.g. Login and Register
    from app.auth import auth
    from app.user import user
    from app.organizer import organizer
    from app.events import events
    from app.search import search

    app.register_blueprint(auth, url_prefix="/")
    app.register_blueprint(user, url_prefix="/")
    app.register_blueprint(organizer, url_prefix="/")
    app.register_blueprint(events, url_prefix="/")
    app.register_blueprint(search, url_prefix="/")

    with app.app_context():
        db.create_all()

        # Index the events database using elasticsearch
        # es = Elasticsearch([f"http://{elasticsearch_host}:9200"])
        if es.indices.exists(index="events"):
            es.options(ignore_status=[400, 404]).indices.delete(index="events")
        else:
            es.index(index="events", document={})

        events_data = EventDetails.query.all()
        for row in events_data:
            event_detail = {
                "id": str(getattr(row, "id")),
                "name": str(getattr(row, "name")),
                "description": str(getattr(row, "description")),
                "type": str(getattr(row, "type")),
                "venue": str(getattr(row, "venue")),
                "additional_info": str(getattr(row, "additional_info")),
            }
            logging.info("The event dict for indexing:", event_detail)
            es.index(index="events", document=event_detail)

        es.indices.refresh(index="events")
        logging.info(es.cat.count(index="events", format="json"))

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(username):
        return Credentials.query.get(username)

    return app

app = create_app(debug=True)
