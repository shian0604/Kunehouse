document.getElementById('select-all-buyers').addEventListener('change', function () {
    const checkboxes = document.querySelectorAll('.buyer-checkbox');
    checkboxes.forEach(checkbox => checkbox.checked = this.checked);
});

document.getElementById('select-all-sellers').addEventListener('change', function () {
    const checkboxes = document.querySelectorAll('.seller-checkbox');
    checkboxes.forEach(checkbox => checkbox.checked = this.checked);
});

document.getElementById('toggle-btn').addEventListener('click', function () {
    const buyersTable = document.getElementById('buyers-table');
    const sellersTable = document.getElementById('sellers-table');
    const userTypeInput = document.getElementById('user-type');

    if (buyersTable.style.display === 'block') {
        buyersTable.style.display = 'none';
        sellersTable.style.display = 'block';
        userTypeInput.value = 'seller';
        this.textContent = 'Show Buyers';
    } else {
        buyersTable.style.display = 'block';
        sellersTable.style.display = 'none';
        userTypeInput.value = 'buyer';
        this.textContent = 'Show Sellers';
    }
});

setTimeout(() => {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((message) => {
        message.style.display = 'none';
    });
}, 3000);