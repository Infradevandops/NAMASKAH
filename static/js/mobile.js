// Mobile Features: PWA, Pull-to-Refresh, Swipe Gestures, Bottom Nav

// Bottom Navigation
function initBottomNav() {
    const sections = ['home', 'verify', 'rentals', 'history', 'settings'];
    const currentSection = localStorage.getItem('currentSection') || 'home';
    
    document.querySelectorAll('.bottom-nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.section === currentSection) {
            item.classList.add('active');
        }
    });
}

function navigateToSection(section) {
    localStorage.setItem('currentSection', section);
    
    // Hide all sections
    document.querySelectorAll('.card').forEach(card => card.style.display = 'none');
    
    // Show relevant section
    if (section === 'home') {
        document.querySelector('.user-info').style.display = 'flex';
        document.querySelectorAll('.card')[0].style.display = 'block';
    } else if (section === 'verify') {
        document.querySelectorAll('.card')[0].style.display = 'block';
    } else if (section === 'rentals') {
        document.getElementById('active-rentals-section').style.display = 'block';
    } else if (section === 'history') {
        document.getElementById('verifications-list').style.display = 'block';
        document.getElementById('transactions-list').style.display = 'block';
    } else if (section === 'settings') {
        document.querySelectorAll('.card').forEach((card, i) => {
            if (i >= document.querySelectorAll('.card').length - 3) card.style.display = 'block';
        });
    }
    
    initBottomNav();
    scrollToTop();
}

// Hamburger Menu
function toggleMobileMenu() {
    const menu = document.querySelector('.mobile-menu');
    const overlay = document.querySelector('.mobile-menu-overlay');
    const hamburger = document.querySelector('.hamburger');
    
    menu.classList.toggle('open');
    overlay.classList.toggle('open');
    hamburger.classList.toggle('active');
}

function closeMobileMenu() {
    document.querySelector('.mobile-menu').classList.remove('open');
    document.querySelector('.mobile-menu-overlay').classList.remove('open');
    document.querySelector('.hamburger').classList.remove('active');
}

// Pull to Refresh
let pullStartY = 0;
let pullMoveY = 0;
let isPulling = false;

function initPullToRefresh() {
    const container = document.querySelector('.container');
    const indicator = document.querySelector('.pull-to-refresh');
    
    container.addEventListener('touchstart', (e) => {
        if (window.scrollY === 0) {
            pullStartY = e.touches[0].clientY;
            isPulling = true;
        }
    });
    
    container.addEventListener('touchmove', (e) => {
        if (!isPulling) return;
        
        pullMoveY = e.touches[0].clientY - pullStartY;
        
        if (pullMoveY > 0 && pullMoveY < 100) {
            indicator.classList.add('visible');
            indicator.style.transform = `translateX(-50%) scale(${pullMoveY / 100})`;
        }
    });
    
    container.addEventListener('touchend', async () => {
        if (isPulling && pullMoveY > 80) {
            indicator.classList.add('spinning');
            await refreshData();
            setTimeout(() => {
                indicator.classList.remove('visible', 'spinning');
            }, 500);
        } else {
            indicator.classList.remove('visible');
        }
        
        isPulling = false;
        pullStartY = 0;
        pullMoveY = 0;
    });
}

async function refreshData() {
    try {
        await Promise.all([
            loadUserData(),
            loadHistory(),
            loadTransactions()
        ]);
        showNotification('✅ Refreshed', 'success');
    } catch (error) {
        console.error('Refresh error:', error);
    }
}

// Swipe Gestures for Modals
function initSwipeGestures() {
    const modals = document.querySelectorAll('.modal-content');
    
    modals.forEach(modal => {
        let startY = 0;
        let currentY = 0;
        let isSwiping = false;
        
        modal.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
            isSwiping = true;
        });
        
        modal.addEventListener('touchmove', (e) => {
            if (!isSwiping) return;
            
            currentY = e.touches[0].clientY;
            const diff = currentY - startY;
            
            if (diff > 0) {
                modal.classList.add('swiping');
                modal.style.transform = `translateY(${diff}px)`;
            }
        });
        
        modal.addEventListener('touchend', () => {
            if (!isSwiping) return;
            
            const diff = currentY - startY;
            modal.classList.remove('swiping');
            
            if (diff > 100) {
                modal.closest('.modal').classList.add('hidden');
            }
            
            modal.style.transform = '';
            isSwiping = false;
        });
    });
}

