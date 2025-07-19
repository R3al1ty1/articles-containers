const SELECTORS_TO_REMOVE = [
    'app-ins-logo',
    '#FRLinkTa-link-image-url-0'
];

function removeElements() {
    for (const selector of SELECTORS_TO_REMOVE) {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            element.remove();
            console.log('Removed element for selector:', selector);
        });
    }
}

const observer = new MutationObserver((mutations) => {
    removeElements();
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Первоначальный вызов на случай, если элемент уже есть на странице
removeElements();