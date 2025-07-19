const SELECTORS_TO_REMOVE = [
    'button[aria-label="Institutional Access"]'
];

function removeElements() {
    let removedSomething = false;

    for (const selector of SELECTORS_TO_REMOVE) {
        const elements = document.querySelectorAll(selector);
        
        for (const element of elements) {
            if (selector === 'button[aria-label="Institutional Access"]') {
                const parentToRemove = element.closest('div');

                if (parentToRemove) {
                    parentToRemove.remove();
                    console.log('[Embase Extension] Removed parent popover for selector:', selector);
                    removedSomething = true;
                }
            } else {
                element.remove();
                console.log('[Embase Extension] Removed element for selector:', selector);
                removedSomething = true;
            }
        }
    }
    return removedSomething;
}

const observer = new MutationObserver((mutations) => {
    removeElements();
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

removeElements();