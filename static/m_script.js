const sidebar = document.querySelector('.sidebar');
const content = document.querySelector('.content');
const toggleBtn = document.querySelector('.toggle-btn');

toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('hidden');
    content.classList.toggle('full');
});


setTimeout(() => {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((message) => {
        message.style.display = 'none';
    });
}, 3000);

function showPopup(productId, event) {
    // Prevent the parent <a> from being triggered
    event.stopPropagation();
    event.preventDefault();

    // Show the popup
    document.getElementById(`add-to-cart-popup-${productId}`).classList.remove('hidden');
    
}

function closePopup(productId) {
    // Hide the popup
    document.getElementById(`add-to-cart-popup-${productId}`).classList.add('hidden');
}


function changeQuantity(change) {
    const quantityInput = document.querySelector('#product-quantity');
    let quantity = parseInt(quantityInput.value);
    quantity = Math.max(1, quantity + change); // Prevent negative quantities
    quantityInput.value = quantity;
}
