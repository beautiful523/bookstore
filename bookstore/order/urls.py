from django.conf.urls import url
from order import views

urlpatterns = [
    url(r'^order_place/$', views.order_place, name='order_place'), # 订单提交页面
    url(r'^order_commit/$', views.order_commit, name='order_commit'), # 生成订单
    url(r'^order_pay/$', views.order_pay, name='order_pay'),
    url(r'^check_pay/$', views.check_pay, name='check_pay'),

]