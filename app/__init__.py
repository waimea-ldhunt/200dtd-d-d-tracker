#=============================================================================================#
# D&D Combat Tracker                                                                          #
# Lachlan Hunt                                                                                #
#---------------------------------------------------------------------------------------------#
# A web app that allows the DM to effectively and efficiently manage creatures in encounters, #
# take notes and see important details.                                                       #
#=============================================================================================#

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

        # Get list of encounters
        sql = "SELECT * FROM encounters ORDER BY name ASC"
        params = []
        result = client.execute(sql, params)
        encounters = result.rows

        # Return home page template
        return render_template("pages/encounters.jinja", encounters=encounters)


#-----------------------------------------------------------
# Create encounter page route
#-----------------------------------------------------------
@app.get("/encounter/new")
def add():

    # Return create encounter page template
    return render_template("pages/create-encounter.jinja")

#-----------------------------------------------------------
# Add encounter
#-----------------------------------------------------------
@app.post("/encounter/create")
def create():

    # Get form inputs
    name  = request.form.get("name")
    description = request.form.get("description")

    # Sanitise the text inputs
    name = html.escape(name)
    description = html.escape(description)

    with connect_db() as client:

        # Create encounter using form inputs
        sql = "INSERT INTO encounters (name, description, pinned) VALUES (?, ?, 0)"
        params = [name, description]
        result = client.execute(sql, params)

        # Redirect to home page
        return redirect("/")

#-----------------------------------------------------------
# Encounter Page route
#-----------------------------------------------------------
@app.get("/encounter/<int:id>")
def view_encounter(id):
    with connect_db() as client:

        # Get the encounter
        sql = "SELECT * FROM encounters WHERE id=?"
        params = [id]
        result = client.execute(sql, params)

        # Did we get a result?
        if result.rows:
            encounter = result.rows[0]

            # Join the Turn and Character pages to allow the dropdowns to work correctly
            sql = "SELECT * FROM initiative FULL JOIN characters ON initiative.character_id = characters.id WHERE encounter_id=? ORDER BY roll desc, initiative_bonus desc"
            params = [id]
            result = client.execute(sql, params)
            characters = result.rows
            
            # Get list of active turns to display to display empty if required
            sql = "SELECT * FROM initiative WHERE encounter_id=? AND active=0"
            params = [id]
            result = client.execute(sql, params)
            inactive = result.rows

            # Get list of inactive turns to display empty if required
            sql = "SELECT * FROM initiative WHERE encounter_id=? AND active=1"
            params = [id]
            result = client.execute(sql, params)
            active = result.rows

            # Return encounter page template
            return render_template("pages/encounter.jinja", encounter=encounter, characters=characters, active=active, inactive=inactive)

        else:
            # Show not found error
            return not_found_error()
        
#-----------------------------------------------------------
# Add a Character
#-----------------------------------------------------------
@app.post("/encounter/<int:id>/add")
def add_character(id):

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

    with connect_db() as client:

        # Add character using the form inputs
        sql = "INSERT INTO characters (name, type, ac, hp, max_hp, initiative_bonus, notes) VALUES (?, ?, ?, ?, ?, ?, ?)"
        params = [name, type, ac, hp, hp, initiative, notes]
        client.execute(sql, params)

        # Get id of the new character
        sql = "SELECT id FROM characters WHERE name=?"
        params = [name]
        result = client.execute(sql, params)
        character_id = result.rows[0][0]

        # Add a turn for the new character
        sql = "INSERT INTO initiative (encounter_id, character_id) VALUES (?, ?)"
        params = [id, character_id]
        client.execute(sql, params)

        # Redirect to the encounter page
        return redirect(f"/encounter/{id}")


#-----------------------------------------------------------
# Deleting an Encounter
#-----------------------------------------------------------
@app.get("/encounter/<int:id>/delete")
def delete_encounter(id):
    with connect_db() as client:
        
        # Delete encounter from database
        sql = "DELETE FROM encounters WHERE id=?"
        params = [id]
        client.execute(sql, params)

        # Redirect to home page
        return redirect("/")
    
#-----------------------------------------------------------
# Deleting a Character
#-----------------------------------------------------------
@app.get("/encounter/<int:encounter>/character/<int:id>/delete")
def delete_character(encounter, id):
    with connect_db() as client:

        # Delete character from characters
        sql = "DELETE FROM characters WHERE id=?"
        params = [id]
        client.execute(sql, params)

        # Delete character from initiative
        sql = "DELETE FROM initiative WHERE character_id=?"
        params = [id]
        client.execute(sql, params)

        # Redirect to the encounter page
        return redirect(f"/encounter/{encounter}")
    

#-----------------------------------------------------------
# Pin an Encounter
#-----------------------------------------------------------
@app.get("/encounter/<int:id>/pin")
def pin(id):
    with connect_db() as client:

        # Set the 'pinned' value of the encounter to 1
        sql = "UPDATE encounters SET pinned=1 WHERE id=?"
        params = [id]
        client.execute(sql, params)

        # Redirect to the home page
        return redirect("/")
    
