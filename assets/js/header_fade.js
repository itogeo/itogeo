const MAX_FADE = 0.8;

const updateNavBackground = (nav) => {
  if (!nav) return;
  const scrollY = window.scrollY;
  const opacity = Math.max(1 - scrollY / 400, MAX_FADE);
  nav.style.background = `rgba(255, 255, 255, ${opacity})`;
};

const initNavInteractions = () => {
  const nav = document.querySelector("nav");
  if (!nav || nav.dataset.navInitialized === "true") {
    return;
  }

  nav.dataset.navInitialized = "true";
  updateNavBackground(nav);

  nav.addEventListener("mouseenter", () => {
    nav.style.background = "rgba(255, 255, 255, 0.98)";
  });

  nav.addEventListener("mouseleave", () => {
    updateNavBackground(nav);
  });

  const navMenu = nav.querySelector("#nav-menu");
  const navToggle = nav.querySelector(".nav-toggle");

  if (navMenu && navToggle) {
    navToggle.addEventListener("click", () => {
      const isOpen = navMenu.classList.toggle("open");
      navToggle.classList.toggle("is-open", isOpen);
      navToggle.setAttribute("aria-expanded", isOpen);
    });

    navMenu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.innerWidth <= 768) {
          navMenu.classList.remove("open");
          navToggle.classList.remove("is-open");
          navToggle.setAttribute("aria-expanded", "false");
        }
      });
    });
  }
};

window.addEventListener("scroll", () => {
  const nav = document.querySelector("nav");
  updateNavBackground(nav);
});

window.addEventListener("resize", () => {
  const nav = document.querySelector("nav");
  if (!nav) return;
  const navMenu = nav.querySelector("#nav-menu");
  const navToggle = nav.querySelector(".nav-toggle");
  if (navMenu && navToggle && window.innerWidth > 768) {
    navMenu.classList.remove("open");
    navToggle.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
  }
});

document.addEventListener("DOMContentLoaded", initNavInteractions);
document.addEventListener("partialsLoaded", initNavInteractions);
