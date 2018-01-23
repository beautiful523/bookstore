from db import BaseModels
# 引入富文本编辑器的功能
from tinymce.models import HTMLField
from books.enums import *
from django.db import models

class BooksManager(models.Manager):
    '''商品模型管理器类'''
    # sort='new' 按照创建时间进行排序
    # sort='hot' 按照商品销量进行排序
    # sort='price' 按照商品的价格进行排序
    # sort= 按照默认顺序排序
    
    # 得到一个列表
    def get_books_by_type(self, type_id, limit=None, sort='default'):
        '''根据商品类型id查询商品信息'''
        if sort == 'new':
            order_by = ('-create_time',)
        elif sort == 'hot':
            order_by = ('-sales', )
        elif sort == 'price':
            order_by = ('price', )
        else:
            order_by = ('-pk', ) # 按照primary key降序排列。

        # 查询数据
        # filter会得到一个QuerySet对象,QuerySet有一个很重要的特性就是延迟加载，并不是每一次调用filter()方法就会去查询一次数据库，只有在真正需要数据的时候才会去查询数据库
        # 下面这个语句并没有去查数据库，用到book_li的时候比如print的时候才会去查数据库，这种机制避免了不必要的数据库查询，减轻了数据库的压力。
        books_li = self.filter(type_id=type_id).order_by(*order_by)
        # print(type(books_li))  # <class 'django.db.models.query.QuerySet'>
        # print(books_li)
        # <QuerySet [<Books: Books object>, <Books: Books object>, <Books: Books object>, <Books: Books object>]>

        # 查询结果集的限制
        if limit:
            books_li = books_li[:limit]
        return books_li

    def get_books_by_id(self, books_id):
        '''根据商品的id获取商品信息'''
        try:
            books = self.get(id=books_id)
        except self.model.DoesNotExist:
            # 不存在商品信息
            books = None
        return books


class Books(BaseModels.BaseModel):
    # 商品模型类(下面两句是与保存常量的文件有关的)
    books_type_choices = ((k, v) for k,v in BOOKS_TYPE.items()) # 返回的是一个迭代器对象，((1, 'Python'),(2,'javascript')...)
    status_choices = ((k, v) for k,v in STATUS_CHOICE.items())  # (0, '上线')
    # .SmallIntegerField 小整数字段，choices是那个迭代器
    type_id = models.SmallIntegerField(default=PYTHON, choices=books_type_choices, verbose_name='商品种类')
    name = models.CharField(max_length=20, verbose_name='商品名称',)
    desc = models.CharField(max_length=128, verbose_name='商品简介')
    # DecimalField 小数字段，decimal_places=2 两位小数
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品价格')
    unite = models.CharField(max_length=20, verbose_name='商品单位')  # 册
    stock = models.IntegerField(default=1, verbose_name='商品库存')
    sales = models.IntegerField(default=0, verbose_name='商品销量')
    # 富文本编辑
    detail = HTMLField(verbose_name='商品详情')
    # upload_to='books' 把图片保存到books目录下
    image = models.ImageField(upload_to='books', verbose_name='商品图片')
    status = models.SmallIntegerField(default=ONLINE, choices=status_choices, verbose_name='商品状态')

    objects = BooksManager()

    class Meta:
        db_table = 's_books'