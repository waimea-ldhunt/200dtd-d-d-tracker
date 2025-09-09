#===========================================================
# YOUR PROJECT TITLE HERE
# YOUR NAME HERE
#-----------------------------------------------------------
# BRIEF DESCRIPTION OF YOUR PROJECT HERE
#===========================================================

from flask import Flask, render_template, request, flash, redirect
import html
import random

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
def delete_encounter(id):
    with connect_db() as client:
        # Delete the thing from the DB
        sql = "DELETE FROM encounters WHERE id=?"
        params = [id]
        client.execute(sql, params)

        return redirect("/")
    
@app.get("/character/<int:id>/delete")
def delete_character(id):
    with connect_db() as client:
        # Delete the thing from the DB

        sql = "SELECT encounter_id FROM initiative WHERE character_id=?"
        params = [id]
        result = client.execute(sql, params)
        encounter = result.rows[0][0]

        sql = "DELETE FROM characters WHERE id=?"
        params = [id]
        client.execute(sql, params)

        sql = "DELETE FROM initiative WHERE character_id=?"
        params = [id]
        client.execute(sql, params)

        
        # Go back to the home page
        return redirect(f"/encounter/{encounter}")
    


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
    
@app.get("/character/<int:id>/activate")
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

@app.get("/character/<int:id>/deactivate")
def deactivate(id):
    with connect_db() as client:
        # Delete the thing from the DB
        sql = "UPDATE initiative SET active=0 WHERE init_id=?"
        params = [id]
        client.execute(sql, params)
        
        sql = "SELECT encounter_id FROM initiative WHERE init_id=?"
        params = [id]
        result = client.execute(sql, params)
        encounter = result.rows[0][0]

        # Go back to the home page
        return redirect(f"/encounter/{encounter}")
    
@app.get("/character/<int:id>/extra")
def extra_turn(id):
    with connect_db() as client:
        # Delete the thing from the DB

        sql = "SELECT encounter_id, active FROM initiative WHERE character_id=?"
        params = [id]
        result = client.execute(sql, params)
        encounter = result.rows[0][0]
        active = result.rows[0][1]

        sql = "INSERT INTO initiative (encounter_id, character_id, active) VALUES (?, ?, ?)"
        params = [encounter, id, active]
        client.execute(sql, params)

        
        # Go back to the home page
        return redirect(f"/encounter/{encounter}")
    
@app.get("/character/<int:id>/turn")
def remove_turn(id):
    with connect_db() as client:
        # Delete the thing from the DB

        sql = "SELECT encounter_id FROM initiative WHERE init_id=?"
        params = [id]
        result = client.execute(sql, params)
        encounter = result.rows[0][0]

        sql = "DELETE FROM initiative WHERE init_id=?"
        params = [id]
        client.execute(sql, params)
   
        # Go back to the home page
        return redirect(f"/encounter/{encounter}")
    
@app.post("/character/<int:id>/update")
def update_character(id):
    with connect_db() as client:
        # Delete the thing from the DB

        hp = request.form.get("hp")
        max_hp = request.form.get("max_hp")
        ac = request.form.get("ac")
        initiative = request.form.get("initiative")

        if hp > max_hp:
            hp = max_hp

        sql = "UPDATE characters SET hp=?, max_hp=?, ac=?, initiative_bonus=? WHERE id=?"
        params = [hp, max_hp, ac, initiative, id]
        client.execute(sql, params)

        sql = "SELECT encounter_id FROM initiative WHERE character_id=?"
        params = [id]
        result = client.execute(sql, params)
        encounter = result.rows[0][0]
    
        # Go back to the home page
        return redirect(f"/encounter/{encounter}")
    
@app.get("/character/<int:id>/roll")
def roll(id):
    with connect_db() as client:
        # Delete the thing from the DB

        sql = "SELECT character_id, encounter_id FROM initiative WHERE init_id=?"
        params = [id]
        result = client.execute(sql, params)
        character = result.rows[0][0]
        encounter = result.rows[0][1]

        sql = "SELECT initiative_bonus FROM characters WHERE id=?"
        params = [character]
        result = client.execute(sql, params)
        bonus = result.rows[0][0]

        roll = random.randint(1,20) + bonus
        
        sql = "UPDATE initiative SET roll=? WHERE init_id=?"
        params = [roll, id]
        client.execute(sql, params)

        
        # Go back to the home page
        return redirect(f"/encounter/{encounter}")