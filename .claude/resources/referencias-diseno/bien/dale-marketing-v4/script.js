/* ============================================================
   DALE MARKETING v4 — script.js
   GSAP 3.x + ScrollTrigger + Vanilla JS
   ============================================================ */

'use strict';

/* ─── Setup ──────────────────────────────────────────────── */
gsap.registerPlugin(ScrollTrigger);

const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const isMobile = () => window.innerWidth <= 768;

const $  = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

/* ─── Loading Screen ─────────────────────────────────────── */
(function initLoading() {
  const loading = $('#loading');
  const fill    = $('#loadingFill');
  const counter = $('#loadingCounter');

  if (!loading) return;

  if (prefersReducedMotion) {
    loading.style.display = 'none';
    document.body.style.overflow = '';
    return;
  }

  document.body.style.overflow = 'hidden';

  let progress = 0;
  const duration = 1600;
  const interval = 20;
  const step = (interval / duration) * 100;

  const timer = setInterval(() => {
    progress = Math.min(progress + step * (0.8 + Math.random() * 0.6), 100);
    const p = Math.floor(progress);
    if (fill)   fill.style.width   = p + '%';
    if (counter) counter.textContent = p;

    if (progress >= 100) {
      clearInterval(timer);
      setTimeout(() => {
        gsap.to(loading, {
          opacity: 0,
          duration: 0.5,
          ease: 'power2.inOut',
          onComplete: () => {
            loading.style.display = 'none';
            document.body.style.overflow = '';
            initHeroAnimation();
          }
        });
      }, 200);
    }
  }, interval);
})();

/* ─── Custom Cursor ──────────────────────────────────────── */
(function initCursor() {
  if (isMobile() || prefersReducedMotion) return;

  const dot  = $('#cursorDot');
  const ring = $('#cursorRing');
  if (!dot || !ring) return;

  let mx = -100, my = -100;
  let rx = -100, ry = -100;

  document.addEventListener('mousemove', e => {
    mx = e.clientX;
    my = e.clientY;
    gsap.set(dot, { x: mx, y: my });
  });

  gsap.ticker.add(() => {
    rx += (mx - rx) * 0.12;
    ry += (my - ry) * 0.12;
    gsap.set(ring, { x: rx, y: ry });
  });

  // Hover states
  const hoverEls = $$('a, button, .service-card, .faq-question, .testimonial-card, .caso-card');
  hoverEls.forEach(el => {
    el.addEventListener('mouseenter', () => ring.classList.add('hovering'));
    el.addEventListener('mouseleave', () => ring.classList.remove('hovering'));
  });
})();

