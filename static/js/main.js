// Main Entry Point - Imports all modules
// This file serves as the orchestrator that loads all modular components

// Global variables shared across modules
const API_BASE = '';

// Load order matters - config first, then utilities, then feature modules
// All modules are loaded via script tags in HTML in this order:
// 1. config.js
// 2. utils.js
// 3. auth.js
// 4. services.js
// 5. verification.js
// 6. history.js
// 7. wallet.js
// 8. rentals.js
// 9. developer.js
// 10. settings.js
// 11. mobile.js (if exists)
// 12. main.js (this file)

console.log('✅ Namaskah SMS Platform Loaded');
console.log('📦 Modular architecture active');
