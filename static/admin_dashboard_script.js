document.getElementById('select-all').addEventListener('change', function() {
    const checkboxes = document.querySelectorAll('input[name="selected_admins"]');
    checkboxes.forEach(checkbox => checkbox.checked = this.checked);
});

// Toggle Add Admin Form
const addAdminBtn = document.getElementById('add-admin-btn');
const addAdminModal = document.getElementById('add-admin-modal');
const closeModal = document.getElementById('close-modal');

addAdminBtn.addEventListener('click', () => {
    addAdminModal.style.display = 'flex';
});

closeModal.addEventListener('click', () => {
    addAdminModal.style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === addAdminModal) {
            addAdminModal.style.display = 'none';
    }
});