/* ─── Navbar ─────────────────────────────────────────────── */
(function initNavbar() {
  const navbar    = $('#navbar');
  const hamburger = $('#navHamburger');
  const mobileMenu = $('#navMobile');
  const mobileLinks = $$('.mobile-link, .mobile-cta', mobileMenu);

  if (!navbar) return;

  // Scroll glass effect
  ScrollTrigger.create({
    start: 'top -80',
    onEnter:     () => navbar.classList.add('scrolled'),
    onLeaveBack: () => navbar.classList.remove('scrolled'),
  });

  // Hamburger toggle
  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      const isOpen = hamburger.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', isOpen);
      mobileMenu.classList.toggle('open', isOpen);
      mobileMenu.setAttribute('aria-hidden', !isOpen);
      document.body.style.overflow = isOpen ? 'hidden' : '';
    });

    // Close on link click
    mobileLinks.forEach(link => {
      link.addEventListener('click', () => {
        hamburger.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
        mobileMenu.classList.remove('open');
        mobileMenu.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
      });
    });

    // Close on Escape
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && mobileMenu.classList.contains('open')) {
        hamburger.click();
      }
    });
  }

  // Smooth scroll for nav links
  $$('a[href^="#"]').forEach(link => {
    link.addEventListener('click', e => {
      const target = $(link.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      const offset = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--navbar-h')) || 72;
      const top = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });
})();

/* ─── Hero Animation ─────────────────────────────────────── */
function initHeroAnimation() {
  if (prefersReducedMotion) {
    // Just show everything
    $$('.word').forEach(w => gsap.set(w, { y: 0 }));
    $$('#heroSubline, #heroCtas, #heroBadges').forEach(el => gsap.set(el, { opacity: 1 }));
    return;
  }

  const tl = gsap.timeline({ defaults: { ease: 'power4.out' } });

  // Hero logo draw
  tl.fromTo('#heroLogo', { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.8 });

  // Headline words stagger
  tl.fromTo('.hero-headline .word',
    { y: '110%', opacity: 0 },
    { y: '0%', opacity: 1, duration: 0.75, stagger: 0.06 },
    '-=0.3'
  );

  // Sub elements
  tl.to('#heroSubline', { opacity: 1, y: 0, duration: 0.6 }, '-=0.2');
  tl.to('#heroCtas',    { opacity: 1, y: 0, duration: 0.5 }, '-=0.3');
  tl.to('#heroBadges',  { opacity: 1, y: 0, duration: 0.5 }, '-=0.3');

  // Road lines draw (subtle)
  gsap.fromTo('.hero-road-svg line',
    { strokeDasharray: 600, strokeDashoffset: 600 },
    { strokeDashoffset: 0, duration: 2, stagger: 0.08, ease: 'power2.out', delay: 0.5 }
  );
}

/* ─── Scroll Reveals ─────────────────────────────────────── */
(function initScrollReveals() {
  if (prefersReducedMotion) {
    $$('.reveal').forEach(el => {
      el.style.opacity = '1';
      el.style.transform = 'none';
    });
    return;
  }

  $$('.reveal').forEach((el, i) => {
    // Detect if it's part of a stagger group
    const delay = el.dataset.delay ? parseFloat(el.dataset.delay) : 0;

    gsap.fromTo(el,
      { opacity: 0, y: 44 },
      {
        opacity: 1,
        y: 0,
        duration: 0.8,
        delay,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: el,
          start: 'top 88%',
          toggleActions: 'play none none none',
        }
      }
    );
  });

  // Staggered children inside service grid
  ScrollTrigger.create({
    trigger: '.servicios-grid',
    start: 'top 80%',
    once: true,
    onEnter: () => {
      gsap.fromTo('.service-card',
        { opacity: 0, y: 50 },
        { opacity: 1, y: 0, duration: 0.65, stagger: 0.1, ease: 'power3.out' }
      );
    }
  });

  // Testimonials stagger
  ScrollTrigger.create({
    trigger: '.testimonios-grid',
    start: 'top 82%',
    once: true,
    onEnter: () => {
      gsap.fromTo('.testimonial-card',
        { opacity: 0, y: 40, scale: 0.97 },
        { opacity: 1, y: 0, scale: 1, duration: 0.6, stagger: 0.12, ease: 'power3.out' }
      );
    }
  });

  // Timeline items stagger
  ScrollTrigger.create({
    trigger: '.timeline',
    start: 'top 80%',
    once: true,
    onEnter: () => {
      gsap.fromTo('.timeline-item',
        { opacity: 0, x: -30 },
        { opacity: 1, x: 0, duration: 0.7, stagger: 0.15, ease: 'power3.out' }
      );
    }
  });

  // Map lines draw on scroll
  ScrollTrigger.create({
    trigger: '.red-map-wrap',
    start: 'top 75%',
    once: true,
    onEnter: () => {
      gsap.fromTo('.europe-svg line',
        { strokeDashoffset: 300 },
        { strokeDashoffset: 0, duration: 1.5, stagger: 0.1, ease: 'power2.out' }
      );
      // City dots pop in
      gsap.fromTo('.map-city-dot',
        { scale: 0, transformOrigin: 'center center' },
        { scale: 1, duration: 0.4, stagger: 0.08, ease: 'back.out(2)', delay: 0.3 }
      );
    }
  });

  // Parallax on case study mockups
  if (!isMobile()) {
    $$('.caso-mockup').forEach(mockup => {
      gsap.to(mockup, {
        yPercent: -6,
        ease: 'none',
        scrollTrigger: {
          trigger: mockup,
          start: 'top bottom',
          end: 'bottom top',
          scrub: 1.5,
        }
      });
    });
  }
})();

