from alipay import AliPay
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from utils.decorators import login_required
from django.http import HttpResponse, JsonResponse
from users.models import Recipient
from books.models import Books
from order.models import OrderInfo, OrderGoods
from django_redis import get_redis_connection
from datetime import datetime
from django.conf import settings
from django.db import transaction
import os
import time
# Create your views here.


@login_required
# 当接到POST请求(参数是书籍id列表)后，提供页面渲染需要的数据，并渲染提交订单页面
def order_place(request):
    '''显示提交订单页面'''
    # 接收数据:书籍id的列表
    # 获取name为'book_id'的表单项的value值，有多个ul所以获取列表
    # 如果表单没有checked的话，input不会提交，就获取不到book_id,该书不在要购买的列表内
    books_id = request.POST.getlist('book_id')

    # 校验数据完整
    if not all(books_id):
        # 跳转会购物车页面
        return redirect(reverse('cart:cart_show'))
    
    if books_id==[]:
        return redirect(reverse('cart:cart_show'))

    # 获取用户默认收货地址
    passport_id = request.session.get('passport_id')
    recipient = Recipient.objects.get_default_recipient(passport_id=passport_id)

    # 用户要购买商品的信息
    books_li = []

    # 商品的总数目和总金额
    total_count = 0
    total_price = 0

    connection = get_redis_connection('default')
    cart_key = 'cart_%d' % passport_id

    for id in books_id:
        # 根据id获取选中商品的信息
        book = Books.objects.get_books_by_id(id)
        # 从redis中获取用户要购买的商品的数目
        count = connection.hget(cart_key, id)
        book.count = count
        # 计算商品的小计
        amount = int(count) * book.price
        book.amount = amount
        books_li.append(book)

        # 累计计算商品的总数目和总金额
        total_count += int(count)
        total_price += book.amount

    # 商品运费和实付款
    transit_price = 10
    total_pay = total_price + transit_price

    # 1,2,3(前端需要books_id作为属性值，所以不能是列表，只能是字符串)
    books_id = ','.join(books_id)


    # 使用模板
    return render(request, 'order/place_order.html', locals())

@transaction.atomic
def order_commit(request):
    '''生成订单'''
    # 验证用户是否登录
    if not request.session.has_key('is_login'):
        return JsonResponse({'res': 0, 'err_msg': '用户未登录'})

    # 接收数据
    recipient_id = request.POST.get('recipient_id')
    pay_method = request.POST.get('pay_method')
    books_id = request.POST.get('books_id')
    print(recipient_id ,"111",pay_method, "111",books_id)
    
    if not recipient_id:
        return JsonResponse({'res': 1, 'err_msg': '请填写收货地址'})

    # 进行数据校验
    if not all([pay_method, books_id]):
        return JsonResponse({'res': 1, 'err_msg': '数据不完整'})
        

    try:
        recipient = Recipient.objects.get(id=recipient_id)
    except Exception as e:
        # 地址信息出错
        return JsonResponse({'res': 2, 'err_msg': '地址信息错误'})
    

    if int(pay_method) not in OrderInfo.PAY_METHODS_ENUM.values():
        return JsonResponse({'res': 3, 'err_msg': '不支持的支付方式'})

    # 订单创建
    # 组织订单信息
    passport_id = request.session.get('passport_id')
    # 订单id: 20171029110830+用户的id
    order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(passport_id)
    # 运费
    transit_price = 10
    # 订单商品总数和总金额
    total_count = 0
    total_price = 0

    # 创建一个保存点
    sid = transaction.savepoint()
    try:
        # 向订单信息表中添加一条记录
        order = OrderInfo.objects.create(order_id=order_id,
                                 passport_id=passport_id,
                                 recipient_id=recipient_id,
                                 total_count=total_count,
                                 total_price=total_price,
                                 transit_price=transit_price,
                                 pay_method=pay_method)

        # 向订单商品表中添加订单商品的记录
        books_id = books_id.split(',')
        connection = get_redis_connection('default')
        cart_key = 'cart_%d' % passport_id

        # 遍历获取用户购买的商品信息
        for id in books_id:
            book = Books.objects.get_books_by_id(id)
            if book is None:
                transaction.savepoint_rollback(sid)
                return JsonResponse({'res': 4, 'err_msg': '商品信息错误'})

            # 获取用户购买的商品数目
            count = connection.hget(cart_key, id)

            # # 判断商品的库存
            # if int(count) > book.stock:
            #     transaction.savepoint_rollback(sid)
            #     return JsonResponse({'res': 5, 'err_msg': '商品库存不足'})

            # 创建一条订单商品记录
            OrderGoods.objects.create(order_id=order_id,
                                      book_id=id,
                                      count=count,
                                      price=book.price)

            # 增加商品的销量，减少商品库存
            book.sales += int(count)
            book.stock -= int(count)
            # 当使用了事务的时候，save()只是将值存到内存，事务结束时再存到硬盘（数据库）中去。
            # 没有使用事务时，save()直接存到数据库。
            book.save()

            # 累计计算商品的总数目和总额
            total_count += int(count)
            total_price += int(count) * book.price

        # 更新订单的商品总数目和总金额
        order.total_count = total_count
        order.total_price = total_price
        order.save()
    except Exception as e:
        # 操作数据库出错，进行回滚操作
        transaction.savepoint_rollback(sid)
        return JsonResponse({'res': 7, 'err_msg': '服务器错误'})

    # 清除购物车对应记录
    connection.hdel(cart_key, *books_id)

    # 事务提交
    transaction.savepoint_commit(sid)
    
    # 返回应答
    return JsonResponse({'res': 6})

