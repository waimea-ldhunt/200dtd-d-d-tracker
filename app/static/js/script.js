function dropdown(id) {
    var element = document.getElementById("dropdown_"+id);

    if (element.className == "dropdown_closed") {
        element.className = "dropdown_open"
    } else if (element.className == "dropdown_open") {
        element.className = "dropdown_closed"
    }
}   