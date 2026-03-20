document.querySelector("form").addEventListener("submit", function(e) {
    const p1 = document.querySelector("#id_password1").value;
    const p2 = document.querySelector("#id_password2").value;

    if (p1 !== p2) {
        alert("Passwords do not match!");
        e.preventDefault();
    }
});
