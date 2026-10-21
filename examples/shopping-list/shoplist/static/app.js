// Mobile shopping list: hash-routed views on top of the JSON API.
// User data only ever reaches the page through textContent, never innerHTML.

const CATEGORY_ICONS = {
  "Obst & Gemüse": "🥕",
  Backwaren: "🥖",
  Kühlregal: "🧀",
  "Fleisch & Fisch": "🥩",
  Vorrat: "🥫",
  Tiefkühl: "🧊",
  Getränke: "🥤",
  Drogerie: "🧴",
};
const DEFAULT_CATEGORY = "Sonstiges";
const number = new Intl.NumberFormat("de-DE", { maximumFractionDigits: 2 });
const view = document.querySelector("#view");
const heading = document.querySelector("#title");
let categories = [DEFAULT_CATEGORY];

function h(tag, props = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key.startsWith("on")) element.addEventListener(key.slice(2), value);
    else if (key === "class") element.className = value;
    else if (value === true) element.setAttribute(key, "");
    else if (value !== false && value != null) element.setAttribute(key, value);
  }
  element.append(...children.flat().filter((child) => child != null && child !== false));
  return element;
}

function icon(category) {
  return CATEGORY_ICONS[category] ?? "🛒";
}

function quantity({ amount, unit }) {
  return [amount == null ? "" : number.format(amount), unit].filter(Boolean).join(" ");
}

function parseAmount(text) {
  const trimmed = text.trim().replace(",", ".");
  if (!trimmed) return null;
  const value = Number(trimmed);
  if (!Number.isFinite(value)) throw new Error("Menge muss eine Zahl sein.");
  return value;
}

async function api(path, { method = "GET", body } = {}) {
  const response = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error ?? "Unbekannter Fehler.");
  return data;
}

function render(title, ...nodes) {
  heading.textContent = title;
  document.title = title === "Einkaufsliste" ? title : `${title} · Einkaufsliste`;
  view.replaceChildren(...nodes.flat().filter(Boolean));
}

let toastTimer;
function toast(message, kind = "info") {
  const element = document.querySelector("#toast");
  element.textContent = message;
  element.dataset.kind = kind;
  element.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    element.hidden = true;
  }, 3000);
}

// Runs a change, then redraws. Errors from the API end up in a toast.
async function act(change, redraw = route) {
  try {
    await change();
    await redraw();
  } catch (error) {
    toast(error.message, "error");
  }
}

function categorySelect(selected = DEFAULT_CATEGORY) {
  return h(
    "select",
    { "aria-label": "Kategorie" },
    categories.map((category) =>
      h("option", { value: category, selected: category === selected }, `${icon(category)} ${category}`),
    ),
  );
}

function groupByCategory(entries) {
  const groups = new Map();
  for (const entry of entries) {
    if (!groups.has(entry.category)) groups.set(entry.category, []);
    groups.get(entry.category).push(entry);
  }
  return [...groups];
}

// ---- Shopping list ----

async function showList() {
  const { items } = await api("/api/items");
  const open = items.filter((item) => !item.checked).length;
  render(
    "Einkaufsliste",
    addItemForm(),
    items.length
      ? h("p", { class: "summary" }, open ? `${open} von ${items.length} noch offen` : "Alles im Korb 🎉")
      : h("p", { class: "empty" }, "Die Liste ist leer. Trag oben ein, was du brauchst."),
    groupByCategory(items).map(([category, entries]) =>
      h(
        "section",
        { class: "group" },
        h("h2", {}, `${icon(category)} ${category}`),
        h("ul", { class: "items" }, entries.map(itemRow)),
      ),
    ),
    items.length > open &&
      h(
        "button",
        { class: "secondary wide", onclick: () => act(() => api("/api/items/checked", { method: "DELETE" })) },
        "Erledigte entfernen",
      ),
  );
}

function addItemForm() {
  const name = h("input", { placeholder: "Was brauchst du?", maxlength: 80, autocomplete: "off", "aria-label": "Artikel", required: true });
  const amount = h("input", { placeholder: "Menge", inputmode: "decimal", "aria-label": "Menge" });
  const unit = h("input", { placeholder: "Einheit", maxlength: 12, "aria-label": "Einheit" });
  const category = categorySelect();
  const submit = (event) => {
    event.preventDefault();
    act(() =>
      api("/api/items", {
        method: "POST",
        body: { name: name.value, amount: parseAmount(amount.value), unit: unit.value, category: category.value },
      }),
    );
  };
  return h(
    "form",
    { class: "card add-item", onsubmit: submit },
    name,
    h("div", { class: "row" }, amount, unit, category),
    h("button", { type: "submit" }, "Hinzufügen"),
  );
}

function itemRow(item) {
  const toggle = (event) =>
    act(() => api(`/api/items/${item.id}`, { method: "PATCH", body: { checked: event.target.checked } }));
  return h(
    "li",
    { class: item.checked ? "item checked" : "item" },
    h(
      "label",
      {},
      h("input", { type: "checkbox", checked: item.checked, onchange: toggle }),
      h("span", { class: "name" }, item.name),
      h("span", { class: "qty" }, quantity(item)),
    ),
  );
}

