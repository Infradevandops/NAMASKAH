// Biometric Authentication Module

let biometricAvailable = false;

async function checkBiometricSupport() {
    if (!window.PublicKeyCredential) return false;
    
    try {
        biometricAvailable = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
        return biometricAvailable;
    } catch (error) {
        return false;
    }
}

async function registerBiometric(email) {
    if (!biometricAvailable) {
        showNotification('❌ Biometric not supported on this device', 'error');
        return;
    }
    
    try {
        const challenge = new Uint8Array(32);
        crypto.getRandomValues(challenge);
        
        const publicKeyOptions = {
            challenge: challenge,
            rp: { name: "Namaskah SMS" },
            user: {
                id: new TextEncoder().encode(email),
                name: email,
                displayName: email
            },
            pubKeyCredParams: [{ alg: -7, type: "public-key" }],
            authenticatorSelection: {
                authenticatorAttachment: "platform",
                userVerification: "required"
            },
            timeout: 60000
        };
        
        const credential = await navigator.credentials.create({ publicKey: publicKeyOptions });
        
        localStorage.setItem('biometric_enabled', 'true');
        localStorage.setItem('biometric_id', btoa(String.fromCharCode(...new Uint8Array(credential.rawId))));
        
        showNotification('✅ Biometric authentication enabled', 'success');
        return true;
    } catch (error) {
        showNotification('❌ Biometric registration failed', 'error');
        return false;
    }
}

async function authenticateWithBiometric() {
    if (!localStorage.getItem('biometric_enabled')) return false;
    
    try {
        const challenge = new Uint8Array(32);
        crypto.getRandomValues(challenge);
        
        const credentialId = Uint8Array.from(atob(localStorage.getItem('biometric_id')), c => c.charCodeAt(0));
        
        const publicKeyOptions = {
            challenge: challenge,
            allowCredentials: [{
                id: credentialId,
                type: 'public-key',
                transports: ['internal']
            }],
            timeout: 60000,
            userVerification: "required"
        };
        
        const assertion = await navigator.credentials.get({ publicKey: publicKeyOptions });
        
        if (assertion) {
            showNotification('✅ Biometric authentication successful', 'success');
            return true;
        }
        return false;
    } catch (error) {
        return false;
    }
}

function disableBiometric() {
    localStorage.removeItem('biometric_enabled');
    localStorage.removeItem('biometric_id');
    showNotification('✅ Biometric authentication disabled', 'success');
}

// Initialize on load
checkBiometricSupport().then(supported => {
    if (supported && localStorage.getItem('biometric_enabled')) {
        const loginBtn = document.querySelector('#login-form button');
        if (loginBtn) {
            const biometricBtn = document.createElement('button');
            biometricBtn.textContent = '🔐 Login with Biometric';
            biometricBtn.style.marginTop = '10px';
            biometricBtn.onclick = async (e) => {
                e.preventDefault();
                const success = await authenticateWithBiometric();
                if (success && token) checkAuth();
            };
            loginBtn.parentNode.insertBefore(biometricBtn, loginBtn.nextSibling);
        }
    }
});
