/* Каталог воркшопов.
   Страницу отдаёт Django, а сетка карточек, поиск, фильтры и «Показать ещё»
   работают только через GET /api/workshops/ — без перезагрузки страницы. */
(function () {
  "use strict";

  var api = window.CampusApi;
  var ui = window.CampusUI;
  var cards = window.CampusCards;

  var PAGE_SIZE = 3;

  var list = document.querySelector("[data-workshop-list]");
  var empty = document.querySelector("[data-empty]");
  var more = document.querySelector("[data-more]");
  var countNode = document.querySelector("[data-result-count]");
  var search = document.querySelector("[data-search]");
  var categoryBar = document.querySelector("[data-categories]");

  var state = {
    skill: "",
    q: "",
    format: "",
    date: "",
    price: "",
    level: "",
    limit: PAGE_SIZE,
  };

  /** Синхронизирует фильтры с адресной строкой, чтобы ссылку можно было дать другому. */
  function readUrl() {
    var params = new URLSearchParams(window.location.search);
    ["skill", "q", "format", "date", "price", "level"].forEach(function (key) {
      if (params.has(key)) state[key] = params.get(key);
    });
  }

  function writeUrl() {
    var params = new URLSearchParams();
    ["skill", "q", "format", "date", "price", "level"].forEach(function (key) {
      if (state[key]) params.set(key, state[key]);
    });
    var query = params.toString();
    window.history.replaceState(
      null,
      "",
      window.location.pathname + (query ? "?" + query : "")
    );
  }

  function applyStateToControls() {
    if (search) search.value = state.q;
    document.querySelectorAll("[data-filter]").forEach(function (field) {
      field.value = state[field.dataset.filter] || "";
    });
    categoryBar.querySelectorAll("[data-skill]").forEach(function (button) {
      button.setAttribute("aria-pressed", String(button.dataset.skill === state.skill));
    });
  }

  function load(mode) {
    var params = {
      skill: state.skill,
      q: state.q,
      format: state.format,
      date: state.date,
      price: state.price,
      level: state.level,
      limit: state.limit,
      offset: 0,
    };

    if (mode !== "append") ui.setLoading(list);

    return api
      .get("/api/workshops/", params)
      .then(function (data) {
        var total = data.count;
        var items = data.results;

        cards.renderInto(list, items, "replace");

        empty.hidden = total > 0;
        countNode.textContent = ui.plural(total, "воркшоп", "воркшопа", "воркшопов");

        var remaining = total - items.length;
        more.hidden = remaining <= 0;
        more.textContent =
          "Показать ещё " + Math.min(PAGE_SIZE, remaining) + " из " + remaining;

        ui.announce(countNode.textContent);
      })
      .catch(function (error) {
        ui.setError(list, error);
        empty.hidden = true;
        more.hidden = true;
      });
  }

  /** Любая смена фильтра сбрасывает догрузку обратно на первую страницу. */
  function refresh() {
    state.limit = PAGE_SIZE;
    writeUrl();
    load();
  }

  categoryBar.addEventListener("click", function (event) {
    var button = event.target.closest("[data-skill]");
    if (!button) return;
    state.skill = button.dataset.skill;
    applyStateToControls();
    refresh();
  });

  document.querySelectorAll("[data-filter]").forEach(function (field) {
    field.addEventListener("change", function () {
      state[field.dataset.filter] = field.value;
      refresh();
    });
  });

  if (search) {
    var timer = null;
    search.addEventListener("input", function () {
      window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        state.q = search.value;
        refresh();
      }, 250);
    });
  }

  document.querySelector("[data-reset]").addEventListener("click", function () {
    state.skill = "";
    state.q = "";
    state.format = "";
    state.date = "";
    state.price = "";
    state.level = "";
    applyStateToControls();
    refresh();
  });

  more.addEventListener("click", function () {
    state.limit += PAGE_SIZE;
    load("append");
  });

  var becomeMentor = document.querySelector("[data-become-mentor]");
  if (becomeMentor) {
    becomeMentor.addEventListener("click", function () {
      becomeMentor.disabled = true;
      api
        .post("/api/profile/become-mentor/")
        .then(function () {
          window.location.href = "/studio/";
        })
        .catch(function (error) {
          becomeMentor.disabled = false;
          ui.flash(api.message(error.payload), true);
        });
    });
  }

  readUrl();
  applyStateToControls();
  load();
})();
