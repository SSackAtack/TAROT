/**
 * TarotKA — Main JavaScript
 * Nawigacja, animacje scroll, FAQ, Karta Dnia, cząsteczki
 */

import './style.css';

// ═══════════ NAVIGATION ═══════════
function initNavigation() {
  const nav = document.getElementById('main-nav');
  const toggle = document.getElementById('nav-toggle');
  const links = document.getElementById('nav-links');

  // Scroll effect
  let lastScroll = 0;
  window.addEventListener('scroll', () => {
    const currentScroll = window.scrollY;
    nav.classList.toggle('nav--scrolled', currentScroll > 60);
    lastScroll = currentScroll;
  });

  // Mobile toggle
  toggle?.addEventListener('click', () => {
    links.classList.toggle('nav__links--open');
  });

  // Close on link click
  links?.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      links.classList.remove('nav__links--open');
    });
  });
}

// ═══════════ SCROLL ANIMATIONS ═══════════
function initScrollAnimations() {
  const elements = document.querySelectorAll('[data-animate]');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const delay = parseInt(entry.target.dataset.delay) || 0;
        setTimeout(() => {
          entry.target.classList.add('animated');
        }, delay);
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.15,
    rootMargin: '0px 0px -50px 0px'
  });

  elements.forEach(el => observer.observe(el));
}

// ═══════════ FAQ ACCORDION ═══════════
function initFAQ() {
  const items = document.querySelectorAll('.faq__item');

  items.forEach(item => {
    const question = item.querySelector('.faq__question');
    question?.addEventListener('click', () => {
      const isOpen = item.classList.contains('faq__item--open');

      // Close all
      items.forEach(i => i.classList.remove('faq__item--open'));

      // Open clicked (if was closed)
      if (!isOpen) {
        item.classList.add('faq__item--open');
      }
    });
  });
}

// ═══════════ DAILY CARD ═══════════
const DAILY_CARDS = [
  { id: '00', name: 'Głupiec', message: 'Dziś jest dobry dzień na nowe początki. Głupiec zachęca do skoku wiary — zaufaj intuicji i ruszaj w nieznane. Nie musisz mieć wszystkiego zaplanowanego.' },
  { id: '01', name: 'Mag', message: 'Masz wszystkie narzędzia, których potrzebujesz. Mag mówi: działaj świadomie, połącz zamiar z czynem. Twoja wola ma dziś wyjątkową moc.' },
  { id: '06', name: 'Kochankowie', message: 'Dzień decyzji serca. Kochankowie przypominają, że autentyczny wybór wymaga odwagi. Słuchaj tego, co czujesz — nie tego, co "powinnaś".' },
  { id: '13', name: 'Śmierć', message: 'Coś się kończy, żeby mogło się zacząć. Śmierć to karta transformacji — pozwól odejść temu, co już nie służy. Miejsce na nowe otworzy się samo.' },
  { id: '17', name: 'Gwiazda', message: 'Gwiazda mówi o nadziei i inspiracji. Dziś jest dobry dzień na snucie planów — Twoje marzenia mają mocny fundament. Zaufaj procesowi.' },
];