/* ─── Counter Animations ─────────────────────────────────── */
(function initCounters() {
  if (prefersReducedMotion) return;

  $$('[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target, 10);
    ScrollTrigger.create({
      trigger: el,
      start: 'top 88%',
      once: true,
      onEnter: () => {
        const obj = { val: 0 };
        gsap.to(obj, {
          val: target,
          duration: 1.8,
          ease: 'power2.out',
          onUpdate: () => {
            const rounded = Math.floor(obj.val);
            // Keep existing HTML structure (spans for +, %)
            const spans = el.querySelectorAll('span');
            if (spans.length) {
              // Has prefix/suffix spans — just update text node
              el.childNodes.forEach(node => {
                if (node.nodeType === Node.TEXT_NODE) {
                  node.textContent = rounded;
                }
              });
            } else {
              el.childNodes.forEach(node => {
                if (node.nodeType === Node.TEXT_NODE) node.textContent = rounded;
              });
              // Simple case
              el.textContent = rounded + (el.dataset.suffix || '');
            }
          }
        });
      }
    });
  });

  // Simpler approach for stat numbers
  $$('.stat-number[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target);
    const suffix = el.innerHTML.includes('+') ? '+' : el.innerHTML.includes('%') ? '%' : '';
    const prefixMatch = el.querySelector('.count-prefix');

    ScrollTrigger.create({
      trigger: el,
      start: 'top 90%',
      once: true,
      onEnter: () => {
        const obj = { n: 0 };
        gsap.to(obj, {
          n: target,
          duration: 2,
          ease: 'power2.out',
          onUpdate: () => {
            const val = Math.floor(obj.n);
            if (prefixMatch) {
              el.innerHTML = `<span class="count-prefix">+</span><span data-target="${target}">${val}</span><span>%</span>`;
            } else {
              el.innerHTML = val + suffix;
            }
          }
        });
      }
    });
  });
})();

/* ─── FAQ Accordion ──────────────────────────────────────── */
(function initFAQ() {
  const items = $$('.faq-item');

  items.forEach(item => {
    const btn    = $('button.faq-question', item);
    const answer = $('.faq-answer', item);
    if (!btn || !answer) return;

    btn.addEventListener('click', () => {
      const isOpen = item.classList.contains('open');

      // Close all others
      items.forEach(other => {
        if (other !== item && other.classList.contains('open')) {
          other.classList.remove('open');
          const otherBtn = $('button', other);
          const otherAns = $('.faq-answer', other);
          if (otherBtn) otherBtn.setAttribute('aria-expanded', 'false');
          if (otherAns) {
            if (prefersReducedMotion) {
              otherAns.style.height = '0';
            } else {
              gsap.to(otherAns, { height: 0, duration: 0.3, ease: 'power2.inOut' });
            }
          }
        }
      });

      // Toggle current
      item.classList.toggle('open', !isOpen);
      btn.setAttribute('aria-expanded', !isOpen);

      if (prefersReducedMotion) {
        answer.style.height = isOpen ? '0' : 'auto';
        return;
      }

      if (isOpen) {
        gsap.to(answer, { height: 0, duration: 0.3, ease: 'power2.inOut' });
      } else {
        // Measure natural height
        gsap.set(answer, { height: 'auto' });
        const h = answer.offsetHeight;
        gsap.fromTo(answer, { height: 0 }, { height: h, duration: 0.38, ease: 'power3.out' });
      }
    });

    // Keyboard support
    btn.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        btn.click();
      }
    });
  });
})();

/* ─── Contact Form ───────────────────────────────────────── */
(function initContactForm() {
  const form   = $('#contactForm');
  const submit = $('#formSubmit');
  if (!form || !submit) return;

  form.addEventListener('submit', e => {
    e.preventDefault();

    // Basic validation
    const nombre  = $('#nombre', form);
    const email   = $('#email', form);
    const proyecto = $('#proyecto', form);
    let valid = true;

    [nombre, email, proyecto].forEach(field => {
      if (!field) return;
      const empty = !field.value.trim();
      const invalid = field.type === 'email' && field.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(field.value);
      if (empty || invalid) {
        field.style.borderColor = '#ff4444';
        valid = false;
        // Reset after interaction
        field.addEventListener('input', () => {
          field.style.borderColor = '';
        }, { once: true });
      }
    });

    if (!valid) return;

    // Submit state
    submit.classList.add('loading');
    submit.textContent = 'Enviando…';

    // Simulate async (replace with real fetch)
    setTimeout(() => {
      submit.classList.remove('loading');
      submit.textContent = '¡Mensaje enviado! Te contactamos pronto ✓';
      submit.style.background = '#27c93f';
      submit.style.color = '#fff';
      form.reset();

      setTimeout(() => {
        submit.textContent = 'Dale, hablamos →';
        submit.style.background = '';
        submit.style.color = '';
      }, 4000);
    }, 1400);
  });

  // Focus state label animation
  $$('.form-input, .form-select, .form-textarea', form).forEach(field => {
    field.addEventListener('focus', () => {
      if (!prefersReducedMotion) {
        gsap.to(field, { scale: 1.005, duration: 0.15 });
      }
    });
    field.addEventListener('blur', () => {
      if (!prefersReducedMotion) {
        gsap.to(field, { scale: 1, duration: 0.15 });
      }
    });
  });
})();

