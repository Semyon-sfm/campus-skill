/* Кабинет ментора: список своих воркшопов, публикация и удаление.
   Данные — GET /api/workshops/mine/, действия — POST .../publish/ и DELETE. */
(function () {
  "use strict";

  var api = window.CampusApi;
  var ui = window.CampusUI;

  var list = document.querySelector("[data-studio-list]");
  var publishedCount = document.querySelector("[data-published-count]");
  var draftCount = document.querySelector("[data-draft-count]");

  function link(href, text, className) {
    var node = document.createElement("a");
    node.className = (className || "sk-text-button") + " cursor-interaction";
    node.href = href;
    node.textContent = text;
    return node;
  }

  function button(text, className, handler) {
    var node = document.createElement("button");
    node.type = "button";
    node.className = (className || "sk-text-button") + " cursor-interaction";
    node.textContent = text;
    node.addEventListener("click", handler);
    return node;
  }

  function publish(id, node) {
    node.disabled = true;
    api
      .post("/api/workshops/" + id + "/publish/")
      .then(function () {
        ui.flash("Воркшоп опубликован — запись открыта.");
        load();
      })
      .catch(function (error) {
        node.disabled = false;
        ui.flash(api.message(error.payload), true);
      });
  }

  function finish(id, title, node) {
    if (!window.confirm("Завершить воркшоп «" + title + "»? Запись закроется, а участники смогут оставить отзывы.")) return;
    node.disabled = true;
    api
      .post("/api/workshops/" + id + "/finish/")
      .then(function () {
        ui.flash("Воркшоп завершён — участники могут оставить отзывы.");
        load();
      })
      .catch(function (error) {
        node.disabled = false;
        ui.flash(api.message(error.payload), true);
      });
  }

  function remove(id, title, node) {
    if (!window.confirm("Удалить воркшоп «" + title + "»?")) return;
    node.disabled = true;
    api
      .del("/api/workshops/" + id + "/")
      .then(function () {
        ui.flash("Воркшоп удалён.");
        load();
      })
      .catch(function (error) {
        node.disabled = false;
        ui.flash(api.message(error.payload), true);
      });
  }

  function row(item) {
    var fragment = ui.clone("sk-studio-row-template");
    var article = fragment.querySelector("article");

    var statusState = item.status === "published" ? "confirmed" : item.status;

    ui.fill(article, "[data-status]", statusLabel(item.status));
    ui.fill(article, "[data-title]", item.title);
    ui.fill(article, "[data-meta]", item.date_label + " · " + item.format_label);
    ui.fill(
      article,
      "[data-seats]",
      item.status === "draft"
        ? "Запись не открыта"
        : item.registered + " из " + item.capacity + " мест"
    );

    article.querySelector("[data-status]").classList.add("sk-state-" + statusState);

    var actions = article.querySelector("[data-actions]");
    actions.append(link(item.url, "Посмотреть"));

    if (item.status === "draft") {
      actions.append(link("/studio/" + item.id + "/edit/", "Редактировать"));
      actions.append(
        button("Опубликовать", "sk-primary", function (event) {
          publish(item.id, event.currentTarget);
        })
      );
      actions.append(
        button("Удалить", "sk-text-button", function (event) {
          remove(item.id, item.title, event.currentTarget);
        })
      );
    } else if (item.status === "published") {
      actions.append(link("/studio/" + item.id + "/edit/", "Редактировать"));
      actions.append(
        button("Завершить воркшоп", "sk-text-button", function (event) {
          finish(item.id, item.title, event.currentTarget);
        })
      );
      actions.append(
        link("/studio/" + item.id + "/participants/", "Участники", "sk-secondary")
      );
    } else {
      actions.append(
        link("/studio/" + item.id + "/participants/", "Участники", "sk-secondary")
      );
    }

    return fragment;
  }

  function statusLabel(status) {
    return {
      published: "Запись открыта",
      draft: "Черновик",
      finished: "Воркшоп завершён",
    }[status] || status;
  }

  function load() {
    ui.setLoading(list);

    api
      .get("/api/workshops/mine/")
      .then(function (items) {
        var published = 0;
        var drafts = 0;
        items.forEach(function (item) {
          if (item.status === "published") published += 1;
          if (item.status === "draft") drafts += 1;
        });
        publishedCount.textContent = String(published);
        draftCount.textContent = String(drafts);

        list.replaceChildren();
        if (!items.length) {
          var box = document.createElement("div");
          box.className = "sk-empty";
          var title = document.createElement("h3");
          title.textContent = "Воркшопов пока нет";
          var copy = document.createElement("p");
          copy.textContent = "Создай первую встречу и поделись навыком.";
          var cta = link("/studio/new/", "Создать воркшоп", "sk-primary");
          box.append(title, copy, cta);
          list.append(box);
          return;
        }
        items.forEach(function (item) {
          list.append(row(item));
        });
        ui.icons(list, 17);
      })
      .catch(function (error) {
        ui.setError(list, error);
      });
  }

  load();
})();
