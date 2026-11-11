/* «Моё обучение»: табы и прогресс по навыкам.
   Каждый таб — отдельный запрос к GET /api/enrollments/?tab=…, страница не
   перезагружается. Прогресс берётся из /api/profile/skill-progress/. */
(function () {
  "use strict";

  var api = window.CampusApi;
  var ui = window.CampusUI;

  var list = document.querySelector("[data-enrollment-list]");
  var tabsBar = document.querySelector("[data-learning-tabs]");
  var progressBox = document.querySelector("[data-skill-progress]");

  var currentTab = "upcoming";

  function emptyState(tab) {
    var box = document.createElement("div");
    box.className = "sk-empty";

    var title = document.createElement("h3");
    title.textContent =
      tab === "waitlist"
        ? "Ты пока не в листе ожидания"
        : tab === "history"
          ? "Пройденных воркшопов пока нет"
          : "Здесь появятся твои воркшопы";

    var copy = document.createElement("p");
    copy.textContent = "Выбери интересную тему в каталоге.";

    var link = document.createElement("a");
    link.className = "sk-primary cursor-interaction";
    link.href = "/";
    link.textContent = "Найти воркшоп";

    box.append(title, copy, link);
    return box;
  }

  function actionLink(href, text, className) {
    var node = document.createElement("a");
    node.className = (className || "sk-text-button") + " cursor-interaction";
    node.href = href;
    node.textContent = text;
    return node;
  }

  function row(item) {
    var fragment = ui.clone("sk-enrollment-row-template");
    var article = fragment.querySelector("article");

    ui.fill(article, "[data-day]", item.day);
    ui.fill(article, "[data-month]", item.month);
    ui.fill(article, "[data-status]", item.status_label);
    ui.fill(article, "[data-title]", item.title);
    ui.fill(article, "[data-meta]", item.meta);
    ui.fill(article, "[data-extra]", item.extra);

    article.querySelector("[data-status]").classList.add("sk-state-" + item.state);

    var actions = article.querySelector("[data-actions]");
    actions.append(actionLink(item.workshop_url, "О воркшопе"));

    if (item.can_review) {
      actions.append(actionLink(item.review_url, "Оставить отзыв", "sk-secondary"));
    } else if (item.has_review) {
      var done = document.createElement("span");
      done.className = "sk-subtle";
      done.textContent = "Отзыв оставлен";
      actions.append(done);
    }

    if (item.state !== "finished") {
      actions.append(
        actionLink(
          item.cancel_url,
          item.status === "waitlist" ? "Покинуть лист" : "Отменить"
        )
      );
    }

    return fragment;
  }

  function loadTab(tab) {
    currentTab = tab;
    tabsBar.querySelectorAll("[data-tab]").forEach(function (button) {
      button.setAttribute("aria-selected", String(button.dataset.tab === tab));
    });

    var url = new URL(window.location.href);
    url.searchParams.set("tab", tab);
    window.history.replaceState(null, "", url.pathname + url.search);

    ui.setLoading(list);

    api
      .get("/api/enrollments/", { tab: tab })
      .then(function (items) {
        list.replaceChildren();
        if (!items.length) {
          list.append(emptyState(tab));
        } else {
          items.forEach(function (item) {
            list.append(row(item));
          });
        }
        ui.icons(list, 17);
        ui.announce(ui.plural(items.length, "запись", "записи", "записей"));
      })
      .catch(function (error) {
        ui.setError(list, error);
      });
  }

  function loadProgress() {
    api
      .get("/api/profile/skill-progress/")
      .then(function (items) {
        progressBox.replaceChildren();
        if (!items.length) {
          var note = document.createElement("p");
          note.textContent = "Пока нет посещённых воркшопов.";
          progressBox.append(note);
          return;
        }
        items.forEach(function (item) {
          var line = document.createElement("div");
          line.className = "sk-skill-progress";

          var label = document.createElement("span");
          var icon = document.createElement("i");
          icon.setAttribute("data-lucide", item.icon);
          icon.setAttribute("aria-hidden", "true");
          var text = document.createElement("span");
          text.textContent = item.label;
          label.append(icon, text);

          var value = document.createElement("strong");
          value.textContent = item.attended_label;

          line.append(label, value);
          progressBox.append(line);
        });
        ui.icons(progressBox, 14);
      })
      .catch(function () { /* панель прогресса не критична */ });
  }

  tabsBar.addEventListener("click", function (event) {
    var button = event.target.closest("[data-tab]");
    if (!button || button.dataset.tab === currentTab) return;
    loadTab(button.dataset.tab);
  });

  window.CampusLearning = {
    start: function (tab) {
      loadTab(tab || "upcoming");
      loadProgress();
    },
  };
})();
