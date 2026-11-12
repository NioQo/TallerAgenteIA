from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from tallerweb.views import budget_pdf_download, complete_work, dashboard, decide_budget, monthly_summary, vehicle_detail

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", dashboard, name="dashboard"),
    path("resumen-mensual/", monthly_summary, name="monthly_summary"),
    path("vehiculos/<int:pk>/", vehicle_detail, name="vehicle_detail"),
    path("presupuestos/<int:pk>/decision/", decide_budget, name="decide_budget"),
    path("presupuestos/<int:pk>/cerrar-trabajo/", complete_work, name="complete_work"),
    path("presupuestos/<int:pk>/pdf/", budget_pdf_download, name="budget_pdf_download"),
]
