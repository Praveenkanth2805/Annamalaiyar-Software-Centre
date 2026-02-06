// Initialize Material Design Components
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateX(100%)';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#f44336';
                    
                    // Add error message
                    let errorMsg = field.nextElementSibling;
                    if (!errorMsg || !errorMsg.classList.contains('error-msg')) {
                        errorMsg = document.createElement('div');
                        errorMsg.className = 'error-msg';
                        errorMsg.style.color = '#f44336';
                        errorMsg.style.fontSize = '0.85rem';
                        errorMsg.style.marginTop = '5px';
                        errorMsg.textContent = 'This field is required';
                        field.parentNode.appendChild(errorMsg);
                    }
                } else {
                    field.style.borderColor = '#ddd';
                    
                    // Remove error message
                    const errorMsg = field.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('error-msg')) {
                        errorMsg.remove();
                    }
                }
            });

            if (!isValid) {
                e.preventDefault();
                
                // Show error flash
                const flash = document.createElement('div');
                flash.className = 'flash error';
                flash.innerHTML = `
                    <span class="material-icons">error</span>
                    Please fill in all required fields
                `;
                
                const flashContainer = document.querySelector('.flash-messages') || createFlashContainer();
                flashContainer.appendChild(flash);
                
                setTimeout(() => flash.remove(), 5000);
            }
        });
    });

    // Phone number formatting
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 10) value = value.substring(0, 10);
            e.target.value = value;
        });
    });

    // Quantity input validation
    const quantityInputs = document.querySelectorAll('input[type="number"]');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const min = parseInt(input.getAttribute('min')) || 1;
            const max = parseInt(input.getAttribute('max')) || 999;
            let value = parseInt(input.value) || min;
            
            if (value < min) value = min;
            if (value > max) value = max;
            
            input.value = value;
        });
    });

    // Language switch active state
    const langLinks = document.querySelectorAll('.language-switch a');
    langLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            langLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
});

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    container.style.position = 'fixed';
    container.style.top = '80px';
    container.style.right = '20px';
    container.style.zIndex = '1000';
    container.style.maxWidth = '400px';
    document.body.appendChild(container);
    return container;
}

// Price calculation utility
function calculatePrice(unitPrice, quantity) {
    return unitPrice * quantity;
}

// Format currency
function formatCurrency(amount) {
    return '₹' + amount.toLocaleString('en-IN');
}
document.addEventListener('DOMContentLoaded', function () {

    const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');

    sidebarLinks.forEach(link => {

        // Clone node to REMOVE all existing event listeners
        const newLink = link.cloneNode(true);
        link.parentNode.replaceChild(newLink, link);

        // Optional debug
        newLink.addEventListener('click', function () {
            console.log('Navigating to:', this.href);
        });

    });

    console.log('Sidebar links fixed:', sidebarLinks.length);
});
