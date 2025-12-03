
//Меню бургер
function toggleSidebar() {
        const sidebar = document.getElementById("sidebar");
        const btn = document.getElementById("menuBtn");

        sidebar.classList.toggle("open");
        btn.classList.toggle("open");
    }