/* Рендер карточек воркшопов из JSON, полученного от /api/workshops/.
   Разметка берётся из <template id="sk-workshop-card-template"> — то есть
   остаётся в Django-шаблоне, а не дублируется строками в JS. */
(function () {
  "use strict";

  var ui = window.CampusUI;

  function card(item) {
    var fragment = ui.clone("sk-workshop-card-template");
    var article = fragment.querySelector("article");

    article.classList.add("sk-skill-" + item.skill.slug);

    ui.fill(article, "[data-skill]", item.tag);
    ui.fill(article, "[data-art-word]", item.art);
    article.querySelector("[data-art-icon]").setAttribute("data-lucide", item.skill.icon);

    ui.fill(article, "[data-format]", item.format_label);
    ui.fill(article, "[data-date]", item.date_label);
    ui.fill(article, "[data-title]", item.title);
    ui.fill(article, "[data-description]", item.description);
    ui.fill(article, "[data-mentor-initials]", item.mentor.initials);
    ui.fill(article, "[data-mentor-name]", item.mentor.full_name);
    // Звезда стоит в блоке ментора, поэтому показываем его рейтинг. Рейтинг
    // самого воркшопа появляется только после отзывов — его место на карточке
    // воркшопа, а не в каталоге.
    var rating = item.rating || item.mentor.rating;
    ui.fill(article, "[data-rating]", rating ? "★ " + rating : "Новый");
    ui.fill(article, "[data-duration]", item.duration_label);
    ui.fill(article, "[data-price]", item.price_label);

    // Если участник уже записан — вместо числа мест показываем его статус.
    ui.fill(
      article,
      "[data-availability]",
      item.my_status_label || item.availability_label
    );

    ui.link(article, "[data-open-art]", item.url);
    ui.link(article, "[data-open-title]", item.url);
    ui.link(article, "[data-open-button]", item.url);
    ui.link(article, "[data-mentor-link]", item.mentor.url);

    article
      .querySelector("[data-open-art]")
      .setAttribute("aria-label", "Подробнее: " + item.title);

    return fragment;
  }

  /** Заполняет контейнер карточками. mode="append" дописывает к имеющимся. */
  function renderInto(container, items, mode) {
    if (mode !== "append") container.replaceChildren();
    items.forEach(function (item) {
      container.append(card(item));
    });
    ui.icons(container, 17);
  }

  window.CampusCards = { card: card, renderInto: renderInto };
})();
