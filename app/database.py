from flask_login import UserMixin
from sqlalchemy import ForeignKey

from app.main import db


class Credentials(db.Model, UserMixin):
    __tablename__ = "credentials"

    username = db.Column(db.String(150), primary_key=True)
    password = db.Column(db.String(150))
    role = db.Column(db.Integer)  # 0: User, 1: Organizer

    # A sample data from this table will look like this
    def __repr__(self):
        return (
            f"Username : {self.username}, Password: {self.password}, Role: {self.role}"
        )

    def get_id(self):
        return self.username


class EventDetails(db.Model):
    __tablename__ = "event_details"

    # Event Indetifier information
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(1000))
    category = db.Column(db.String(150))

    # Location and Time information
    is_online = db.Column(db.Integer)
    venue = db.Column(db.String(150))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    # Participant capacity information
    max_capacity = db.Column(db.Integer)
    current_capacity = db.Column(db.Integer)

    # Ticket Price Information
    ticket_price = db.Column(db.Float)

    # Additional informations
    redirect_link = db.Column(db.String(300))
    additional_info = db.Column(db.String(1000))

    # A sample data from this table will look like this
    def __repr__(self):
        return f"ID : {self.id}, Name: {self.name}"

    def get_id(self):
        return self.id


class EventBanner(db.Model):
    __tablename__ = "event_banners"

    # Event Indetifier information
    # TODO: If we are restricting one graphics per event we can remove id and make event_id a primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer, ForeignKey("event_details.id"))
    image = db.Column(db.String(250), nullable=True)

    # A sample data from this table will look like this
    def __repr__(self):
        return f"Event ID : {self.id}, Banner Image: {self.name}"

    def get_id(self):
        return self.event_id


class OrganizerEventDetails(db.Model):
    __tablename__ = "organizer_event_relations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer, ForeignKey("event_details.id"))
    organizer_username = db.Column(db.String(150), ForeignKey("credentials.username"))

    # A sample data from this table will look like this
    def __repr__(self):
        return f"Organizer: {self.organizer_name}, Event ID: {self.event_id}"


class EventRating(db.Model):
    __tablename__ = 'event_ratings'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    #username of the user who gave the rating:
    attendee_username = db.Column(db.String(150), ForeignKey("credentials.username"))
    # Event on which the rating was given for:
    event_id = db.Column(db.Integer, ForeignKey('event_details.id'))
    #the rating:
    #TODO: Perhaps limit the range of integers from 1 to 5
    rating = db.Column(db.Integer)

    def __repr__(self):
        return f"Username: {self.attendee_username}, ID : {self.event_id}, Rating: {self.rating}"


class EventRegistration(db.Model):
    __tablename__ = "event_registration"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer, ForeignKey("event_details.id"), nullable=False)
    attendee_username = db.Column(db.String(150), ForeignKey("credentials.username"), nullable=False)

    # Unique constraint
    __table_args__ = (db.UniqueConstraint("event_id", "attendee_username"),)

    # A sample data from this table will look like this
    def __repr__(self):
        return f"Attendee: {self.attendee_username}, Event ID: {self.event_id}"


class UserDetails(db.Model):
    __tablename__ = "user_details"

    # Basic user details we will need for registration
    username = db.Column(db.String(150), primary_key=True)
    firstname = db.Column(db.String(250), nullable=False)
    lastname = db.Column(db.String(250), nullable=True)
    email = db.Column(db.String(250), nullable=False)

    # A sample data from this table will look like this
    def __repr__(self):
        return f"Username : {self.username}, First name: {self.firstname}, Email: {self.email}"
