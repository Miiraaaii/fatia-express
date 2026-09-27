const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[char]));
const brl = value => new Intl.NumberFormat('pt-BR', {style: 'currency', currency: 'BRL'}).format(value);
const cents = value => Math.round((Number(value) + Number.EPSILON) * 100);
const normalize = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const paths = {
  pizza: '<path d="M4 5Q12 0 20 5L12 22Z"/><path d="M4 5Q12 1 20 5" stroke-width="3"/><circle cx="10" cy="9" r="1"/><circle cx="14" cy="12" r="1"/><path d="m10 15 1 1"/>',
  bag: '<path d="M5 7h14l1 14H4L5 7Z"/><path d="M8 8V6a4 4 0 0 1 8 0v2"/>',
  'arrow-right': '<path d="M4 12h16m-6-6 6 6-6 6"/>',
  'arrow-up': '<path d="M12 20V4m-6 6 6-6 6 6"/>',
  heart: '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>',
  oven: '<path d="M3 21V11a9 9 0 0 1 18 0v10H3Z"/><path d="M7 21v-8a5 5 0 0 1 10 0v8M1 21h22M9 17h6M12 1v3"/>',
  scooter: '<circle cx="5" cy="18" r="3"/><circle cx="19" cy="18" r="3"/><path d="M8 18h5l4-10-2-5h-3M3 11h7l3 7M3 8h6M17 8h4"/>',
  wallet: '<rect x="3" y="5" width="19" height="15" rx="2"/><path d="M3 5V3h15v2M22 11h-6v4h6"/><path d="M18 13h.01"/>',
  sparkles: '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Zm8 0v4m-2-2h4"/>',
  search: '<circle cx="10.5" cy="10.5" r="7.5"/><path d="m16 16 5 5"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  minus: '<path d="M5 12h14"/>',
  store: '<path d="M3 10v11h18V10M2 3h20v5a3 3 0 0 1-5 2 3 3 0 0 1-5 0 3 3 0 0 1-5 0 3 3 0 0 1-5-2V3ZM9 21v-7h6v7"/>',
  card: '<rect x="2" y="4" width="20" height="16" rx="3"/><path d="M2 9h20M6 15h4"/>',
  lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V6a4 4 0 0 1 8 0v4M12 14v3"/>',
  drink: '<path d="m6 7 2 15h9l2-15H6Zm-2 0h17M12 7l2-5h4"/><path d="M8 12h9"/>',
  sweet: '<path d="M3 13h18v8H3zM6 13V9h12v4M4 17q2 3 4 0 2 3 4 0 2 3 4 0 2 3 4 0M12 9V6M12 2q-4 4 0 4 4 0 0-4"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  refresh: '<path d="M20 7a9 9 0 1 0 1 9M20 3v5h-5"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  trash: '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/>',
};
const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.pizza}</svg>`;
$$('[data-icon]').forEach(element => { element.innerHTML = icon(element.dataset.icon); });

const KEYS = {cart: 'fatia.cart.v1', orders: 'fatia.orders.v1', delivery: 'fatia.delivery.v1', pending: 'fatia.pending.v1'};
function read(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } }
function write(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch { return false; } }
const storedOrders = read(KEYS.orders, []);
const state = {
  catalog: null, cart: [], category: 0, query: '', sort: 'menu',
  delivery: read(KEYS.delivery, 'ENTREGA') === 'BALCAO' ? 'BALCAO' : 'ENTREGA',
  orders: Array.isArray(storedOrders) ? storedOrders.filter(o => Number.isInteger(o?.id) && typeof o?.token === 'string').slice(0, 20) : [],
  receipts: new Map(), pending: read(KEYS.pending, {}), selected: null, submitting: false, tracking: false, toastTimer: null,
};
function toast(message) { const element = $('#toast'); element.textContent = message; element.classList.add('visible'); clearTimeout(state.toastTimer); state.toastTimer = setTimeout(() => element.classList.remove('visible'), 3500); }
function showDialog(id) { const dialog = $(`#${id}`); if (!dialog.open) dialog.showModal(); }
function closeDialog(id) { if (id === 'checkout-dialog' && state.submitting) return; $(`#${id}`).close(); }
$$('dialog').forEach(dialog => { dialog.addEventListener('click', event => { if (event.target === dialog) { const rect = dialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) closeDialog(dialog.id); } }); });
$('#checkout-dialog').addEventListener('cancel', event => { if (state.submitting) event.preventDefault(); });
document.addEventListener('click', event => { const close = event.target.closest('[data-close]'); if (close) closeDialog(close.dataset.close); });