// ---- Dishes ----

async function showDishes() {
  const { dishes } = await api("/api/dishes");
  render(
    "Gerichte",
    h("a", { class: "button", href: "#/gerichte/neu" }, "+ Neues Gericht"),
    dishes.length
      ? h(
          "ul",
          { class: "dishes" },
          dishes.map((dish) =>
            h(
              "li",
              {},
              h(
                "a",
                { class: "card dish", href: `#/gerichte/${dish.id}` },
                h("strong", {}, dish.name),
                h("span", {}, `${dish.servings} Portionen · ${dish.ingredients.length} Zutaten`),
              ),
            ),
          ),
        )
      : h("p", { class: "empty" }, "Noch keine Gerichte. Leg dein erstes an."),
  );
}

function ingredientList(ingredients) {
  return h(
    "ul",
    { class: "ingredients" },
    ingredients.map((ingredient) =>
      h(
        "li",
        {},
        h("span", { "aria-hidden": "true" }, icon(ingredient.category)),
        h("span", { class: "name" }, ingredient.name),
        h("span", { class: "qty" }, quantity(ingredient)),
      ),
    ),
  );
}

async function showDish(id) {
  const { dish } = await api(`/api/dishes/${id}`);
  const remove = () => {
    if (!confirm(`„${dish.name}“ löschen?`)) return;
    act(
      () => api(`/api/dishes/${id}`, { method: "DELETE" }),
      async () => {
        location.hash = "#/gerichte";
      },
    );
  };
  render(
    dish.name,
    h("p", { class: "meta" }, `Zutaten für ${dish.servings} Portionen`),
    ingredientList(dish.ingredients),
    h(
      "div",
      { class: "actions" },
      h("a", { class: "button secondary", href: "#/gerichte" }, "Zurück"),
      h("button", { class: "danger", onclick: remove }, "Löschen"),
    ),
  );
}

// One editable ingredient. read() returns null for a row left empty.
function ingredientRow() {
  const name = h("input", { placeholder: "Zutat", maxlength: 80, autocomplete: "off", "aria-label": "Zutat" });
  const amount = h("input", { placeholder: "Menge", inputmode: "decimal", "aria-label": "Menge" });
  const unit = h("input", { placeholder: "Einheit", maxlength: 12, "aria-label": "Einheit" });
  const category = categorySelect();
  return {
    element: h("fieldset", { class: "ingredient" }, name, h("div", { class: "row" }, amount, unit, category)),
    read: () =>
      name.value.trim()
        ? { name: name.value, amount: parseAmount(amount.value), unit: unit.value, category: category.value }
        : null,
  };
}

function showDishForm() {
  const name = h("input", { placeholder: "z. B. Linsensuppe", maxlength: 80, required: true });
  const servings = h("input", { type: "number", min: 1, max: 50, value: 2, inputmode: "numeric", required: true });
  const rows = h("div", { class: "ingredient-rows" });
  const ingredientRows = [];
  const addRow = () => {
    const row = ingredientRow();
    ingredientRows.push(row);
    rows.append(row.element);
  };
  addRow();
  addRow();
  addRow();
  const save = (event) => {
    event.preventDefault();
    act(
      async () => {
        const ingredients = ingredientRows.map((row) => row.read()).filter(Boolean);
        const { dish } = await api("/api/dishes", {
          method: "POST",
          body: { name: name.value, servings: Number(servings.value), ingredients },
        });
        location.hash = `#/gerichte/${dish.id}`;
      },
      async () => {},
    );
  };
  render(
    "Neues Gericht",
    h(
      "form",
      { class: "card", onsubmit: save },
      h("label", { class: "field" }, "Name", name),
      h("label", { class: "field" }, "Portionen", servings),
      h("h2", {}, "Zutaten"),
      rows,
      h("button", { type: "button", class: "secondary", onclick: addRow }, "+ Zutat"),
      h("button", { type: "submit" }, "Gericht speichern"),
    ),
  );
}

// ---- Routing ----

const routes = [
  [/^#\/liste$/, showList],
  [/^#\/gerichte$/, showDishes],
  [/^#\/gerichte\/neu$/, showDishForm],
  [/^#\/gerichte\/(\d+)$/, (id) => showDish(Number(id))],
];

async function route() {
  const hash = location.hash || "#/liste";
  const found = routes.map(([pattern, show]) => [hash.match(pattern), show]).find(([match]) => match);
  if (!found) {
    location.hash = "#/liste";
    return;
  }
  for (const tab of document.querySelectorAll(".tabbar a")) {
    const href = tab.getAttribute("href");
    if (hash === href || hash.startsWith(`${href}/`)) tab.setAttribute("aria-current", "page");
    else tab.removeAttribute("aria-current");
  }
  const [match, show] = found;
  try {
    await show(...match.slice(1));
  } catch (error) {
    render("Fehler", h("p", { class: "empty" }, error.message));
  }
}

async function start() {
  try {
    ({ categories } = await api("/api/categories"));
  } catch (error) {
    toast(error.message, "error");
  }
  window.addEventListener("hashchange", route);
  await route();
}

start();
