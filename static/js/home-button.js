/**
 * Universal Home Button Component
 * Automatically adds a home button to all pages
 */

(function() {
    'use strict';
    
    // Don't add home button on landing page
    if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
        return;
    }
    
    // Create home button
    const homeButton = document.createElement('a');
    homeButton.href = '/';
    homeButton.className = 'universal-home-btn';
    homeButton.innerHTML = '🏠 Home';
    homeButton.title = 'Go to Home';
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        .universal-home-btn {
            position: fixed;
            top: 20px;
            left: 20px;
            background: linear-gradient(135deg, #e94560 0%, #c23b52 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            box-shadow: 0 4px 15px rgba(233, 69, 96, 0.4);
            z-index: 9999;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .universal-home-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(233, 69, 96, 0.5);
        }
        
        .universal-home-btn:active {
            transform: translateY(0);
        }
        
        @media (max-width: 768px) {
            .universal-home-btn {
                top: 10px;
                left: 10px;
                padding: 10px 18px;
                font-size: 13px;
            }
        }
    `;
    
    // Add to page
    document.head.appendChild(style);
    document.body.appendChild(homeButton);
    
    console.log('✅ Universal home button loaded');
})();
