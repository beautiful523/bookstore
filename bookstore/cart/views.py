from django.shortcuts import render
from django.http import JsonResponse
# 引入书籍的模型类
from books.models import Books
# 引入登录验证装饰器
from utils.decorators import login_required
# redis
from django_redis import get_redis_connection


def cart_add(request):
	if not request.session.has_key('is_login'):
		# 如果没有登录返回数据：0,先登录
		return JsonResponse({'res':0, 'err_msg':'请先登录'})
	
	# 获取POST过来的book_id,book_count
	book_id = request.POST.get('book_id')
	book_count = request.POST.get('book_count')
	if not all([book_id, book_count]):
		# 如果这两个数不完整返回数据：1,不完整
		return JsonResponse({'res':1, 'err_msg': "数据不完整"})
	
	# 根据book_id从数据库查询到这本书的信息
	book = Books.objects.get_books_by_id(book_id)
	
	if book is None:
		# 如果不存在返回数据：2,不存在
		return JsonResponse({'res':2, 'err_msg':"商品不存在"})
	
	# 每个用户的购物车记录用一条hash数据保存，格式:cart_用户id: 商品id 商品数量
	connection = get_redis_connection('default')
	cart_key = 'cart_%d'% request.session.get('passport_id')
	
	# 获取该用户购物车中这本书的数量
	get_num = connection.hget(cart_key, book_id)
	
	# 将购物车中这本书的数加上POST过来的添加书本数
	if get_num is None:
		set_num = 0 + int(book_count)
	else:
		set_num = int(get_num) + int(book_count)
	
	# 将redis中购物车里的书本数更新
	connection.hset(cart_key, book_id, set_num)
	
	# 返回数据：5，成功添加
	return JsonResponse({'res': 5})

def cart_count(request):
	if not request.session.get('is_login'):
		# 如果没有登录返回数据：0
		return JsonResponse({'res': 0})
	
	# 准备redis连接与键
	connection = get_redis_connection('default')
	cart_key = 'cart_%d' % request.session.get('passport_id')
	
	# 从redis查询到该用户各种书籍数量的列表
	num_list = connection.hvals(cart_key)
	
	# 各种书加起来的总数
	total_num = 0
	for i in num_list:
		total_num += int(i)
		
	# 返回数据：总数
	return JsonResponse({'res': total_num})

@login_required
def cart_show(request):
	# 视图提供每一种书的每一栏信息需要的数据，
	# 选中结算和总数在前端javascript直接实现
	'''显示用户购物车页面'''
	
	passport_id = request.session.get('passport_id')
	
	# 获取redis中用户购物车的记录：book_id,book_count
	# default是默认的redis连接的名字，在settings.py中写了CACHES:default:"redis://127.0.0.1:6379/2",
	connection = get_redis_connection('default')
	cart_key = 'cart_%d' % passport_id
	res_dict = connection.hgetall(cart_key)
	
	# 购物车的所有书籍种类
	books_li = []
	
	# 遍历res_dict获取商品的数据
	for id, count in res_dict.items():
		
		# 根据id查询mysql中书的信息
		book = Books.objects.get_books_by_id(id)
		
		# 保存单种商品的数目
		book.count = count
		
		# 保存单种商品的价格小计
		book.amount = int(count) * book.price
		
		# 书籍列表增加这种书
		books_li.append(book)
		
	return render(request, 'cart/cart_show.html', locals())


def cart_del(request):
	if not request.session.has_key('is_login'):
		return JsonResponse({'res':0, 'err_msg':'请先登陆'})
	
	book_id = request.POST.get('book_id')
	
	connection = get_redis_connection('default')
	cart_key = 'cart_%d' % request.session.get('passport_id')
	connection.hdel(cart_key, book_id)
	
	return JsonResponse({'res': 1})
	

def cart_update(request):
	# 这个接口用来：当前端改变商品数量时更新redis
	# 判断用户是否登录
	if not request.session.has_key('is_login'):
		return JsonResponse({'res': 0, 'err_msg':'请先登录'})
	# 接收数据
	book_id = request.POST.get('book_id')
	print('book_id:',book_id)
	book_count = request.POST.get('book_count')
	print('book_count:',book_count)
	# 数据的校验
	if not all([book_id, book_count]):
		return JsonResponse({'res': 1, 'err_msg': '数据不完整'})
	book = Books.objects.get_books_by_id(book_id)
	if book is None:
		return JsonResponse({'res': 2, 'err_msg': '商品不存在'})
	try:
		book_count = int(book_count)
	except Exception as e:
		return JsonResponse({'res': 3, 'err_msg': '商品数目必须为数字'})
	# 更新redis操作
	connection = get_redis_connection('default')
	cart_key = 'cart_%d' % request.session.get('passport_id')
	connection.hset(cart_key, book_id, book_count)

	return JsonResponse({'res': 5})
	
	

	
	
		
