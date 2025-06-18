// Function to set the default address
function setDefaultAddress(radio) {
    fetch('/set_default_address', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ address_id: radio.value })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Default address updated.');
            highlightDefaultAddress(radio.value);
        } else {
            alert('Error updating default address.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An unexpected error occurred.');
    });
}

// Function to highlight the selected default address
function highlightDefaultAddress(defaultAddressId) {
    const addressContainers = document.querySelectorAll('.address-container');

    addressContainers.forEach(container => {
        const radio = container.querySelector('input[type="radio"]');
        if (radio.value === defaultAddressId) {
            container.classList.add('default-address');
            container.style.backgroundColor = '#f2f2f2'; // Highlight color for default
        } else {
            container.classList.remove('default-address');
            container.style.backgroundColor = 'white'; // Reset color for non-default
        }
    });
}

// Highlight the default address on page load
window.onload = function() {
    const selectedRadio = document.querySelector('input[name="default_address"]:checked');
    if (selectedRadio) {
        highlightDefaultAddress(selectedRadio.value);
    }
};

// Function to delete an address
function deleteAddress(addressId) {
    if (confirm('Are you sure you want to delete this address?')) {
        fetch('/delete_address', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ address_id: addressId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Address deleted successfully.');
                location.reload(); // Reload the page to reflect the changes
            } else {
                alert('Error deleting address.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An unexpected error occurred while deleting the address.');
        });
    }
}