// PWA Install Prompt
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Show custom install prompt after 30 seconds
    setTimeout(() => {
        if (!localStorage.getItem('pwaInstallDismissed')) {
            showPWAInstallPrompt();
        }
    }, 30000);
});

function showPWAInstallPrompt() {
    const prompt = document.querySelector('.pwa-install-prompt');
    if (prompt) prompt.classList.add('show');
}

function dismissPWAPrompt() {
    document.querySelector('.pwa-install-prompt').classList.remove('show');
    localStorage.setItem('pwaInstallDismissed', 'true');
}

async function installPWA() {
    if (!deferredPrompt) return;
    
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
        showNotification('✅ App installed!', 'success');
    }
    
    deferredPrompt = null;
    dismissPWAPrompt();
}

// Scroll to top helper
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Haptic feedback (if supported)
function hapticFeedback(type = 'light') {
    if (navigator.vibrate) {
        const patterns = {
            light: [10],
            medium: [20],
            heavy: [30]
        };
        navigator.vibrate(patterns[type] || patterns.light);
    }
}

// Add haptic to buttons
function addHapticToButtons() {
    document.querySelectorAll('button, .tab, .bottom-nav-item').forEach(el => {
        el.addEventListener('click', () => hapticFeedback('light'));
    });
}

// Detect if running as PWA
function isPWA() {
    return window.matchMedia('(display-mode: standalone)').matches || 
           window.navigator.standalone === true;
}

// Show PWA-specific UI
if (isPWA()) {
    document.body.classList.add('pwa-mode');
}

// Initialize mobile features
if (window.innerWidth <= 767) {
    document.addEventListener('DOMContentLoaded', () => {
        initBottomNav();
        initPullToRefresh();
        initSwipeGestures();
        addHapticToButtons();
    });
}

// Handle orientation change
window.addEventListener('orientationchange', () => {
    setTimeout(() => {
        window.scrollTo(0, 0);
    }, 100);
});

// Prevent zoom on double tap
let lastTouchEnd = 0;
document.addEventListener('touchend', (e) => {
    const now = Date.now();
    if (now - lastTouchEnd <= 300) {
        e.preventDefault();
    }
    lastTouchEnd = now;
}, false);

// Advanced Gestures
let touchStartX = 0;
let touchEndX = 0;

function handleSwipe() {
    const diff = touchEndX - touchStartX;
    if (Math.abs(diff) > 100) {
        if (diff > 0) {
            // Swipe right - go back
            if (window.history.length > 1) window.history.back();
        } else {
            // Swipe left - open menu
            toggleMobileMenu();
        }
    }
}

document.addEventListener('touchstart', e => {
    touchStartX = e.changedTouches[0].screenX;
});

document.addEventListener('touchend', e => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
});

// Shake to refresh
let lastShake = 0;
if (window.DeviceMotionEvent) {
    window.addEventListener('devicemotion', (e) => {
        const acc = e.accelerationIncludingGravity;
        const threshold = 15;
        
        if (acc && (Math.abs(acc.x) > threshold || Math.abs(acc.y) > threshold || Math.abs(acc.z) > threshold)) {
            const now = Date.now();
            if (now - lastShake > 1000) {
                lastShake = now;
                hapticFeedback('medium');
                refreshData();
            }
        }
    });
}

// Export functions
window.navigateToSection = navigateToSection;
window.toggleMobileMenu = toggleMobileMenu;
window.closeMobileMenu = closeMobileMenu;
window.installPWA = installPWA;
window.dismissPWAPrompt = dismissPWAPrompt;
window.hapticFeedback = hapticFeedback;
