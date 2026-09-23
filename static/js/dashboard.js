// Flowbite's drawer is mobile-only; keep desktop navigation accessible.
window.addEventListener('load', () => {
  const sidebar = document.getElementById('dashboard-sidebar');
  if (!sidebar) return;
  const trigger = document.querySelector('[data-drawer-toggle="dashboard-sidebar"]');
  const drawer = window.FlowbiteInstances.getInstance('Drawer', 'dashboard-sidebar');
  const desktop = window.matchMedia('(min-width: 64rem)');
  const focusable = () => [...sidebar.querySelectorAll('a, button, select')]
    .filter(element => !element.disabled && element.getClientRects().length);
  let wasOpen = false;
  const sync = () => {
    const open = !desktop.matches && drawer.isVisible();
    sidebar.inert = !desktop.matches && !open;
    trigger.setAttribute('aria-expanded', String(open));
    if (desktop.matches) {
      if (sidebar.hasAttribute('aria-hidden')) sidebar.removeAttribute('aria-hidden');
      sidebar.removeAttribute('aria-modal');
      sidebar.removeAttribute('role');
    }
    if (open && !wasOpen) focusable()[0]?.focus();
    if (!open && wasOpen && !desktop.matches) trigger.focus();
    wasOpen = open;
  };
  new MutationObserver(sync).observe(sidebar, { attributes: true, attributeFilter: ['aria-hidden'] });
  desktop.addEventListener('change', () => {
    drawer.hide();
    sync();
  });
  document.addEventListener('keydown', event => {
    if (desktop.matches || !drawer.isVisible() || event.key !== 'Tab') return;
    const items = focusable();
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && (document.activeElement === first || !sidebar.contains(document.activeElement))) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !sidebar.contains(document.activeElement))) {
      event.preventDefault();
      first?.focus();
    }
  });
  sync();
});
