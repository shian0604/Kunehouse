document.getElementById('filter-btn').addEventListener('click', function() {
    var filterOptions = document.getElementById('filter-options');
    // Toggle visibility
    if (filterOptions.style.display === "none" || filterOptions.style.display === "") {
        filterOptions.style.display = "block"; // Show the filter options
        var buttonRect = this.getBoundingClientRect(); // Get button position
        filterOptions.style.position = "absolute"; // Ensure it's positioned relative to the button
        filterOptions.style.top = (buttonRect.bottom + window.scrollY) + 'px'; // Set position below the button
        filterOptions.style.left = (buttonRect.left - 11) + 'px'; // Adjust to the left by 10px
    } else {
        filterOptions.style.display = "none"; // Hide the filter options
    }
});