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
