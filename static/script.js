document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");

    form.addEventListener("submit", function (event) {
        const phone = document.querySelector('input[name="phone"]').value;
        const email = document.querySelector('input[name="email"]').value;

        const phonePattern = /^[0-9]{10}$/;
        if (!phone.match(phonePattern)) {
            alert("Please enter a valid 10-digit phone number.");
            event.preventDefault();
            return;
        }

        const emailPattern = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
        if (!email.match(emailPattern)) {
            alert("Please enter a valid email address.");
            event.preventDefault();
            return;
        }
    });
});
