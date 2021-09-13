from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.InstitutionDetail.as_view(), name='institution_detail'),
    # url(r'^logo$', views.LogoUpload.as_view(), name='logo_upload'),
    # url(r'^banner$', views.BannerUpload.as_view(), name='banner_upload'),
]
