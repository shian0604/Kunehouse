function updateStock(productId, action) {
    $.ajax({
        url: '/update_stock',
        method: 'POST',
        data: {
            product_id: productId,
            action: action
        },
        success: function(response) {
            $('#quantity-' + productId).text(response.new_quantity);
        },
        error: function() {
            alert('Failed to update stock. Please try again.');
        }
    });
}