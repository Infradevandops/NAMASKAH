// Debug script to test button functionality
console.log('=== Button Debug Script ===');

// Test if buttons exist
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const googleBtn = document.getElementById('google-auth-btn');
const googleSep = document.getElementById('google-separator');

console.log('Login button:', loginBtn);
console.log('Register button:', registerBtn);
console.log('Google button:', googleBtn);
console.log('Google separator:', googleSep);

// Test if functions exist
console.log('login function:', typeof window.login);
console.log('register function:', typeof window.register);
console.log('togglePassword function:', typeof window.togglePassword);

// Test button click handlers
if (loginBtn) {
    console.log('Login button onclick:', loginBtn.onclick);
    console.log('Login button getAttribute onclick:', loginBtn.getAttribute('onclick'));
}

if (registerBtn) {
    console.log('Register button onclick:', registerBtn.onclick);
    console.log('Register button getAttribute onclick:', registerBtn.getAttribute('onclick'));
}

// Test CSS styles
if (loginBtn) {
    const styles = window.getComputedStyle(loginBtn);
    console.log('Login button computed styles:');
    console.log('- display:', styles.display);
    console.log('- visibility:', styles.visibility);
    console.log('- pointer-events:', styles.pointerEvents);
    console.log('- cursor:', styles.cursor);
}

// Test Google OAuth visibility
if (googleBtn) {
    const googleStyles = window.getComputedStyle(googleBtn);
    console.log('Google button computed styles:');
    console.log('- display:', googleStyles.display);
    console.log('- visibility:', googleStyles.visibility);
    console.log('- innerHTML:', googleBtn.innerHTML);
    console.log('- classList:', googleBtn.classList.toString());
}

// Test manual button click
console.log('Testing manual button clicks...');
if (loginBtn) {
    loginBtn.addEventListener('click', () => {
        console.log('✅ Login button click event fired!');
    });
}

if (registerBtn) {
    registerBtn.addEventListener('click', () => {
        console.log('✅ Register button click event fired!');
    });
}

console.log('=== End Debug Script ===');