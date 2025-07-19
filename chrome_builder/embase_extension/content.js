function removeAnnoyingElements() {
    const institutionInfoSelector = '.els-header-institution-info';
    const institutionInfoElement = document.querySelector(institutionInfoSelector);
    if (institutionInfoElement) {
        institutionInfoElement.remove();
        console.log('[Extension] Removed institution info block:', institutionInfoElement);
    }

    const popoverCloseButtonSelector = 'button[aria-label="Close"], button[aria-label="Dismiss"], button[aria-label="Dismiss tip"]';
    
    const closeButton = document.querySelector(popoverCloseButtonSelector);
    
    if (closeButton) {
        const popover = closeButton.closest('div[role="dialog"], div[role="tooltip"]');
        
        if (popover) {
            popover.remove();
            console.log('[Extension] Removed parent popover:', popover);
        } else {
            const parent = closeButton.parentElement;
            parent.remove();
            console.log('[Extension] Removed direct parent of the close button:', parent);
        }
    }
}

const observer = new MutationObserver((mutations) => {
    removeAnnoyingElements();
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

console.log('[Extension] Loaded and running. Performing initial cleanup.');
removeAnnoyingElements();