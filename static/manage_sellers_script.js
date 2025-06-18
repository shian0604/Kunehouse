document.getElementById('select-all').addEventListener('change', function(event) {
    var checkboxes = document.querySelectorAll('input[name="selected_sellers"]');
    checkboxes.forEach(function(checkbox) {
        checkbox.checked = event.target.checked;
    });
});

setTimeout(() => {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((message) => {
        message.style.display = 'none';
    });
}, 3000);