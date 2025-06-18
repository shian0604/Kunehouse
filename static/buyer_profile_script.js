function loadOrders(status) {
    fetch(`/buyer_orders/${status}`)
        .then(response => response.json())
        .then(data => {
            const ordersSection = document.getElementById('orders-section');
            ordersSection.innerHTML = '';

            if (data.orders && data.orders.length > 0) {
                data.orders.forEach(order => {
                    let orderHTML = `
                        <div class="order-item">
                            <div class="order-right">
                                <h4>Order ID: ${order.OrderID}</h4>
                                <img src="${order.ProductImg}" alt="Product Image">
                            </div>

                            <div class="order-left">
                                <p><strong>Product:</strong> Sample Product</p>
                                <p><strong>Store:</strong> Sample Store</p>
                                <p><strong>Color:</strong> Red</p>
                                <p><strong>Size:</strong> Medium</p>
                                <p><strong>Payment Method:</strong> Credit Card</p>
                                <p><strong>Shipping Address:</strong> 123 Main Street</p>
                                <p><strong>Status:</strong> Delivered</p>
                                <p><strong>Confirmation:</strong> Confirmed</p>
                                <p><strong>Total Amount:</strong> $100</p>
                            </div>
                        </div>

                    `;

                    // Add buttons for unpaid orders
                    if (status === 'unpaid' && order.ConfirmationStatus === 'pending') {
                        orderHTML += `
                            <button onclick="confirmOrder(${order.OrderID})">Confirm Order</button>
                            <button onclick="cancelOrder(${order.OrderID})">Cancel Order</button>
                        `;
                    }

                    if (order.OrderStatus === 'delivered') {
                        orderHTML += `
                            <button onclick="markOrderReceived(${order.OrderID})">Order Received</button>
                        `;
                    }

                    if (order.OrderStatus === 'review') {
                        orderHTML += `
                            <a href="/review_product/${order.OrderID}">
                                <button>Review</button>
                            </a>
                        `;
                    }



                    orderHTML += `</div>`;
                    ordersSection.innerHTML += orderHTML;
                });
            } else {
                ordersSection.innerHTML = `<p>No orders found for ${status}.</p>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('orders-section').innerHTML = '<p>An error occurred while fetching orders.</p>';
        });
}

function setActiveTab(event, status) {
    event.preventDefault();

    // Remove 'active' class from all links and add it to the clicked link
    document.querySelectorAll('.order-link').forEach(link => link.classList.remove('active'));
    event.target.classList.add('active');

    // Load the orders for the selected status
    loadOrders(status);
}

// Load all orders by default on page load
document.addEventListener('DOMContentLoaded', () => {
    loadOrders('archived');
});

function confirmOrder(orderId) {
    fetch(`/confirm_order/${orderId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                loadOrders('unpaid');
            } else {
                alert(data.error || 'Failed to confirm order.');
            }
        })
        .catch(error => console.error('Error:', error));
}

function cancelOrder(orderId) {
    fetch(`/cancel_order/${orderId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            loadOrders('unpaid'); // Refresh the 'unpaid' orders list
        } else {
            alert(data.error || 'An error occurred while canceling the order.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while canceling the order.');
    });
}

function markOrderReceived(orderId) {
    fetch(`/mark_order_received/${orderId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                loadOrders('shipped'); // Refresh the shipped orders list
            } else {
                alert(data.error || 'Failed to mark the order as received.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while marking the order as received.');
        });
}