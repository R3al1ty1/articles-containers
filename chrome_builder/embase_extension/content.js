const SELECTORS_TO_REMOVE = [
    'button[aria-label="Institutional Access"]',

    '#header-btn-institution'
];

function removeElements() {
    for (const selector of SELECTORS_TO_REMOVE) {
        const elements = document.querySelectorAll(selector);
        
        for (const element of elements) {

            if (selector === 'button[aria-label="Institutional Access"]') {
                const parentToRemove = element.closest('div'); 
                if (parentToRemove) {
                    parentToRemove.remove();
                    console.log('[Embase Extension] Removed parent popover for selector:', selector);
                }
            } 

            else if (selector === '#header-btn-institution') {
                const parentToRemove = document.querySelector('#header-popover-institution');
                
                if (parentToRemove) {
                    parentToRemove.remove();
                    console.log('[Embase Extension] Removed header institution popover using trigger:', selector);
                } else {
                    console.log('[Embase Extension] Trigger #header-btn-institution found, but #header-popover-institution was not. Nothing removed.');
                }
            }

            else {
                element.remove();
                console.log('[Embase Extension] Removed simple element for selector:', selector);
            }
        }
    }
}

const observer = new MutationObserver((mutations) => {
    removeElements();
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

removeElements();