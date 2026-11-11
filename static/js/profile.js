/* Профиль: сохранение данных и интересов через REST API,
   PATCH /api/profile/ и PUT /api/profile/interests/. */
(function () {
  "use strict";

  var api = window.CampusApi;
  var ui = window.CampusUI;

  var form = document.querySelector("[data-profile-form]");
  var error = document.querySelector("[data-profile-error]");
  var status = document.querySelector("[data-profile-status]");

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (!form.reportValidity()) return;

    var data = new FormData(form);
    var payload = {
      full_name: String(data.get("full_name")).trim(),
      study_group: String(data.get("study_group") || "").trim(),
      bio: String(data.get("bio") || "").trim(),
    };
    if (data.has("experience")) {
      payload.experience = String(data.get("experience")).trim();
    }

    var submit = form.querySelector("button[type=submit]");
    submit.disabled = true;
    error.hidden = true;
    status.textContent = "";

    api
      .patch("/api/profile/", payload)
      .then(function (profile) {
        submit.disabled = false;
        status.textContent = "Профиль сохранён.";
        // Обновляем шапку и заголовок без перезагрузки.
        ui.fill(document, "[data-profile-name]", profile.full_name);
        ui.fill(document, "[data-profile-initials]", profile.initials);
        var headerAvatar = document.querySelector(".sk-profile-button span");
        if (headerAvatar) headerAvatar.textContent = profile.initials;
      })
      .catch(function (err) {
        submit.disabled = false;
        error.textContent = api.message(err.payload);
        error.hidden = false;
      });
  });

  var saveInterests = document.querySelector("[data-save-interests]");
  var interestStatus = document.querySelector("[data-interest-status]");
  var interestList = document.querySelector("[data-interest-list]");

  saveInterests.addEventListener("click", function () {
    var selected = Array.from(interestList.querySelectorAll("input:checked")).map(
      function (input) {
        return input.value;
      }
    );

    saveInterests.disabled = true;
    interestStatus.textContent = "";

    api
      .put("/api/profile/interests/", { interests: selected })
      .then(function (data) {
        saveInterests.disabled = false;
        interestStatus.textContent = data.detail;
      })
      .catch(function (err) {
        saveInterests.disabled = false;
        interestStatus.textContent = api.message(err.payload);
      });
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
        .catch(function (err) {
          becomeMentor.disabled = false;
          ui.flash(api.message(err.payload), true);
        });
    });
  }
})();
