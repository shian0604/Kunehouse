const container = document.getElementById('container');
const registerBtn = document.getElementById('register');
const loginBtn = document.getElementById('login');

registerBtn.addEventListener('click', () => {
    container.classList.add("active");
});

loginBtn.addEventListener('click', () => {
    container.classList.remove("active");
});

setTimeout(() => {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((message) => {
        message.style.display = 'none';
    });
}, 3000);

function showRequirements() {
            const role = document.querySelector('input[name="role"]:checked').value;
            const requirementsList = document.getElementById('requirements-list');

            requirementsList.innerHTML = ""; // Clear current list

            if (role === 'buyer') {
                requirementsList.innerHTML = "<li>For Buyers: Valid email and password.</li>";
            } else if (role === 'seller') {
                requirementsList.innerHTML = "<li>For Sellers: Valid email, password, and business license.</li>";
            }
        }

        // Initialize requirements on page load
        window.onload = showRequirements;