async function api(path, options = {}) {
  let response;
  try { response = await fetch(path, {...options, signal: AbortSignal.timeout(15000)}); }
  catch { throw new Error('Não foi possível conectar. Confira sua conexão e tente novamente.'); }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) { const error = new Error(data.error || 'Não foi possível concluir agora. Tente novamente.'); error.field = data.field; error.status = response.status; throw error; }
  return data;
}

const photoByName = {'Calabresa Especial': 'calabresa.png', 'Marguerita Clássica': 'marguerita.png', 'Frango com Catupiry': 'frango.png', 'Quatro Queijos Nobres': 'queijos.png', 'Pepperoni Supremo': 'hero.png'};
const featuredNames = ['Calabresa Especial', 'Marguerita Clássica', 'Frango com Catupiry', 'Quatro Queijos Nobres', 'Pepperoni Supremo'];
const categoryNames = {1: 'Tradicionais', 2: 'Especiais', 3: 'Doces', 4: 'Bebidas'};
const categoryIcons = {1: 'pizza', 2: 'sparkles', 3: 'sweet', 4: 'drink'};
function getProduct(id) { return state.catalog?.products.find(p => p.id === id); }
function itemDetails(item) { return {product: getProduct(item.product_id), size: state.catalog?.sizes.find(s => s.id === item.size_id), crust: state.catalog?.crusts.find(c => c.id === item.crust_id)}; }
function unitCents(item) { const {product, size, crust} = itemDetails(item); return product ? cents(product.price_base * (product.is_pizza ? size?.price_multiplier ?? 1 : 1) + (product.is_pizza ? crust?.price ?? 0 : 0)) : 0; }
function totals() { const subtotal = state.cart.reduce((sum, item) => sum + unitCents(item) * item.quantity, 0); const fee = state.cart.length && state.delivery === 'ENTREGA' ? cents(state.catalog?.delivery_fee ?? 7) : 0; return {subtotal, fee, total: subtotal + fee}; }
function description(item) { const {size, crust} = itemDetails(item); return [size?.name, crust?.price ? `Borda de ${crust.name}` : null].filter(Boolean).join(' · '); }
function minimumPrice(product) { return product.is_pizza ? product.price_base * Math.min(...state.catalog.sizes.map(s => s.price_multiplier)) : product.price_base; }

