document.addEventListener('DOMContentLoaded', function () {
    const toggleBtn = document.querySelector('.toggle-btn');
    const detailsContent = document.querySelector('.details-content');

    toggleBtn.addEventListener('click', function () {
        detailsContent.classList.toggle('active');

        // Optional: Toggle the arrow direction
        const svgPath = toggleBtn.querySelector('path');
        svgPath.setAttribute(
            'd',
            detailsContent.classList.contains('active')
                ? 'M7 14l5-5 5 5H7z' // Arrow up
                : 'M7 10l5 5 5-5H7z' // Arrow down
        );
    });
});

function changeQuantity(change) {
    var quantityInput = document.getElementById('product-quantity');
    var currentQuantity = parseInt(quantityInput.value) || 1;
    var newQuantity = currentQuantity + change;

    if (newQuantity >= 1) {  // Ensure quantity does not go below 1
        quantityInput.value = newQuantity;
    }
}

function showPopup() {
    document.getElementById('add-to-cart-popup').classList.remove('hidden');
}

function closePopup() {
    document.getElementById('add-to-cart-popup').classList.add('hidden');
}

function changeQuantity(change) {
    const quantityInput = document.querySelector('#product-quantity');
    let quantity = parseInt(quantityInput.value);
    quantity = Math.max(1, quantity + change); // Prevent negative quantities
    quantityInput.value = quantity;
}

function openOrderForm(event, productId) {
    event.preventDefault(); // Prevent default form action

    // Get the modal element
    const modal = document.getElementById('order-modal');

    // Fetch product details from the product card
    const productElement = event.target.closest('.product-detail');
    const productName = productElement.querySelector('h1').innerText;
    const productPrice = productElement.querySelector('h2').innerText.replace('$', '');

    // Populate modal fields
    modal.style.display = 'block';
    document.getElementById('modal-product-id').value = productId;
    document.getElementById('modal-product-name').innerText = productName;
    document.getElementById('modal-product-price').innerText = productPrice;
}

function closeOrderForm() {
    // Hide the modal
    document.getElementById('order-modal').style.display = 'none';
}

// Close modal on clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('order-modal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
};

