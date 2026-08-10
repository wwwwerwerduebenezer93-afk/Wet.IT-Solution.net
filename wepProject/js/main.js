(function () {
  "use strict";

  const navToggle = document.querySelector(".nav__toggle");
  const navMenu = document.querySelector(".nav__menu");
  const navLinks = document.querySelectorAll(".nav__link");
  const themeToggle = document.querySelector(".theme-toggle");
  const contactForm = document.getElementById("contact-form");
  const yearEl = document.getElementById("year");
  const sections = document.querySelectorAll("section[id]");

  /* ---- Footer year ---- */
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  /* ---- Hamburger menu ---- */
  function closeMenu() {
    navToggle.setAttribute("aria-expanded", "false");
    navToggle.setAttribute("aria-label", "Open navigation menu");
    navMenu.classList.remove("is-open");
  }

  function openMenu() {
    navToggle.setAttribute("aria-expanded", "true");
    navToggle.setAttribute("aria-label", "Close navigation menu");
    navMenu.classList.add("is-open");
  }

  navToggle.addEventListener("click", function () {
    const isOpen = navToggle.getAttribute("aria-expanded") === "true";
    isOpen ? closeMenu() : openMenu();
  });

  navLinks.forEach(function (link) {
    link.addEventListener("click", closeMenu);
  });

  document.addEventListener("click", function (event) {
    if (!navMenu.classList.contains("is-open")) return;
    if (!event.target.closest(".nav")) {
      closeMenu();
    }
  });

  window.addEventListener("resize", function () {
    if (window.innerWidth >= 768) {
      closeMenu();
    }
  });

  /* ---- Active nav link on scroll ---- */
  function setActiveNavLink() {
    const scrollPos = window.scrollY + 120;

    sections.forEach(function (section) {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      const id = section.getAttribute("id");

      if (scrollPos >= top && scrollPos < top + height) {
        navLinks.forEach(function (link) {
          link.classList.toggle("is-active", link.getAttribute("href") === "#" + id);
        });
      }
    });
  }

  window.addEventListener("scroll", setActiveNavLink);
  setActiveNavLink();

  /* ---- Light / dark mode toggle ---- */
  const THEME_KEY = "portfolio-theme";

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    themeToggle.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
    themeToggle.setAttribute(
      "aria-label",
      theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
    );
  }

  function getPreferredTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  applyTheme(getPreferredTheme());

  themeToggle.addEventListener("click", function () {
    const current = document.documentElement.getAttribute("data-theme") || "light";
    const next = current === "dark" ? "light" : "dark";
    applyTheme(next);
    localStorage.setItem(THEME_KEY, next);
  });

  /* ---- Contact form validation ---- */
  const validators = {
    name: function (value) {
      if (!value.trim()) return "Full name is required.";
      if (value.trim().length < 2) return "Name must be at least 2 characters.";
      return "";
    },
    email: function (value) {
      if (!value.trim()) return "Email address is required.";
      const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!pattern.test(value.trim())) return "Please enter a valid email address.";
      return "";
    },
    subject: function (value) {
      if (!value.trim()) return "Subject is required.";
      return "";
    },
    message: function (value) {
      if (!value.trim()) return "Message is required.";
      if (value.trim().length < 10) return "Message must be at least 10 characters.";
      return "";
    },
  };

  function showFieldError(field, message) {
    const errorEl = document.getElementById(field.id + "-error");
    field.classList.toggle("is-invalid", Boolean(message));
    if (errorEl) errorEl.textContent = message;
  }

  function validateField(field) {
    const validator = validators[field.name];
    if (!validator) return true;
    const message = validator(field.value);
    showFieldError(field, message);
    return message === "";
  }

  contactForm.querySelectorAll(".form-input").forEach(function (field) {
    field.addEventListener("blur", function () {
      validateField(field);
    });

    field.addEventListener("input", function () {
      if (field.classList.contains("is-invalid")) {
        validateField(field);
      }
    });
  });

  contactForm.addEventListener("submit", function (event) {
    event.preventDefault();

    const fields = contactForm.querySelectorAll(".form-input");
    let isValid = true;

    fields.forEach(function (field) {
      if (!validateField(field)) {
        isValid = false;
      }
    });

    const successEl = document.getElementById("form-success");

    if (isValid) {
      successEl.hidden = false;
      successEl.textContent =
        "Thank you, " +
        contactForm.name.value.trim() +
        "! Your message has been validated and is ready to send.";
      contactForm.reset();
      fields.forEach(function (field) {
        showFieldError(field, "");
      });
    } else {
      successEl.hidden = true;
      const firstInvalid = contactForm.querySelector(".is-invalid");
      if (firstInvalid) firstInvalid.focus();
    }
  });
})();