async function loadCatalog() {
  $('#products').setAttribute('aria-busy', 'true');
  try {
    state.catalog = await api('/api/catalog');
    const saved = read(KEYS.cart, []);
    state.cart = Array.isArray(saved) ? saved.slice(0, 30).filter(item => {
      if (!item || !Number.isInteger(item.quantity) || item.quantity < 1 || item.quantity > 20) return false;
      const {product, size, crust} = itemDetails(item);
      return product && product.available && (!product.is_pizza || (size && crust));
    }).map(item => ({product_id: item.product_id, size_id: getProduct(item.product_id).is_pizza ? item.size_id : null, crust_id: getProduct(item.product_id).is_pizza ? item.crust_id : null, quantity: item.quantity, notes: typeof item.notes === 'string' ? item.notes.slice(0, 250) : ''})) : [];
    if (Array.isArray(saved) && saved.length !== state.cart.length) toast('Atualizamos seu carrinho: alguns itens não estão mais disponíveis.');
    renderCategories(); renderProducts(); renderCart();
  } catch (error) {
    $('#results-count').textContent = 'Cardápio indisponível no momento';
    $('#products').innerHTML = `<div class="empty-state">${icon('refresh')}<h3>O cardápio não carregou</h3><p>${escapeHTML(error.message)}</p><button class="button secondary" id="retry-catalog">Tentar novamente</button></div>`;
    $('#retry-catalog').addEventListener('click', loadCatalog);
  } finally { $('#products').setAttribute('aria-busy', 'false'); }
}
function renderCategories() {
  const categories = [{id: 0, name: 'Todos'}, ...state.catalog.categories];
  $('#categories').innerHTML = categories.map(cat => `<button type="button" class="category-button" data-category="${cat.id}" aria-pressed="${state.category === cat.id}">${icon(categoryIcons[cat.id] || 'grid')}${escapeHTML(categoryNames[cat.id] || cat.name)}</button>`).join('');
}
function renderProducts() {
  if (!state.catalog) return;
  let products = state.catalog.products.filter(p => (!state.category || p.category_id === state.category) && normalize(`${p.name} ${p.description}`).includes(normalize(state.query)));
  const rank = p => featuredNames.includes(p.name) ? featuredNames.indexOf(p.name) : 100 + p.id;
  products.sort((a, b) => state.sort === 'price-asc' ? minimumPrice(a) - minimumPrice(b) : state.sort === 'price-desc' ? minimumPrice(b) - minimumPrice(a) : state.sort === 'name' ? a.name.localeCompare(b.name, 'pt-BR') : rank(a) - rank(b));
  $('#results-count').textContent = `${products.length} ${products.length === 1 ? 'opção para escolher' : 'opções para escolher'}`;
  $('#products').innerHTML = products.length ? products.map(product => {
    const photo = photoByName[product.name];
    return `<article class="product-card ${photo ? '' : 'compact-card'}">${photo ? `<div class="product-image"><img src="/static/assets/${photo}" alt="${escapeHTML(product.name)}, imagem ilustrativa" width="1536" height="1024" loading="lazy">${featuredNames.indexOf(product.name) < 2 ? `<span class="product-tag">${product.name.startsWith('Calabresa') ? 'UM CLÁSSICO DA CASA' : 'SABOR QUE ABRAÇA'}</span>` : ''}</div>` : `<span class="compact-mark">${icon(categoryIcons[product.category_id])}</span>`}<div class="product-body"><p class="product-category">${escapeHTML(product.category_name)}</p><h3>${escapeHTML(product.name)}</h3><p class="product-description">${escapeHTML(product.description)}</p><div class="product-bottom"><div class="product-price"><small>${product.is_pizza ? 'a partir de' : 'unidade'}</small><strong>${brl(minimumPrice(product))}</strong></div><button type="button" class="add-button" data-product="${product.id}" aria-label="${product.is_pizza ? 'Personalizar' : 'Adicionar'} ${escapeHTML(product.name)}">${icon('plus')}<span>${product.is_pizza ? 'Escolher' : 'Adicionar'}</span></button></div></div></article>`;
  }).join('') : `<div class="empty-state">${icon('search')}<h3>Nenhum sabor por aqui</h3><p>Tente outro ingrediente ou explore todas as categorias.</p><button type="button" class="button secondary" data-reset-search>Ver todo o cardápio</button></div>`;
}
$('#categories').addEventListener('click', event => { const button = event.target.closest('[data-category]'); if (button) { state.category = Number(button.dataset.category); $$('[data-category]').forEach(el => el.setAttribute('aria-pressed', String(Number(el.dataset.category) === state.category))); renderProducts(); } });
$('#search').addEventListener('input', event => { state.query = event.target.value.trim(); renderProducts(); });
$('#sort').addEventListener('change', event => { state.sort = event.target.value; renderProducts(); });
$('#products').addEventListener('click', event => { const button = event.target.closest('[data-product]'); if (button) openProduct(Number(button.dataset.product)); if (event.target.closest('[data-reset-search]')) { state.category = 0; state.query = ''; $('#search').value = ''; renderCategories(); renderProducts(); } });
document.addEventListener('keydown', event => { if (event.key === '/' && !event.ctrlKey && !event.metaKey && !['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName) && !$('dialog[open]')) { event.preventDefault(); $('#search').focus(); } });

function openProduct(id) {
  const product = getProduct(id); if (!product) return;
  const defaultSize = state.catalog.sizes.find(size => size.price_multiplier === 1) || state.catalog.sizes[0];
  state.selected = {product_id: id, size_id: product.is_pizza ? defaultSize?.id : null, crust_id: product.is_pizza ? state.catalog.crusts[0]?.id : null, quantity: 1, notes: ''};
  const photo = photoByName[product.name];
  const close = `<button type="button" class="icon-button" data-close="product-dialog" aria-label="Fechar personalização">${icon('close')}</button>`;
  $('#product-detail').innerHTML = `${photo ? `<div class="dialog-product-image"><img src="/static/assets/${photo}" alt="${escapeHTML(product.name)}, imagem ilustrativa">${close}</div>` : ''}<div class="dialog-header"><div><p class="eyebrow">${escapeHTML(product.category_name)}</p><h2 id="product-title">${escapeHTML(product.name)}</h2></div>${photo ? '' : close}</div><p class="product-description">${escapeHTML(product.description)}</p><form id="product-form">${product.is_pizza ? `<fieldset><legend>Qual é o tamanho da sua fome?</legend><div class="size-options">${state.catalog.sizes.map(size => `<label class="choice"><input type="radio" name="size" value="${size.id}" ${size.id === state.selected.size_id ? 'checked' : ''}><span><strong>${escapeHTML(size.name.split(' (')[0])}</strong><small>${size.slices} fatias</small>${brl(cents(product.price_base * size.price_multiplier) / 100)}</span></label>`).join('')}</div></fieldset><fieldset><legend>E a borda?</legend><div class="crust-options">${state.catalog.crusts.map(crust => `<label><input type="radio" name="crust" value="${crust.id}" ${crust.id === state.selected.crust_id ? 'checked' : ''}>${escapeHTML(crust.price ? crust.name : 'Tradicional, sem recheio')}<strong>${crust.price ? `+ ${brl(crust.price)}` : 'Inclusa'}</strong></label>`).join('')}</div></fieldset>` : ''}<label>Do seu jeito <span class="optional">(opcional)</span><textarea id="item-notes" name="notes" maxlength="250" rows="2" placeholder="Ex.: sem cebola, bem assada…"></textarea></label><div class="product-actions"><div class="quantity"><button type="button" data-modal-qty="-1" aria-label="Diminuir quantidade" disabled>${icon('minus')}</button><output id="product-quantity" aria-live="polite">1</output><button type="button" data-modal-qty="1" aria-label="Aumentar quantidade">${icon('plus')}</button></div><button type="submit" class="button primary" id="add-product"></button></div><p class="dialog-price-help" id="unit-price"></p></form>`;
  $('#product-form').addEventListener('change', event => { if (event.target.name === 'size') state.selected.size_id = Number(event.target.value); if (event.target.name === 'crust') state.selected.crust_id = Number(event.target.value); updateProductPrice(); });
  $('#product-form').addEventListener('click', event => { const button = event.target.closest('[data-modal-qty]'); if (!button) return; state.selected.quantity = Math.min(20, Math.max(1, state.selected.quantity + Number(button.dataset.modalQty))); updateProductPrice(); });
  $('#product-form').addEventListener('submit', event => { event.preventDefault(); addSelected(); });
  updateProductPrice(); showDialog('product-dialog');
}
function updateProductPrice() { const item = state.selected; const unit = unitCents(item); $('#add-product').textContent = `Adicionar · ${brl(unit * item.quantity / 100)}`; $('#unit-price').textContent = `${brl(unit / 100)} por unidade`; $('#product-quantity').value = item.quantity; $('[data-modal-qty="-1"]').disabled = item.quantity <= 1; $('[data-modal-qty="1"]').disabled = item.quantity >= 20; }
function addSelected() {
  const item = {...state.selected, notes: $('#item-notes').value.trim()};
  const existing = state.cart.find(row => row.product_id === item.product_id && row.size_id === item.size_id && row.crust_id === item.crust_id && row.notes === item.notes);
  if (existing && existing.quantity + item.quantity > 20) { toast('Você pode pedir até 20 unidades por combinação.'); return; }
  if (!existing && state.cart.length >= 30) { toast('Seu pedido pode ter até 30 combinações.'); return; }
  if (existing) existing.quantity += item.quantity; else state.cart.push(item);
  renderCart(); closeDialog('product-dialog'); toast(`${getProduct(item.product_id).name} no seu pedido!`);
}

function totalMarkup() { const {subtotal, fee, total} = totals(); return `<div class="cart-totals"><div><span>Subtotal</span><span>${brl(subtotal / 100)}</span></div><div><span>${state.delivery === 'ENTREGA' ? 'Taxa de entrega' : 'Retirada no balcão'}</span><span>${state.delivery === 'BALCAO' ? 'Grátis' : state.cart.length ? brl(fee / 100) : '—'}</span></div><div class="cart-grand-total"><span>Total</span><strong>${brl(total / 100)}</strong></div></div>`; }
function renderCart({persist = true} = {}) {
  const count = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  if (persist && state.catalog) { write(KEYS.cart, state.cart); write(KEYS.delivery, state.delivery); }
  $$('[data-cart-count]').forEach(element => { element.textContent = count; });
  $('#basket-button').setAttribute('aria-label', `Meu pedido, ${count} itens`);
  $('#mobile-total').textContent = brl(totals().total / 100);
  for (const target of ['desktop-cart', 'dialog-cart']) {
    const drawer = target === 'dialog-cart';
    $(`#${target}`).innerHTML = `<div class="cart-title">${icon('bag')} Seu pedido ${drawer ? `<button type="button" class="icon-button" data-close="cart-dialog" aria-label="Fechar carrinho">${icon('close')}</button>` : `<span class="cart-small-count">${count} ${count === 1 ? 'item' : 'itens'}</span>`}</div><p class="cart-subtitle">Uma boa escolha começa por aqui.</p><div class="delivery-toggle" role="group" aria-label="Como receber"><button type="button" data-delivery="ENTREGA" aria-pressed="${state.delivery === 'ENTREGA'}">${icon('scooter')} Entrega</button><button type="button" data-delivery="BALCAO" aria-pressed="${state.delivery === 'BALCAO'}">${icon('store')} Retirada</button></div>${state.cart.length ? `<div class="cart-items">${state.cart.map((item, index) => `<div class="cart-item"><div class="cart-item-top"><strong>${escapeHTML(getProduct(item.product_id).name)}</strong><button type="button" data-remove="${index}" aria-label="Remover ${escapeHTML(getProduct(item.product_id).name)}">${icon('trash')}</button></div><p>${escapeHTML(description(item))}</p>${item.notes ? `<p>Obs.: ${escapeHTML(item.notes)}</p>` : ''}<div class="cart-item-bottom"><div class="quantity"><button type="button" data-qty="-1" data-index="${index}" aria-label="Diminuir quantidade de ${escapeHTML(getProduct(item.product_id).name)}" ${item.quantity <= 1 ? 'disabled' : ''}>${icon('minus')}</button><output>${item.quantity}</output><button type="button" data-qty="1" data-index="${index}" aria-label="Aumentar quantidade de ${escapeHTML(getProduct(item.product_id).name)}" ${item.quantity >= 20 ? 'disabled' : ''}>${icon('plus')}</button></div><strong>${brl(unitCents(item) * item.quantity / 100)}</strong></div></div>`).join('')}</div>` : `<div class="cart-empty"><span class="empty-bag">${icon('bag')}</span><strong>Sua próxima fatia espera por você</strong><p>Escolha seus favoritos no cardápio<br>e monte um pedido com a sua cara.</p></div>`}${totalMarkup()}<button type="button" class="button primary full-width" data-checkout ${!state.cart.length ? 'disabled' : ''}>Continuar pedido ${icon('arrow-right')}</button><div class="cart-payments"><span>${icon('sparkles')} Pix</span><span>${icon('card')} Cartão</span><span>${icon('wallet')} Dinheiro</span></div>`;
  }
}
for (const container of $$('#desktop-cart, #dialog-cart')) container.addEventListener('click', event => {
  const remove = event.target.closest('[data-remove]'), quantity = event.target.closest('[data-qty]'), delivery = event.target.closest('[data-delivery]');
  let focusSelector;
  if (remove) { state.cart.splice(Number(remove.dataset.remove), 1); renderCart(); toast('Item removido do pedido.'); focusSelector = '[data-checkout]'; }
  if (quantity) { const index = Number(quantity.dataset.index); state.cart[index].quantity = Math.min(20, Math.max(1, state.cart[index].quantity + Number(quantity.dataset.qty))); focusSelector = `[data-index="${index}"][data-qty="${quantity.dataset.qty}"]`; renderCart(); }
  if (delivery) { state.delivery = delivery.dataset.delivery; focusSelector = `[data-delivery="${state.delivery}"]`; renderCart(); }
  if (focusSelector) $(focusSelector, container)?.focus({preventScroll: true});
  if (event.target.closest('[data-checkout]')) openCheckout();
});
$('#basket-button').addEventListener('click', () => showDialog('cart-dialog'));
$('#mobile-cart').addEventListener('click', () => showDialog('cart-dialog'));

function openCheckout() {
  if (!state.cart.length) return;
  closeDialog('cart-dialog');
  $(`input[name="delivery_type"][value="${state.delivery}"]`).checked = true;
  $('#checkout-error').hidden = true; updateCheckout(); showDialog('checkout-dialog');
}
function updateCheckout() {
  const delivery = state.delivery === 'ENTREGA';
  $('#address-field').hidden = !delivery; $('#pickup-note').hidden = delivery;
  $('[name="address"]').required = delivery;
  $('[name="address"]').disabled = !delivery;
  $('#checkout-summary').innerHTML = state.cart.map(item => `<div class="checkout-item"><span>${item.quantity}× ${escapeHTML(getProduct(item.product_id).name)}<small>${escapeHTML(description(item))}</small></span><strong>${brl(unitCents(item) * item.quantity / 100)}</strong></div>`).join('') + totalMarkup();
}
$$('[name="delivery_type"]').forEach(input => input.addEventListener('change', () => { state.delivery = input.value; renderCart(); updateCheckout(); }));
$('#checkout-form').addEventListener('input', event => event.target.setCustomValidity?.(''));
$('#checkout-form').addEventListener('submit', async event => {
  event.preventDefault(); if (state.submitting || !state.cart.length) return;
  const form = event.target; const data = new FormData(form);
  const payload = {customer_name: data.get('customer_name').trim(), customer_phone: data.get('customer_phone').trim(), delivery_type: state.delivery, payment_method: data.get('payment_method'), address: state.delivery === 'ENTREGA' ? data.get('address').trim() : null, notes: data.get('notes').trim(), items: state.cart.map(item => ({...item}))};
  state.submitting = true; $('#checkout-error').hidden = true; const submit = $('#submit-order'); submit.disabled = true; submit.textContent = 'Enviando seu pedido…';
  try {
    const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(JSON.stringify(payload))))].map(byte => byte.toString(16).padStart(2, '0')).join('');
    const previous = state.pending;
    const requestId = previous?.digest === digest && typeof previous?.id === 'string' ? previous.id : crypto.randomUUID();
    state.pending = {digest, id: requestId};
    write(KEYS.pending, state.pending);
    const result = await api('/api/orders', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({...payload, request_id: requestId})});
    state.orders = [{id: result.order.id, token: result.tracking_token}, ...state.orders.filter(order => order.id !== result.order.id)].slice(0, 20);
    state.receipts.set(result.order.id, result.order);
    const stored = write(KEYS.orders, state.orders); state.pending = null; write(KEYS.pending, null);
    state.cart = []; renderCart(); form.reset(); state.submitting = false; closeDialog('checkout-dialog');
    renderOrders(); showDialog('orders-dialog');
    toast(stored ? `Pedido #${result.order.id} recebido!` : `Pedido #${result.order.id} recebido. Mantenha esta página aberta para acompanhar.`);
  } catch (error) {
    $('#checkout-error').textContent = error.message; $('#checkout-error').hidden = false;
    if (error.field) { const field = form.elements.namedItem(error.field); if (field instanceof HTMLElement) { field.focus(); } }
  } finally { state.submitting = false; submit.disabled = false; submit.innerHTML = `Confirmar pedido ${icon('arrow-right')}`; }
});