def order_pay(request):
    '''订单支付'''
    # 用户登录判断
    if not request.session.has_key('is_login'):
        return JsonResponse({'res': 0, 'err_msg': '用户未登录'})

    # 接收订单id
    order_id = request.POST.get('order_id')

    # 数据校验
    if not order_id:
        return JsonResponse({'res': 1, 'err_msg': '订单不存在'})

    try:
        order = OrderInfo.objects.get(order_id=order_id,
                                      status=1,
                                      pay_method=3)
    except OrderInfo.DoesNotExist:
        return JsonResponse({'res': 2, 'err_msg': '订单信息出错'})

    # 和支付宝进行交互
    alipay = AliPay(
        appid="2016090800464054", # 应用id
        app_notify_url=None,  # 默认回调url
        app_private_key_path=os.path.join(settings.BASE_DIR, 'order/app_private_key.pem'),
        alipay_public_key_path=os.path.join(settings.BASE_DIR, 'order/alipay_public_key.pem'),  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type = "RSA2",  # RSA 或者 RSA2
        debug = True,  # 默认False
    )

    # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
    total_pay = order.total_price + order.transit_price # decimal
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order_id, # 订单id
        total_amount=str(total_pay),
        subject='尚硅谷书城%s' % order_id,
        return_url=None,
        notify_url=None  # 可选, 不填则使用默认notify url
    )
    # 返回应答
    pay_url = settings.ALIPAY_URL + '?' + order_string
    return JsonResponse({'res': 3, 'pay_url': pay_url, 'message': 'OK'})

def check_pay(request):
    '''获取用户支付的结果'''
    # 用户登录判断
    if not request.session.has_key('is_login'):
        return JsonResponse({'res': 0, 'err_msg': '用户未登录'})

    passport_id = request.session.get('passport_id')
    # 接收订单id
    order_id = request.POST.get('order_id')

    # 数据校验
    if not order_id:
        return JsonResponse({'res': 1, 'err_msg': '订单不存在'})

    try:
        order = OrderInfo.objects.get(order_id=order_id,
                                      passport_id=passport_id,
                                      pay_method=3)
    except OrderInfo.DoesNotExist:
        return JsonResponse({'res': 2, 'err_msg': '订单信息出错'})

    # 和支付宝进行交互
    alipay = AliPay(
        appid="2016090800464054",  # 应用id
        app_notify_url=None,  # 默认回调url
        app_private_key_path=os.path.join(settings.BASE_DIR, 'df_order/app_private_key.pem'),
        alipay_public_key_path=os.path.join(settings.BASE_DIR, 'df_order/alipay_public_key.pem'),
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True,  # 默认False
    )

    while True:
        # 进行支付结果查询
        result = alipay.api_alipay_trade_query(order_id)
        code = result.get('code')
        if code == '10000' and result.get('trade_status') == 'TRADE_SUCCESS':
            # 用户支付成功
            # 改变订单支付状态
            order.status = 2 # 待发货
            # 填写支付宝交易号
            order.trade_id = result.get('trade_no')
            order.save()
            # 返回数据
            return JsonResponse({'res':3, 'message':'支付成功'})
        elif code == '40004' or (code == '10000' and result.get('trade_status') == 'WAIT_BUYER_PAY'):
            # 支付订单还未生成，继续查询
            # 用户还未完成支付，继续查询
            time.sleep(5)
            continue
        else:
            # 支付出错
            return JsonResponse({'res':4, 'err_msg':'支付出错'})