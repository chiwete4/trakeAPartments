(() => {
  const main = document.getElementById('apartment-main-photo');
  const caption = document.getElementById('photo-caption');
  if (!main) return;
  document.querySelectorAll('.gallery-photo').forEach(button => {
    button.addEventListener('click', () => {
      main.src = button.dataset.full;
      main.alt = button.dataset.caption;
      caption.textContent = button.dataset.caption;
      document.querySelectorAll('.gallery-photo').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
      main.scrollIntoView({behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block:'center'});
    });
  });
})();
