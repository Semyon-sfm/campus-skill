/* Редактор воркшопа. Форма размечена Django, но создание и правка идут
   через POST / PATCH /api/workshops/ — страница не перезагружается. */
(function () {
  "use strict";

  var api = window.CampusApi;
  var ui = window.CampusUI;

  function start(options) {
    var form = document.querySelector("[data-editor-form]");
    var error = document.querySelector("[data-form-error]");
    var locationLabel = document.querySelector("[data-location-label]");
    var formatField = form.elements.namedItem("format");
    var placeField = form.elements.namedItem("place");

    /* Подпись поля места зависит от формата — как в макете. */
    function syncLocationLabel() {
      var online = formatField.value === "online";
      locationLabel.textContent = online
        ? "Площадка или ссылка на встречу"
        : "Место проведения";
      placeField.placeholder = online
        ? "Ссылка или название платформы"
        : "Корпус и аудитория";
    }

    formatField.addEventListener("change", syncLocationLabel);
    syncLocationLabel();

    /* Запоминаем, какая кнопка нажата: черновик или публикация. */
    var intent = "draft";
    form.querySelectorAll("button[type=submit]").forEach(function (node) {
      node.addEventListener("click", function () {
        intent = node.value;
      });
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();

      if (!form.reportValidity()) return;

      var data = new FormData(form);
      var payload = {
        title: String(data.get("title")).trim(),
        skill: data.get("skill"),
        level: data.get("level"),
        description: String(data.get("description")).trim(),
        program: String(data.get("program")),
        requirements: String(data.get("requirements")).trim(),
        date: data.get("date"),
        time: data.get("time"),
        duration: Number(data.get("duration")),
        capacity: Number(data.get("capacity")),
        format: data.get("format"),
        amount: Number(data.get("amount")),
        place: String(data.get("place")).trim(),
        requires_approval: data.get("approval") === "on",
        intent: intent,
      };

      var buttons = form.querySelectorAll("button[type=submit]");
      buttons.forEach(function (node) { node.disabled = true; });
      error.hidden = true;

      var request = options.workshopId
        ? api.patch("/api/workshops/" + options.workshopId + "/", payload)
        : api.post("/api/workshops/", payload);

      request
        .then(function () {
          window.location.href = options.studioUrl;
        })
        .catch(function (err) {
          buttons.forEach(function (node) { node.disabled = false; });
          error.textContent = api.message(err.payload);
          error.hidden = false;
          error.scrollIntoView({ block: "center", behavior: "smooth" });
          ui.announce(error.textContent);
        });
    });
  }

  window.CampusEditor = { start: start };
})();