function initDailyCard() {
  const card = document.getElementById('daily-card-flip');
  const img = document.getElementById('daily-card-img');
  const name = document.getElementById('daily-card-name');
  const message = document.getElementById('daily-card-message');
  const interpretation = document.getElementById('daily-card-interpretation');
  
  // Elementy generatora wideo do resetu
  const btnGenerate = document.getElementById('btn-generate-video');
  const progress = document.getElementById('video-progress');
  const bar = document.getElementById('video-bar');
  const result = document.getElementById('video-result');

  if (!card) return;

  // Pick card based on day
  const dayOfYear = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0)) / 86400000);
  const todayCard = DAILY_CARDS[dayOfYear % DAILY_CARDS.length];

  img.src = `/images/cards/RWS_${todayCard.id}_thumb.webp`;
  img.alt = todayCard.name;
  name.textContent = todayCard.name;
  message.textContent = ''; // startuje puste dla typewriter

  let typewriterTimeout = null;
  let isTyping = false;

  function startTypewriter(element, text) {
    element.textContent = '';
    element.classList.add('typewriter-cursor');
    let i = 0;
    isTyping = true;
    
    if (typewriterTimeout) clearTimeout(typewriterTimeout);
    
    function type() {
      if (i < text.length) {
        element.textContent += text.charAt(i);
        i++;
        typewriterTimeout = setTimeout(type, 25);
      } else {
        element.classList.remove('typewriter-cursor');
        isTyping = false;
      }
    }
    type();
  }

  card.addEventListener('click', () => {
    card.classList.toggle('daily-card__card--flipped');

    if (card.classList.contains('daily-card__card--flipped')) {
      setTimeout(() => {
        interpretation.classList.add('daily-card__interpretation--visible');
        startTypewriter(message, todayCard.message);
      }, 500);
    } else {
      if (typewriterTimeout) clearTimeout(typewriterTimeout);
      isTyping = false;
      message.textContent = '';
      message.classList.remove('typewriter-cursor');
      interpretation.classList.remove('daily-card__interpretation--visible');
      
      // Reset generatora wideo
      if (btnGenerate) btnGenerate.style.display = 'inline-flex';
      if (progress) progress.style.display = 'none';
      if (bar) bar.style.width = '0%';
      if (result) result.style.display = 'none';
    }
  });
}

// ═══════════ PARTICLES ═══════════
function initParticles() {
  const container = document.getElementById('hero-particles');
  if (!container) return;

  const canvas = document.createElement('canvas');
  container.appendChild(canvas);
  const ctx = canvas.getContext('2d');

  let width, height;
  const particles = [];
  const PARTICLE_COUNT = 45;

  function resize() {
    width = canvas.width = container.offsetWidth;
    height = canvas.height = container.offsetHeight;
  }

  // Gothic Romantic Autumn palette for particles
  const PARTICLE_COLORS = [
    { r: 184, g: 150, b: 62 },   // antyczne złoto
    { r: 212, g: 182, b: 92 },   // jasne złoto
    { r: 107, g: 45, b: 62 },    // burgundowy
    { r: 58, g: 74, b: 46 },     // ciemna zieleń
    { r: 138, g: 138, b: 154 },  // srebrzyste
  ];

  class Particle {
    constructor() {
      this.reset();
    }

    reset() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.size = Math.random() * 2 + 0.3;
      this.speedX = (Math.random() - 0.5) * 0.15;
      this.speedY = (Math.random() - 0.5) * 0.15;
      this.opacity = Math.random() * 0.35 + 0.05;
      this.pulseSpeed = Math.random() * 0.015 + 0.003;
      this.pulseOffset = Math.random() * Math.PI * 2;
      // Weighted: 60% gold, 15% burgundy, 10% forest, 15% silver
      const roll = Math.random();
      const color = roll < 0.35 ? PARTICLE_COLORS[0]
                  : roll < 0.6  ? PARTICLE_COLORS[1]
                  : roll < 0.75 ? PARTICLE_COLORS[2]
                  : roll < 0.85 ? PARTICLE_COLORS[3]
                  :               PARTICLE_COLORS[4];
      this.r = color.r;
      this.g = color.g;
      this.b = color.b;
    }

    update(time) {
      this.x += this.speedX;
      this.y += this.speedY;

      // Wrap
      if (this.x < -10) this.x = width + 10;
      if (this.x > width + 10) this.x = -10;
      if (this.y < -10) this.y = height + 10;
      if (this.y > height + 10) this.y = -10;

      // Pulse
      this.currentOpacity = this.opacity * (0.5 + 0.5 * Math.sin(time * this.pulseSpeed + this.pulseOffset));
    }

    draw(ctx) {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${this.r}, ${this.g}, ${this.b}, ${this.currentOpacity})`;
      ctx.fill();

      // Glow
      if (this.size > 1.5) {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size * 3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${this.r}, ${this.g}, ${this.b}, ${this.currentOpacity * 0.15})`;
        ctx.fill();
      }
    }
  }

  resize();
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push(new Particle());
  }

  let animFrame;
  function animate(time) {
    ctx.clearRect(0, 0, width, height);
    particles.forEach(p => {
      p.update(time);
      p.draw(ctx);
    });
    animFrame = requestAnimationFrame(animate);
  }

  // Only animate when hero is visible
  const heroObserver = new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting) {
      if (!animFrame) animate(0);
    } else {
      if (animFrame) {
        cancelAnimationFrame(animFrame);
        animFrame = null;
      }
    }
  });
  heroObserver.observe(document.getElementById('hero'));

  window.addEventListener('resize', resize);
  animate(0);
}

