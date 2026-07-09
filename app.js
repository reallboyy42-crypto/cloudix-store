<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Admin</title>
  <link rel="stylesheet" href="/static/styles.css">
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
  <main class="app">
    <section class="hero">
      <p class="pill">admin</p>
      <h1>Админка</h1>
      <p>Управление товарами, вкусами и заказами.</p>
    </section>

    <section class="panel">
      <div class="topbar">
        <h2>Товары</h2>
        <button id="refreshProducts" class="ghost">Обновить</button>
      </div>
      <div id="products"></div>
    </section>

    <section class="panel">
      <div class="topbar">
        <h2>Заказы</h2>
        <button id="refreshOrders" class="ghost">Обновить</button>
      </div>
      <div id="orders"></div>
    </section>
  </main>
  <script src="/static/admin.js"></script>
</body>
</html>
