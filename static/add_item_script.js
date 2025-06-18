// Define Subcategories for Each Main Category
const subcategories = {
    "pet essentials": ["Food", "Grooming", "Collars", "Leashes"],
    "health and wellness": ["Supplements", "Medications", "Vitamins", "First Aid"],
    "toys": ["Chew Toys", "Interactive Toys", "Balls", "Puzzles"],
    "clothing and accessory": ["Shirts", "Coats", "Shoes", "Hats"],
    "furniture": ["Beds", "Scratch Posts", "Cages", "Playpens"],
    "housing and enclosure": ["Cages", "Aquariums", "Terrariums", "Kennels"],
    "training and behavior": ["Clickers", "Treats", "Training Collars", "Books"],
    "outdoor and activity gear": ["Harnesses", "Carriers", "Travel Bowls", "Backpacks"]
};

// Update Subcategories when Main Category Changes
function updateSubcategories() {
    const mainCategory = document.getElementById("productcategory").value;
    const subcategorySelect = document.getElementById("subcategory");

    // Clear existing options
    subcategorySelect.innerHTML = "";

    // Populate Subcategories based on Main Category
    if (subcategories[mainCategory]) {
        subcategories[mainCategory].forEach(subcategory => {
            const option = document.createElement("option");
            option.value = subcategory;
            option.textContent = subcategory;
            subcategorySelect.appendChild(option);
        });
    }
}

// Initialize Subcategories when the page loads
document.addEventListener("DOMContentLoaded", updateSubcategories);

setTimeout(() => {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((message) => {
        message.style.display = 'none';
    });
}, 3000);