const statusLabels = {RECEBIDO: 'Recebido', EM_PREPARO: 'Em preparo', NO_FORNO: 'No forno', SAIU_ENTREGA: 'Saiu para entrega', ENTREGUE: 'Concluído', CANCELADO: 'Cancelado'};
const statusFlow = ['RECEBIDO', 'EM_PREPARO', 'NO_FORNO', 'SAIU_ENTREGA', 'ENTREGUE'];
const paymentLabels = {PIX: 'Pix', CARTAO_CREDITO: 'Crédito', CARTAO_DEBITO: 'Débito', DINHEIRO: 'Dinheiro'};
function renderOrders(errors = new Map()) {
  $('#orders-list').innerHTML = state.orders.length ? state.orders.map(record => {
    const order = state.receipts.get(record.id);
    const error = errors.get(record.id);
    if (!order) return `<article class="order-receipt"><strong>Pedido #${record.id}</strong><p class="receipt-note">${escapeHTML(error || 'Consultando o andamento…')}</p></article>`;
    const date = new Date(order.created_at);
    const label = order.delivery_type === 'BALCAO' && order.status === 'SAIU_ENTREGA' ? 'Pronto para retirada' : statusLabels[order.status] || order.status;
    return `<article class="order-receipt"><div class="receipt-top"><strong>Pedido #${order.id}</strong><span class="order-status ${order.status === 'CANCELADO' ? 'cancelled' : ''}">${icon(order.status === 'ENTREGUE' ? 'check' : 'oven')}${escapeHTML(label)}</span></div><p class="order-date">${Number.isNaN(date.getTime()) ? '' : date.toLocaleString('pt-BR', {dateStyle: 'short', timeStyle: 'short'})} · ${order.delivery_type === 'ENTREGA' ? 'Entrega' : 'Retirada no balcão'}</p>${order.status !== 'CANCELADO' ? `<div class="order-steps" aria-label="Etapa atual: ${escapeHTML(label)}">${statusFlow.map((_, index) => `<span class="${index <= statusFlow.indexOf(order.status) ? 'done' : ''}"></span>`).join('')}</div>` : ''}<div class="receipt-items">${order.items.map(item => `<div class="receipt-item">${item.quantity}× ${escapeHTML(item.product_name)}<small>${escapeHTML([item.size_name, item.crust_name].filter(Boolean).join(' · '))}</small>${item.notes ? `<small>Obs.: ${escapeHTML(item.notes)}</small>` : ''}</div>`).join('')}</div><div class="cart-totals"><div><span>Subtotal</span><span>${brl(order.subtotal)}</span></div><div><span>Entrega</span><span>${order.delivery_fee ? brl(order.delivery_fee) : 'Grátis'}</span></div><div class="cart-grand-total"><span>Total · ${escapeHTML(paymentLabels[order.payment_method] || order.payment_method)}</span><strong>${brl(order.total)}</strong></div></div>${order.address ? `<p class="receipt-note">${escapeHTML(order.address)}</p>` : ''}<p class="receipt-note">${order.status === 'CANCELADO' ? 'Este pedido foi cancelado pela loja.' : 'Pagamento no recebimento. O andamento é atualizado pela equipe da pizzaria.'}</p>${error ? `<p class="form-error">${escapeHTML(error)} Exibindo a última informação disponível.</p>` : ''}</article>`;
  }).join('') : `<div class="empty-state">${icon('bag')}<h3>Sua primeira fatia está por vir</h3><p>Quando você fizer um pedido neste navegador, ele aparecerá aqui.</p><button type="button" class="button primary" data-close="orders-dialog">Explorar o cardápio</button></div>`;
  $('#refresh-orders').hidden = !state.orders.length;
}
async function refreshOrders() {
  if (state.tracking || !state.orders.length) return;
  state.tracking = true; $('#refresh-orders').disabled = true; $('#refresh-orders').textContent = 'Atualizando…';
  const errors = new Map();
  await Promise.all(state.orders.map(async record => { try { const result = await api(`/api/orders/${record.id}`, {headers: {Authorization: `Bearer ${record.token}`}}); state.receipts.set(record.id, result.order); } catch (error) { errors.set(record.id, error.message); } }));
  renderOrders(errors); state.tracking = false; $('#refresh-orders').disabled = false; $('#refresh-orders').innerHTML = `${icon('refresh')} Atualizar pedidos`;
}
$('#orders-button').addEventListener('click', () => { renderOrders(); showDialog('orders-dialog'); refreshOrders(); });
$('#refresh-orders').addEventListener('click', refreshOrders);
setInterval(() => { if ($('#orders-dialog').open && document.visibilityState === 'visible') refreshOrders(); }, 20000);
renderCart({persist: false});
loadCatalog();
