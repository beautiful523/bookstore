from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.core.urlresolvers import reverse
import re

from order.models import OrderInfo, OrderGoods
from users.models import *
from utils.decorators import login_required


# 用户注册页面
def register(request):
	return render(request, 'users/register.html')


# 注册表单提交
def register_handle(request):
	# 接收数据
	user_name = request.POST.get("user_name")
	password = request.POST.get("password")
	email = request.POST.get("email")
	# 数据校验
	# 不能为空
	if not all([user_name, password, email]):
		return render(request,"users/register.html",{"erro_msg": "参数不能为空"})
	# 邮箱格式
	if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
		return render(request, 'users/register.html', {'erro_msg': '邮箱不合法!'})
	# 像数据库添加一个账户
	passport = Passport.object.add_one_passport(user_name, password,email)
	# 注册完，还是返回注册页
	return redirect(reverse('first:index'))


def login(request):
	return render(request, 'users/login.html')
	
# 登陆数据提交之后的处理
def login_check(request):
	user_name = request.POST.get("user_name")
	password = request.POST.get("password")
	remember = request.POST.get("remember")
	# 有数据为空就结束并返回res=2
	if not all([user_name, password]):
		print(user_name, password)
		return JsonResponse({"res":2})
	
	# 数据完整则查询此用户
	passport = Passport.object.get_one_passport(user_name, password)
	print(passport.user_name)
	
	# 如果查询到了,准备res数据
	if passport:
		# session还没设置
		# 当没有session.url_path的时候就传首页的路由
		next_url = request.session.get("url_path", reverse('first:index'))
		# JsonResponse就是返回到请求端的data
		# 初步的JsonResponse
		jres = JsonResponse({'res':1, 'next_url':next_url})
		# 记住用户名就在浏览器存一个cookie：user_name
		if remember == 'true':
			jres.set_cookie('user_name', user_name, max_age=7*24*3600)
		else:
			# 忘记就把客户端的cookie删除
			jres.delete_cookie('user_name')
		# 记录一些session值
		request.session['is_login'] = True
		request.session['user_name'] = user_name
		request.session['passport_id'] = passport.id
		# 经历了一些处理的JsonResponse
		return jres
	
	else:
		# 如果查询不到,说明用户名或者密码错误
		return JsonResponse({'res': 0})


def logout(request):
	'''用户退出登录'''
	# 清空用户的session信息
	request.session.flush()
	# 跳转到首页
	return redirect(reverse('books:index'))

@login_required
def user_center_info(request):
	passport_id = request.session.get('passport_id')
	passport = Passport.object.get(id=passport_id)
	return render(request, 'users/user_center_info.html', locals())

@login_required
def user_center_site(request):
	'''用户中心-地址页'''
	# 获取登录用户的id
	passport_id = request.session.get('passport_id')

	if request.method == 'GET':
		# 显示地址页面,传过去用户的默认地址
		recipient = Recipient.objects.get_default_recipient(passport_id=passport_id)
		return render(request, 'users/user_center_site.html', locals())
	
	else:
		# 添加收货地址
		# 1.接收数据
		recipient_name = request.POST.get('recipient_name')
		recipient_address = request.POST.get('recipient_address')
		postal_code = request.POST.get('postal_code')
		recipient_phone = request.POST.get('recipient_phone')

		# 2.进行校验
		if not all([recipient_name, recipient_address, postal_code, recipient_phone]):
			return render(request, 'users/user_center_site.html', {'err_msg': '参数不必为空!'})

		# 3.添加收货地址
		Recipient.objects.add_one_recipient(passport_id=passport_id,
										recipient_name=recipient_name,
										  recipient_address=recipient_address,
										  postal_code=postal_code,
										recipient_phone=recipient_phone)

		# 4.返回应答
		return redirect(reverse('users:user_center_site'))

@login_required
def user_center_order(request):
	'''用户中心-订单页'''
	# 查询用户的订单信息
	passport_id = request.session.get('passport_id')

	# 获取订单信息
	order_li = OrderInfo.objects.filter(passport_id=passport_id)

	# 遍历获取订单的商品信息
	# order->OrderInfo实例对象
	for order in order_li:
		# 根据订单id查询订单商品信息
		order_id = order.order_id
		order_books_li = OrderGoods.objects.filter(order_id=order_id)

		# 计算商品的小计
		# order_books ->OrderBooks实例对象
		for order_books in order_books_li:
			count = order_books.count
			price = order_books.price
			amount = count * price
			# 保存订单中每一个商品的小计
			order_books.amount = amount

		# 给order对象动态增加一个属性order_goods_li,保存订单中商品的信息
		order.order_books_li = order_books_li


	return render(request, 'users/user_center_order.html', locals())
		
		
		
	
	
		
	
	