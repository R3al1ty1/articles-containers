const SELECTORS_TO_REMOVE = [
    '#header-mobile-panel > div.els-mobile-panel__content > div > div.els-header-institution-info',
    '#popover-8' 
];

function removeElements() {
    let removedSomething = false;

    for (const selector of SELECTORS_TO_REMOVE) {
        const element = document.querySelector(selector);
        
        if (element) {
            if (selector === '#institution-button') {
                const parentToRemove = element.closest('.Popover_target__Edpxk');
                if (parentToRemove) {
                    parentToRemove.remove();
                    console.log('Removed element parent for selector:', selector);
                    removedSomething = true;
                }
            } else {
                element.remove();
                console.log('Removed element for selector:', selector);
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