/* Quiet, progressive motion. All content remains usable without JavaScript. */
(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) return;
  const targets = document.querySelectorAll('.section-heading, .apartment-card, .comfort-grid article, .property-arrival, .cta, .metrics article, .dashboard-main > .panel, .dash-columns > .panel');
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.remove('motion-pending');
      observer.unobserve(entry.target);
    });
  }, {threshold: 0.06, rootMargin: '0px 0px 30px 0px'});
  targets.forEach((element, index) => {
    // Do not hide anything already visible when the script starts.
    if (element.getBoundingClientRect().top < window.innerHeight - 20) return;
    element.classList.add('motion-reveal', 'motion-pending');
    element.style.setProperty('--motion-delay', `${index % 2 * 65}ms`);
    observer.observe(element);
  });
  // Anchor jumps, browser find and keyboard navigation must expose content at once.
  document.addEventListener('focusin', event => event.target.closest('.motion-pending')?.classList.remove('motion-pending'));
  window.addEventListener('beforeprint', () => targets.forEach(element => element.classList.remove('motion-pending')));
})();
