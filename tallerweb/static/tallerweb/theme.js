(function () {
  var KEY = "ftm-theme";
  var root = document.documentElement;
  var button = document.getElementById("theme-toggle");
  var status = document.getElementById("theme-status");
  if (!button) return;

  function render() {
    var dark = root.getAttribute("data-theme") === "dark";
    button.querySelector(".theme-label").textContent = dark ? "Modo claro" : "Modo oscuro";
    button.querySelector(".theme-icon").textContent = dark ? "☀" : "☾";
  }

  button.addEventListener("click", function () {
    var next = root.getAttribute("data-theme") === "dark" ? "hybrid" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem(KEY, next); } catch (e) {}
    render();
    if (status) status.textContent = next === "dark" ? "Modo oscuro activado" : "Modo claro activado";
  });

  render();
})();