// ═══════════ CONTACT FORM ═══════════
function initContactForm() {
  const form = document.getElementById('contact-form');
  const success = document.getElementById('form-success');

  form?.addEventListener('submit', (e) => {
    e.preventDefault();

    // Simulate submit (replace with Firebase later)
    const btn = document.getElementById('contact-submit');
    btn.textContent = 'Wysyłanie...';
    btn.disabled = true;

    setTimeout(() => {
      form.reset();
      btn.textContent = 'Wyślij wiadomość';
      btn.disabled = false;
      success.classList.add('form__success--visible');

      setTimeout(() => {
        success.classList.remove('form__success--visible');
      }, 5000);
    }, 1200);
  });
}

// ═══════════ SMOOTH ANCHOR SCROLL ═══════════
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        e.preventDefault();
        const offset = 80; // nav height
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });
}

// ═══════════ HERO PARALLAX FLOATING CARDS ═══════════
function initHeroParallax() {
  const cards = document.querySelectorAll('.hero__float-card');
  if (!cards.length) return;

  let mouseX = 0, mouseY = 0;
  let currentX = 0, currentY = 0;

  document.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  function animate() {
    currentX += (mouseX - currentX) * 0.05;
    currentY += (mouseY - currentY) * 0.05;

    cards.forEach(card => {
      const speed = parseFloat(card.dataset.speed) || 0.03;
      const x = currentX * speed * 800;
      const y = currentY * speed * 800;
      const baseRotation = parseFloat(card.dataset.rotate) || 0;
      card.style.transform = `translate(${x}px, ${y}px) rotate(${baseRotation}deg)`;
    });
    requestAnimationFrame(animate);
  }
  animate();
}

// ═══════════ VIDEO GENERATOR (html-video) ═══════════
function initVideoGenerator() {
  const btnGenerate = document.getElementById('btn-generate-video');
  const progress = document.getElementById('video-progress');
  const bar = document.getElementById('video-bar');
  const status = document.getElementById('video-status');
  const result = document.getElementById('video-result');

  if (!btnGenerate) return;

  const steps = [
    { percent: 15, text: 'Łączenie z silnikiem html-video...' },
    { percent: 35, text: 'Wczytywanie szablonu frame-light-leak-cinema...' },
    { percent: 55, text: 'Wstrzykiwanie tekstu interpretacji...' },
    { percent: 75, text: 'Generowanie ścieżki dźwiękowej z lektorem AI...' },
    { percent: 90, text: 'Kompresja wideo MP4 przez FFmpeg...' },
    { percent: 100, text: 'Gotowe!' }
  ];

  btnGenerate.addEventListener('click', () => {
    btnGenerate.style.display = 'none';
    progress.style.display = 'block';

    let stepIdx = 0;

    function runStep() {
      if (stepIdx < steps.length) {
        const step = steps[stepIdx];
        bar.style.width = `${step.percent}%`;
        status.textContent = step.text;
        stepIdx++;
        setTimeout(runStep, stepIdx === steps.length ? 1500 : 1000);
      } else {
        progress.style.display = 'none';
        result.style.display = 'block';
      }
    }
    runStep();
  });
}

// ═══════════ INIT ═══════════
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initScrollAnimations();
  initFAQ();
  initDailyCard();
  initParticles();
  initContactForm();
  initSmoothScroll();
  initHeroParallax();
  initVideoGenerator();
});
