from flask import (
    Blueprint,
    render_template,
    send_from_directory,
    flash,
    current_app,
    request,
    redirect,
    url_for,
)
from flask_login import login_required, current_user
from sqlalchemy import delete
import logging
from datetime import date

from app.main import db
from app.globals import Role
from app.auth import login_required
from app.database import Credentials, EventRegistration, EventDetails, EventRating

events = Blueprint("events", __name__)

@events.route("/events/<int:id>", methods=["GET"])
@login_required
def show_event(id):
    logging.info("Loading webpage for event ID: %d", id)

    ## Get all the details for the event
    event = EventDetails.query.filter_by(id=id).first()

    if not event:
        print(
            "Integrity Error: The event ID passed to show_event has no valid entry in the database"
        )

    # Check if the user registered for the event
    is_registered = EventRegistration.query.filter_by(attendee_username=current_user.get_id(), event_id=id).first()

    #Check for past event. Users will only be able to rate if this is met. 
    is_past_event = past_event(id)
    logging.info("is it a past event: ",is_past_event)

    #get existing user rating
    prev_rating = previous_rating(attendee_username=current_user.get_id(), event_id=id)
    logging.info("Prev Rating: ", prev_rating)

    if is_registered is not None:
        flash("You are already registered for the event!", category="info")
        return render_template("event.html", event=event.__dict__, is_registered=True, is_past_event = is_past_event, prev_rating=prev_rating)
    else:
        return render_template("event.html", event=event.__dict__, is_registered=False, is_past_event = is_past_event, prev_rating=prev_rating)


@events.route("/events/send_file/<filename>")
@events.route("/events/register/send_file/<filename>")
@login_required
def send_file(filename):
    """
    This function is used to fetch event banner images for event.html pages"
    """

    return send_from_directory(current_app.config["GRAPHIC_DIRECTORY"], filename)


@events.route("/events/register/<int:event_id>", methods=["GET", "POST"])
@login_required
def register_for_event(event_id):
    """
    Description: Responsible for registering the user for an event.
                 Upon succesfull registeration it re-renders the template

    Returns:
        0: On successful registration
        1: If the event ID is invalid
        2: If the username is invalid
        3: If username is valid but the role is organizer
        4: If the user is already registered for the event
        redirect: If the event is a past event
    """
    # Check for valid event ID
    if event_id is None:
        logging.info("Cannot register user with an event ID: None")
        return ("1")

    logging.info("EVENT ID: %s", event_id)
    logging.info("USERNAME: %s", current_user.get_id())

    # Check for valid username
    user = Credentials.query.filter_by(username=current_user.get_id()).first()
    is_past_event = past_event(event_id)
    if not user:
        logging.warning("Cannot register user with an invalid username")
        return ("2")

    # We should also check if a username corresponds to a user and not an organizer
    if user.role != Role.USER.value:
        logging.warning("Cannot register an organizer")
        return ("3")
    
    #Check for past event is also needed and has been implemented on
    #the event.html page where the register button is disabled once an event is over.

    #TODO: Check if event has enough seats left

    # Check if the user is already registered
    is_registered = EventRegistration.query.filter_by(attendee_username=current_user.get_id(), event_id=event_id).first()
    if is_registered:
        logging.info("Cancelling user's registration")

        # Delete the registeration
        EventRegistration.query.filter_by(attendee_username=current_user.get_id(), event_id=event_id).delete()
        db.session.commit()

        flash("Cancelled registeration for the event!", category="success")
        event = EventDetails.query.filter_by(id=event_id).first()
        for key, val in event.__dict__.items():
            logging.info("Key: %s", key)
            logging.info("Value: %s", val)
        return redirect(url_for('events.show_event', id=event_id))

    # Register the user
    new_registration = EventRegistration(
        attendee_username=current_user.get_id(),
        event_id=event_id,
    )

    db.session.add(new_registration)
    db.session.commit()

    # Re-render the page showing user that registration is complete
    flash("Registered for the event!", category="success")
    event = EventDetails.query.filter_by(id=event_id).first()
    for key, val in event.__dict__.items():
        logging.info("Key: %s", key)
        logging.info("Value: %s", val)
    return redirect(url_for('events.show_event', id=event_id))


def past_event(event_id):
    #Here we check to see if the event is a past event or not.
    #Only if it is a past event will users be able to add a rating for it
    #TODO: Compare to the exact time as well. Currently only filters by date.
    event_detail = EventDetails.query.filter_by(id=event_id).first()
    logging.info(date.today())
    if event_detail.end_date < date.today():
        return True
    else:
        return False


def previous_rating(attendee_username, event_id):
    #This function returns 0 if no previous rating
    #Else, it returns the value of the previous rating (1-5)

    prev_rating = EventRating.query.filter_by(attendee_username=attendee_username, event_id=event_id).first()
    logging.info("Existing Rating: ", prev_rating)
    if prev_rating is None:
        return 0
    else:
        return prev_rating.rating


@events.route("/events/submit_rating/<int:event_id>", methods=["GET", "POST"])
def submit_rating(event_id):
    # Get the user's username (assuming they are logged in)
    attendee_username = current_user.get_id()
    event_id = request.form.get('event_id')
    rating = request.form.get('rating')

    if event_id and rating and attendee_username: 
        # Check if the user has already rated this event, and update the rating if they have
        existing_rating = EventRating.query.filter_by(attendee_username=attendee_username, event_id=event_id).first()
        if existing_rating is not None:
            existing_rating.rating = rating
            flash('Rating Updated successfully', 'success')
        else:
            # Create a new rating record
            new_rating = EventRating(attendee_username=attendee_username ,event_id=event_id, rating=rating)
            db.session.add(new_rating)
            
            db.session.commit()

            flash('Rating submitted successfully', 'success')
    else:
        flash('Failed to submit rating. Please try again.', 'error')
    
    return redirect(url_for('events.show_event', id=event_id))