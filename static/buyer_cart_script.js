function changeQuantity(button, change) {
    var inputField = button.parentElement.querySelector('.quantity-input');
    var currentQuantity = parseInt(inputField.value) || 0;
    var newQuantity = currentQuantity + change;

    if (newQuantity >= 1) {  // Ensuring the quantity doesn't go below 1
        inputField.value = newQuantity;
    }
}

function updateQuantity(input, productId) {
    var newQuantity = parseInt(input.value) || 0;
    if (newQuantity < 1) {
        input.value = 1;  // Ensure minimum quantity is 1
    }
    // Here you can add an AJAX call or form submission to update the quantity in the database if needed.
}

document.addEventListener('DOMContentLoaded', function () {
    const selectAllCheckbox = document.getElementById('select-all');
    const cartCheckboxes = document.querySelectorAll('.cart-checkbox');
    const selectedItemsInput = document.getElementById('selected-items'); // Hidden input to store selected items

    // Toggle all checkboxes when "Select All" is clicked
    selectAllCheckbox.addEventListener('change', function () {
        const isChecked = selectAllCheckbox.checked;
        cartCheckboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
        });
        updateSelectedItems(); // Update the selected items
    });

    // Uncheck "Select All" if any checkbox is manually unchecked
    cartCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            if (!checkbox.checked) {
                selectAllCheckbox.checked = false;
            } else if ([...cartCheckboxes].every(cb => cb.checked)) {
                selectAllCheckbox.checked = true;
            }
            updateSelectedItems(); // Update the selected items
        });
    });

    // Update the hidden input with selected item IDs
    function updateSelectedItems() {
        const selectedItems = [];
        cartCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                selectedItems.push(checkbox.value);
            }
        });
        selectedItemsInput.value = selectedItems.join(','); // Store the selected items as a comma-separated string
    }
});


document.getElementById('discard-form').addEventListener('submit', function (event) {
    const selectedCheckboxes = document.querySelectorAll('.cart-checkbox:checked');
    const selectedItems = Array.from(selectedCheckboxes).map(checkbox => checkbox.value);

    if (selectedItems.length === 0) {
        event.preventDefault(); // Prevent form submission if no items are selected
        alert('Please select items to discard.');
        return;
    }

    // Set the hidden input value to the selected item IDs
    document.getElementById('selected-items').value = JSON.stringify(selectedItems);
});



