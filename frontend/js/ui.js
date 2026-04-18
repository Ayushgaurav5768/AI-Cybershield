document.addEventListener("DOMContentLoaded", () => {
    const nav = document.querySelector(".top-nav");
    const toggle = document.getElementById("navToggle");
    const links = document.querySelectorAll("#primaryNav a");

    if (!nav || !toggle) {
        return;
    }

    const closeMenu = () => {
        nav.classList.remove("menu-open");
        toggle.setAttribute("aria-expanded", "false");
    };

    const openMenu = () => {
        nav.classList.add("menu-open");
        toggle.setAttribute("aria-expanded", "true");
    };

    toggle.addEventListener("click", () => {
        if (nav.classList.contains("menu-open")) {
            closeMenu();
            return;
        }
        openMenu();
    });

    links.forEach((link) => {
        link.addEventListener("click", () => {
            closeMenu();
        });
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 760) {
            closeMenu();
        }
    });
});
