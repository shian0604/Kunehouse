document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('select_all');
    const productCheckboxes = document.querySelectorAll('.product-checkbox');
    

    // Function to toggle all product checkboxes based on "Select All" checkbox
    selectAllCheckbox.addEventListener('change', function() {
        productCheckboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
        });
    });
});

const deleteButton = document.getElementById('delete-button');
const productCheckboxes = document.querySelectorAll('.product-checkbox'); // Assuming you have a class for product checkboxes

deleteButton.addEventListener('click', function() {
    const selectedProducts = Array.from(productCheckboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value); // Get the value (ID) of each selected product

    if (selectedProducts.length > 0) {
        // Confirm deletion
        const confirmation = confirm(`Are you sure you want to delete these products: ${selectedProducts.join(', ')}?`);
        if (confirmation) {
            fetch('/delete_products', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ product_ids: selectedProducts }),
            })
            .then(response => {
                if (response.ok) {
                    location.reload(); // Reload to see changes
                } else {
                    alert('Error deleting products. Please try again.');
                }
            })
            .catch(err => {
                console.error('Error:', err);
                alert('Error deleting products. Please try again.');
            });
        }
    } else {
        alert('Please select at least one product to delete.');
    }
});

function editProduct() {
    // Get all selected product checkboxes
    const checkboxes = document.querySelectorAll('.product-checkbox:checked');
    if (checkboxes.length === 1) {
        const productId = checkboxes[0].value;
        window.location.href = `/edit_product/${productId}`;
    } else if (checkboxes.length === 0) {
        alert('Please select a product to edit.');
    } else {
        alert('Please select only one product to edit.');
    }
}