#-----------------------------------------------------------
# Unpin an Encounter
#-----------------------------------------------------------
@app.get("/encounter/<int:id>/unpin")
def unpin(id):
    with connect_db() as client:
        
        # Set the 'pinned' value of the encounter to 0
        sql = "UPDATE encounters SET pinned=0 WHERE id=?"
        params = [id]
        client.execute(sql, params)

        # Redirect to the home page
        return redirect("/")

#-----------------------------------------------------------
# Activate a Character
#-----------------------------------------------------------
@app.get("/encounter/<int:encounter>/character/<int:id>/activate")
def activate(encounter, id):
    with connect_db() as client:

        # Set the 'active' value of the character to 1
        sql = "UPDATE initiative SET active=1 WHERE init_id=?"
        params = [id]
        client.execute(sql, params)

        # Redirect to the home page
        return redirect(f"/encounter/{encounter}")

#-----------------------------------------------------------
# Deactivate a Character
#-----------------------------------------------------------
@app.get("/encounter/<int:encounter>/character/<int:id>/deactivate")
def deactivate(encounter, id):
    with connect_db() as client:

        # Set the 'active' value of the character to 0
        sql = "UPDATE initiative SET active=0 WHERE init_id=?"
        params = [id]
        client.execute(sql, params)
        
        # Redirect to the home page
        return redirect(f"/encounter/{encounter}")
    
#-----------------------------------------------------------
# Add an extra turn
#-----------------------------------------------------------
@app.get("/encounter/<int:encounter>/character/<int:id>/extra_turn")
def extra_turn(encounter, id):
    with connect_db() as client:

        # Get the 'active' value of the existing turn
        sql = "SELECT active FROM initiative WHERE character_id=?"
        params = [id]
        result = client.execute(sql, params)
        active = result.rows[0][0]

        # Add the new turn using the active value 
        sql = "INSERT INTO initiative (encounter_id, character_id, active) VALUES (?, ?, ?)"
        params = [encounter, id, active]
        client.execute(sql, params)

        # Redirect to the home page
        return redirect(f"/encounter/{encounter}")

#-----------------------------------------------------------
# Remove turn
#-----------------------------------------------------------
@app.get("/encounter/<int:encounter>/character/<int:id>/turn/<int:turn_id>/remove_turn")
def remove_turn(encounter, id, turn_id):
    with connect_db() as client:
        
        # Get list of turns for the character
        sql = "SELECT * FROM initiative WHERE character_id=?"
        params = [id]
        result = client.execute(sql, params)
        turns = result.rows

        # If deleting the last turn, delete the character instead
        if turns.__len__() == 1:
            return redirect(f"/encounter/{encounter}/character/{id}/delete")

        # Remove the turn from the database
        sql = "DELETE FROM initiative WHERE init_id=?"
        params = [turn_id]
        client.execute(sql, params)
   
        # Redirect to the home page
        return redirect(f"/encounter/{encounter}")

#-----------------------------------------------------------
# Update character details
#-----------------------------------------------------------
@app.post("/encounter/<int:encounter>/character/<int:id>/update")
def update_character(encounter, id):
    with connect_db() as client:

        # Get form inputs
        hp = request.form.get("hp")
        max_hp = request.form.get("max_hp")
        ac = request.form.get("ac")
        initiative_bonus = request.form.get("initiative_bonus")
        notes = request.form.get("notes")

        # Update character using form inputs
        sql = "UPDATE characters SET hp=?, max_hp=?, ac=?, initiative_bonus=?, notes=? WHERE id=?"
        params = [hp, max_hp, ac, initiative_bonus, notes, id]
        client.execute(sql, params)
    
        # Redirect to the encounter page
        return redirect(f"/encounter/{encounter}")

#-----------------------------------------------------------
# Roll/Reroll initiative
#-----------------------------------------------------------
@app.get("/encounter/<int:encounter>/character/<int:id>/roll")
def roll(encounter, id):
    with connect_db() as client:

        # Gets Character id from Turn
        sql = "SELECT character_id FROM initiative WHERE init_id=?"
        params = [id]
        result = client.execute(sql, params)
        character = result.rows[0][0]

        # Gets Initiative bonus from character
        sql = "SELECT initiative_bonus FROM characters WHERE id=?"
        params = [character]
        result = client.execute(sql, params)
        bonus = result.rows[0][0]

        # Generates Initiative Roll (Bonus Included)
        roll = random.randint(1,20) + bonus
        
        # Sets Initiative of Turn
        sql = "UPDATE initiative SET roll=? WHERE init_id=?"
        params = [roll, id]
        client.execute(sql, params)

        # Redirects to the encounter page
        return redirect(f"/encounter/{encounter}")