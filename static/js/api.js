/* Общий слой работы с REST API.
   Все страницы берут данные только отсюда — прямых обращений к fetch в
   страничных скриптах нет. */
(function () {
  "use strict";

  function csrfToken() {
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    if (match) return decodeURIComponent(match[1]);
    var input = document.querySelector("input[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  function buildUrl(path, params) {
    var url = new URL(path, window.location.origin);
    Object.keys(params || {}).forEach(function (key) {
      var value = params[key];
      if (value === undefined || value === null || value === "") return;
      url.searchParams.set(key, value);
    });
    return url.pathname + url.search;
  }

  /** Ошибка запроса с распарсенным телом ответа DRF. */
  function ApiError(status, payload) {
    this.name = "ApiError";
    this.status = status;
    this.payload = payload || {};
    this.message = firstMessage(this.payload) || "Не удалось выполнить запрос.";
  }
  ApiError.prototype = Object.create(Error.prototype);

  /** Достаёт человекочитаемый текст из ответа DRF с ошибками валидации. */
  function firstMessage(payload) {
    if (!payload) return "";
    if (typeof payload === "string") return payload;
    if (payload.detail) return payload.detail;
    var keys = Object.keys(payload);
    for (var i = 0; i < keys.length; i += 1) {
      var value = payload[keys[i]];
      if (Array.isArray(value) && value.length) return String(value[0]);
      if (typeof value === "string") return value;
    }
    return "";
  }

  function request(method, path, options) {
    options = options || {};
    var headers = { Accept: "application/json" };
    var init = { method: method, headers: headers, credentials: "same-origin" };

    if (method !== "GET" && method !== "HEAD") {
      headers["X-CSRFToken"] = csrfToken();
    }
    if (options.body !== undefined) {
      headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(options.body);
    }

    return fetch(buildUrl(path, options.params), init).then(function (response) {
      if (response.status === 204) return null;

      var isJson = (response.headers.get("Content-Type") || "").indexOf("json") !== -1;
      return (isJson ? response.json() : response.text()).then(function (payload) {
        if (!response.ok) throw new ApiError(response.status, payload);
        return payload;
      });
    });
  }

  var api = {
    get: function (path, params) {
      return request("GET", path, { params: params });
    },
    post: function (path, body) {
      return request("POST", path, { body: body || {} });
    },
    patch: function (path, body) {
      return request("PATCH", path, { body: body || {} });
    },
    put: function (path, body) {
      return request("PUT", path, { body: body || {} });
    },
    del: function (path, params) {
      return request("DELETE", path, { params: params });
    },
    ApiError: ApiError,
    message: firstMessage,
  };

  /* --- Общие помощники интерфейса --- */

  var ui = {
    /** Показывает плашку статуса в шапке (sk-flash из макета). */
    flash: function (text, isError) {
      var node = document.querySelector("[data-flash]");
      if (!node) return;
      if (!text) {
        node.hidden = true;
        return;
      }
      node.textContent = text;
      node.hidden = false;
      node.classList.toggle("sk-flash-error", Boolean(isError));
      node.scrollIntoView({ block: "nearest", behavior: "smooth" });
    },

    /** Озвучивает смену состояния для скринридеров. */
    announce: function (text) {
      var node = document.querySelector("[data-announcement]");
      if (node) node.textContent = text;
    },

    /** Клонирует <template> по id и возвращает фрагмент. */
    clone: function (id) {
      var template = document.getElementById(id);
      if (!template) throw new Error("Нет шаблона #" + id);
      return template.content.cloneNode(true);
    },

    /** Заполняет все узлы по селектору текстом. */
    fill: function (root, selector, value) {
      root.querySelectorAll(selector).forEach(function (node) {
        node.textContent = value === null || value === undefined ? "" : String(value);
      });
    },

    /** Проставляет href всем узлам по селектору. */
    link: function (root, selector, href) {
      root.querySelectorAll(selector).forEach(function (node) {
        node.setAttribute("href", href);
      });
    },

    /** Перерисовывает иконки внутри только что созданного DOM. */
    icons: function (root, size) {
      if (window.CampusIcons) window.CampusIcons.render(root || document, size);
    },

    /** Русская множественная форма: 1 воркшоп / 2 воркшопа / 5 воркшопов. */
    plural: function (count, one, few, many) {
      var hundred = count % 100;
      var ten = count % 10;
      var word = many;
      if (hundred < 11 || hundred > 14) {
        if (ten === 1) word = one;
        else if (ten >= 2 && ten <= 4) word = few;
      }
      return count + " " + word;
    },

    /** Состояние загрузки / пустого списка для контейнера. */
    setLoading: function (node, text) {
      node.replaceChildren();
      var div = document.createElement("div");
      div.className = "sk-loading";
      div.textContent = text || "Загружаем…";
      node.append(div);
    },

    /** Сообщение об ошибке запроса в контейнере списка. */
    setError: function (node, error) {
      node.replaceChildren();
      var div = document.createElement("div");
      div.className = "sk-empty";
      var title = document.createElement("h3");
      title.textContent = "Не удалось загрузить данные";
      var copy = document.createElement("p");
      copy.textContent = api.message(error && error.payload) || "Попробуй обновить страницу.";
      div.append(title, copy);
      node.append(div);
    },
  };

  window.CampusApi = api;
  window.CampusUI = ui;
})();
