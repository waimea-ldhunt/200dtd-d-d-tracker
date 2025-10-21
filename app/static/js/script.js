function dropdown(id) {

    // Get the dropdown element from id
    var element = document.getElementById("dropdown_"+id);


    if (element.className == "dropdown_closed") { // If the class is 'closed', set it to 'open'
        element.className = "dropdown_open"
    } else if (element.className == "dropdown_open") { // If the class is 'open', set it to 'closed'
        element.className = "dropdown_closed"
    }

    // Get the the arrow element from id
    var element = document.getElementById("arrow_"+id);

    if (element.className == "arrow_down") { // If the class is 'down', set it to 'up'
        console.log("A")
        element.className = "arrow_up"
    } else if (element.className == "arrow_up") { // If the class is 'up', set it to 'down'
        element.className = "arrow_down"
    }
}