/* ─── Parallax hero scroll ───────────────────────────────── */
(function initHeroParallax() {
  if (prefersReducedMotion || isMobile()) return;

  gsap.to('.hero-logo-wrap', {
    yPercent: -15,
    ease: 'none',
    scrollTrigger: {
      trigger: '.hero',
      start: 'top top',
      end: 'bottom top',
      scrub: 1,
    }
  });

  gsap.to('.hero-content', {
    yPercent: -8,
    ease: 'none',
    scrollTrigger: {
      trigger: '.hero',
      start: 'top top',
      end: 'bottom top',
      scrub: 1.5,
    }
  });

  // Road lines parallax
  gsap.to('.hero-road-wrap', {
    yPercent: 20,
    ease: 'none',
    scrollTrigger: {
      trigger: '.hero',
      start: 'top top',
      end: 'bottom top',
      scrub: 2,
    }
  });
})();

/* ─── Section label animate ──────────────────────────────── */
(function initSectionLabels() {
  if (prefersReducedMotion) return;

  $$('.section-label').forEach(label => {
    gsap.fromTo(label,
      { opacity: 0, x: -20 },
      {
        opacity: 1,
        x: 0,
        duration: 0.6,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: label,
          start: 'top 90%',
          toggleActions: 'play none none none',
        }
      }
    );
  });
})();

/* ─── Service cards hover glow ───────────────────────────── */
(function initServiceHover() {
  if (prefersReducedMotion) return;

  $$('.service-card').forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width - 0.5) * 20;
      const y = ((e.clientY - rect.top) / rect.height - 0.5) * 20;
      gsap.to(card, { rotateX: -y * 0.3, rotateY: x * 0.3, duration: 0.3, ease: 'power1.out', transformPerspective: 800 });
    });
    card.addEventListener('mouseleave', () => {
      gsap.to(card, { rotateX: 0, rotateY: 0, duration: 0.5, ease: 'power2.out' });
    });
  });
})();

/* ─── Map pulse animation ────────────────────────────────── */
(function initMapPulse() {
  if (prefersReducedMotion) return;

  const pulseRing = document.querySelector('.pulse-ring');
  if (!pulseRing) return;

  gsap.to(pulseRing, {
    attr: { r: 28 },
    opacity: 0,
    duration: 1.8,
    ease: 'power2.out',
    repeat: -1,
    repeatDelay: 0.5,
    onRepeat: () => {
      gsap.set(pulseRing, { attr: { r: 18 }, opacity: 0.35 });
    }
  });
})();

/* ─── Scroll progress bar ────────────────────────────────── */
(function initScrollProgress() {
  const bar = document.createElement('div');
  bar.style.cssText = `
    position: fixed;
    top: 0; left: 0;
    height: 2px;
    width: 0%;
    background: linear-gradient(to right, var(--mint), var(--gold));
    z-index: 9999;
    transition: width 0.1s linear;
    pointer-events: none;
  `;
  document.body.appendChild(bar);

  window.addEventListener('scroll', () => {
    const scrolled = window.scrollY;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.width = (max > 0 ? (scrolled / max) * 100 : 0) + '%';
  }, { passive: true });
})();

/* ─── Active nav link highlight ──────────────────────────── */
(function initActiveNav() {
  const sections = $$('section[id], div[id].stats-bar');
  const navLinks = $$('.nav-links a');

  if (!navLinks.length) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const id = entry.target.id;
      navLinks.forEach(link => {
        const href = link.getAttribute('href');
        const active = href === '#' + id || (id === 'quienes' && href === '#quienes');
        link.style.color = active ? 'var(--mint)' : '';
      });
    });
  }, { rootMargin: '-40% 0px -50% 0px' });

  sections.forEach(s => observer.observe(s));
})();

/* ─── Resize handler ─────────────────────────────────────── */
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    ScrollTrigger.refresh();
  }, 250);
}, { passive: true });
