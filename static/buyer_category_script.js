// Subcategories mapping by category
const subcategories = {
    "all": [
        "Food", "Grooming", "Collars", "Leashes", "Supplements", "Medications", "Vitamins", "First Aid",
        "Chew Toys", "Interactive Toys", "Balls", "Puzzles", "Shirts", "Coats", "Shoes", "Hats",
        "Beds", "Scratch Posts", "Cages", "Playpens", "Aquariums", "Terrariums", "Kennels",
        "Clickers", "Treats", "Training Collars", "Books", "Harnesses", "Carriers", "Travel Bowls", "Backpacks"
    ],
    "pet essentials": ["Food", "Grooming", "Collars", "Leashes"],
    "health and wellness": ["Supplements", "Medications", "Vitamins", "First Aid"],
    "toys": ["Chew Toys", "Interactive Toys", "Balls", "Puzzles"],
    "clothing and accessory": ["Shirts", "Coats", "Shoes", "Hats"],
    "furniture": ["Beds", "Scratch Posts", "Cages", "Playpens"],
    "housing and enclosure": ["Cages", "Aquariums", "Terrariums", "Kennels"],
    "training and behavior": ["Clickers", "Treats", "Training Collars", "Books"],
    "outdoor and activity gear": ["Harnesses", "Carriers", "Travel Bowls", "Backpacks"]
};

// Function to populate the dropdown based on the selected category
function populateSubcategories(selectedCategory) {
    const dropdown = document.getElementById("subcategory-dropdown");
    dropdown.innerHTML = ""; // Clear current dropdown items

    // Get subcategories for the selected category
    const categorySubcategories = subcategories[selectedCategory] || [];

    // Create dropdown items for each subcategory
    categorySubcategories.forEach(subcategory => {
        const subcategoryLink = document.createElement("a");
        subcategoryLink.href = `?subcategory=${subcategory}`;
        subcategoryLink.textContent = subcategory;
        dropdown.appendChild(subcategoryLink);
    });
}

// Function to toggle the visibility of the dropdown
function toggleDropdown() {
    const dropdown = document.getElementById("subcategory-dropdown");
    dropdown.classList.toggle("active");
}

// Automatically load subcategories based on the current category (from the backend)
document.addEventListener("DOMContentLoaded", () => {
    const currentCategory = "{{ category_name }}"; // Injected from Flask
    populateSubcategories(currentCategory.toLowerCase());
});
