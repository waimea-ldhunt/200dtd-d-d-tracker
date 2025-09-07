#===========================================================
# YOUR PROJECT TITLE HERE
# YOUR NAME HERE
#-----------------------------------------------------------
# BRIEF DESCRIPTION OF YOUR PROJECT HERE
#===========================================================

from flask import Flask, render_template, request, flash, redirect
import html

from app.helpers.session import init_session
from app.helpers.db      import connect_db
from app.helpers.errors  import init_error, not_found_error
from app.helpers.logging import init_logging
from app.helpers.time    import init_datetime, utc_timestamp, utc_timestamp_now


# Create the app
app = Flask(__name__)

# Configure app
init_session(app)   # Setup a session for messages, etc.
init_logging(app)   # Log requests
init_error(app)     # Handle errors and exceptions
init_datetime(app)  # Handle UTC dates in timestamps


#-----------------------------------------------------------
# Home page route
#-----------------------------------------------------------
@app.get("/")
def index():
    with connect_db() as client:

        sql = "SELECT * FROM encounters ORDER BY name ASC"
        params = []
        result = client.execute(sql, params)
        encounters = result.rows
        return render_template("pages/encounters.jinja", encounters=encounters)


#-----------------------------------------------------------
# About page route
#-----------------------------------------------------------
@app.get("/encounter/new")
def add():
    return render_template("pages/create-encounter.jinja")

@app.post("/encounter/create")
def create():
    name  = request.form.get("name")
    description = request.form.get("description")

    # Sanitise the text inputs
    name = html.escape(name)
    description = html.escape(description)

    with connect_db() as client:

        sql = "INSERT INTO encounters (name, description, pinned) VALUES (?, ?, 0)"
        params = [name, description]
        result = client.execute(sql, params)

        return redirect("/")


#-----------------------------------------------------------
# Things page route - Show all the things, and new thing form
#-----------------------------------------------------------



#-----------------------------------------------------------
# Thing page route - Show details of a single thing
#-----------------------------------------------------------
@app.get("/encounter/<int:id>")
def show_one_thing(id):
    with connect_db() as client:
        # Get the thing details from the DB
        sql = "SELECT * FROM encounters WHERE id=?"
        params = [id]
        result = client.execute(sql, params)

        # Did we get a result?
        if result.rows:
            # yes, so show it on the page
            encounter = result.rows[0]

            sql = "SELECT * FROM initiative FULL JOIN characters ON initiative.character_id = characters.id WHERE encounter_id=? ORDER BY roll desc"
            params = [id]
            result = client.execute(sql, params)
            characters = result.rows

            return render_template("pages/encounter.jinja", encounter=encounter, characters=characters)

        else:
            # No, so show error
            return not_found_error()
        

#-----------------------------------------------------------
# Route for adding a thing, using data posted from a form
#-----------------------------------------------------------
@app.post("/encounter/<int:id>/add")
def add_a_character(id):
    # Get the data from the form
    name  = request.form.get("name")
    type = request.form.get("type")
    ac = request.form.get("ac")
    hp = request.form.get("max_hp")
    initiative = request.form.get("initiative")
    notes = request.form.get("notes")

    # Sanitise the text inputs
    name = html.escape(name)
    type = html.escape(type)
    notes = html.escape(notes)

    type = type[0]

    with connect_db() as client:
        # Add the thing to the DB
        sql = "INSERT INTO characters (name, type, ac, hp, max_hp, initiative_bonus, notes) VALUES (?, ?, ?, ?, ?, ?, ?)"
        params = [name, type, ac, hp, hp, initiative, notes]
        client.execute(sql, params)

        sql = "SELECT id FROM characters WHERE name=?"
        params = [name]
        result = client.execute(sql, params)
        character_id = result.rows[0][0]

        sql = "INSERT INTO initiative (encounter_id, character_id, active) VALUES (?, ?, ?)"
        params = [id, character_id, 0]
        client.execute(sql, params)

        return redirect(f"/encounter/{id}")


#-----------------------------------------------------------
# Route for deleting a thing, Id given in the route
#-----------------------------------------------------------
@app.get("/encounter/<int:id>/delete")
def delete_a_thing(id):
    with connect_db() as client:
        # Delete the thing from the DB
        sql = "DELETE FROM encounters WHERE id=?"
        params = [id]
        client.execute(sql, params)

        # Go back to the home page
        flash("Encounter deleted", "success")
        return redirect("/")
    


@app.get("/encounter/<int:id>/pin")
def pin(id):
    with connect_db() as client:
        # Delete the thing from the DB
        sql = "UPDATE encounters SET pinned=1 WHERE id=?"
        params = [id]
        client.execute(sql, params)

        # Go back to the home page
        return redirect("/")
    
@app.get("/encounter/<int:id>/unpin")
def unpin(id):
    with connect_db() as client:
        # Delete the thing from the DB
        sql = "UPDATE encounters SET pinned=0 WHERE id=?"
        params = [id]
        client.execute(sql, params)

        # Go back to the home page
        return redirect("/")
    
@app.get("/activate/<int:id>")
def activate(id):
    with connect_db() as client:
        # Delete the thing from the DB
        sql = "UPDATE initiative SET active=1 WHERE init_id=?"
        params = [id]
        client.execute(sql, params)
        
        sql = "SELECT encounter_id FROM initiative WHERE init_id=?"
        params = [id]
        result = client.execute(sql, params)
        encounter = result.rows[0][0]

        # Go back to the home page
        return redirect(f"/encounter/{encounter}")