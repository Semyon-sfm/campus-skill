/* Список участников воркшопа у ментора.
   Поиск идёт на сервер: GET /api/workshops/<id>/participants/?q=…
   Подтверждение и отклонение заявок — PATCH /api/enrollment-status/<id>/. */
(function () {
  "use strict";

  var api = window.CampusApi;
  var ui = window.CampusUI;

  function start(workshopId) {
    var list = document.querySelector("[data-people-list]");
    var empty = document.querySelector("[data-people-empty]");
    var countNode = document.querySelector("[data-participant-count]");
    var search = document.querySelector("[data-participant-search]");

    function statusButton(enrollment, status, text, className) {
      var node = document.createElement("button");
      node.type = "button";
      node.className = className + " cursor-interaction";
      node.textContent = text;
      node.addEventListener("click", function () {
        node.disabled = true;
        api
          .patch("/api/enrollment-status/" + enrollment.id + "/", { status: status })
          .then(function () {
            ui.flash("Статус участника обновлён.");
            load(search.value);
          })
          .catch(function (error) {
            node.disabled = false;
            ui.flash(api.message(error.payload), true);
          });
      });
      return node;
    }

    function row(person) {
      var line = document.createElement("div");
      line.className = "sk-person-row";

      var nameCell = document.createElement("div");
      nameCell.className = "sk-person-name";
      var avatar = document.createElement("span");
      avatar.className = "sk-avatar";
      avatar.textContent = person.initials;
      var name = document.createElement("strong");
      name.textContent = person.name;
      nameCell.append(avatar, name);

      var group = document.createElement("span");
      group.className = "sk-person-group";
      group.textContent = person.group || "—";

      var actions = document.createElement("div");
      actions.className = "sk-person-actions";

      var tag = document.createElement("span");
      tag.className = "sk-state-tag sk-state-" + person.status;
      tag.textContent = person.status_label;
      actions.append(tag);

      if (person.status === "pending") {
        actions.append(statusButton(person, "confirmed", "Подтвердить", "sk-text-button"));
      }
      if (person.status === "waitlist") {
        actions.append(statusButton(person, "confirmed", "Взять в группу", "sk-text-button"));
      }

      line.append(nameCell, group, actions);
      return line;
    }

    function load(query) {
      ui.setLoading(list);

      api
        .get("/api/workshops/" + workshopId + "/participants/", { q: query || "" })
        .then(function (data) {
          var people = data.results;
          list.replaceChildren();
          people.forEach(function (person) {
            list.append(row(person));
          });
          empty.hidden = people.length > 0;
          countNode.textContent = ui.plural(
            people.length,
            "участник",
            "участника",
            "участников"
          );
          ui.icons(list, 17);
        })
        .catch(function (error) {
          ui.setError(list, error);
          empty.hidden = true;
        });
    }

    var timer = null;
    search.addEventListener("input", function () {
      window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        load(search.value);
      }, 250);
    });

    load("");
  }

  window.CampusParticipants = { start: start };
})();
