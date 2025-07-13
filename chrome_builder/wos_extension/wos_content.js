const SELECTORS_TO_REMOVE = [
    'app-ins-logo' // Самый надежный селектор для удаления всего блока с логотипом
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